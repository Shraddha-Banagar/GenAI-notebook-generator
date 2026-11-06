"""FastAPI entrypoint for the GenAI Notebook Generator."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .catalog import DATASETS, MODELS, public_catalog
from .config import SAMPLES_DIR, settings
from .llm_service import LLMError, generate_overrides
from .notebook_builder import (
    NotebookBuildError,
    build_notebook,
    notebook_filename,
    notebook_to_dict,
    write_notebook,
)
from .templates import TemplateError, build_spec
from .validation import validate_code, validate_notebook

app = FastAPI(
    title="GenAI Notebook Generator API",
    description="Generates runnable TF2/Keras Colab notebooks for generative models.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    model: str = Field(..., description="dcgan | vae | char_rnn")
    dataset: str = Field(..., description="Dataset id from /api/catalog")
    epochs: int = Field(5, ge=1, le=100)
    batch_size: int = Field(64, ge=1, le=512)
    use_llm: bool = True


class ValidateRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=200_000)
    section: str = "manual"


SAMPLES: dict[str, dict[str, Any]] = {
    "dcgan_fashion_mnist": {
        "id": "dcgan_fashion_mnist",
        "filename": "dcgan_fashion_mnist.ipynb",
        "title": "DCGAN · Fashion-MNIST",
        "description": "Convolutional GAN with custom train step, latent sampling and BLIP captioning.",
        "model": "dcgan",
        "dataset": "fashion_mnist",
        "license": "MIT",
    },
    "char_rnn_tiny_shakespeare": {
        "id": "char_rnn_tiny_shakespeare",
        "filename": "char_rnn_tiny_shakespeare.ipynb",
        "title": "char-RNN · Tiny Shakespeare",
        "description": "Stateful GRU language model with temperature sampling and perplexity evaluation.",
        "model": "char_rnn",
        "dataset": "tiny_shakespeare",
        "license": "Public Domain",
    },
}


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "GenAI Notebook Generator",
        "docs": "/docs",
        "catalog": "/api/catalog",
    }


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "llm": settings.describe(),
        "models": list(MODELS.keys()),
        "datasets": list(DATASETS.keys()),
    }


@app.get("/api/catalog")
def catalog() -> dict[str, Any]:
    return public_catalog()


@app.get("/api/samples")
def list_samples() -> dict[str, Any]:
    items = []
    for sample in SAMPLES.values():
        path = SAMPLES_DIR / sample["filename"]
        items.append(
            {
                **sample,
                "available": path.exists(),
                "download_url": f"/api/samples/{sample['id']}",
            }
        )
    return {"samples": items}


@app.get("/api/samples/{sample_id}")
def download_sample(sample_id: str) -> FileResponse:
    sample = SAMPLES.get(sample_id)
    if sample is None:
        raise HTTPException(status_code=404, detail="Unknown sample notebook.")
    path = SAMPLES_DIR / sample["filename"]
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Sample notebook has not been generated yet. Run scripts/generate_samples.py.",
        )
    return FileResponse(
        path,
        media_type="application/x-ipynb+json",
        filename=sample["filename"],
    )


@app.post("/api/validate")
def validate_snippet(request: ValidateRequest) -> dict[str, Any]:
    findings = validate_code(request.code, section=request.section)
    return {
        "passed": not any(f.severity == "error" for f in findings),
        "errors": [f.to_dict() for f in findings if f.severity == "error"],
        "warnings": [f.to_dict() for f in findings if f.severity == "warning"],
    }


@app.post("/api/generate")
def generate(request: GenerateRequest) -> dict[str, Any]:
    started = time.perf_counter()

    if request.model not in MODELS:
        raise HTTPException(status_code=422, detail=f"Unknown model '{request.model}'.")
    if request.dataset not in DATASETS:
        raise HTTPException(status_code=422, detail=f"Unknown dataset '{request.dataset}'.")

    try:
        spec = build_spec(
            request.model,
            request.dataset,
            batch_size=request.batch_size,
            epochs=request.epochs,
        )
    except TemplateError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    generation: dict[str, Any] = {
        "source": "template",
        "provider": None,
        "llm_model": None,
        "llm_attempted": False,
        "fallback_reason": None,
        "notes": None,
    }
    overrides: dict[str, str] = {}

    if request.use_llm:
        generation["llm_attempted"] = True
        if not settings.llm_enabled:
            generation["fallback_reason"] = (
                "No LLM provider configured; deterministic templates were used."
            )
        else:
            try:
                result = generate_overrides(request.model, request.dataset, spec)
                overrides = result.overrides
                generation.update(
                    {
                        "source": "llm",
                        "provider": result.provider,
                        "llm_model": result.model,
                        "notes": result.notes or None,
                    }
                )
            except LLMError as exc:
                generation["fallback_reason"] = str(exc)
            except Exception as exc:  # pragma: no cover - defensive
                generation["fallback_reason"] = f"Unexpected LLM failure: {exc}"

    try:
        notebook = build_notebook(
            spec,
            llm_overrides=overrides,
            generation_meta=generation,
        )
    except NotebookBuildError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    payload = notebook_to_dict(notebook)
    report = validate_notebook(payload)

    # If an LLM section caused a notebook-level failure, rebuild safely.
    if not report["passed"] and overrides:
        generation["fallback_reason"] = (
            "LLM output passed pre-checks but failed full-notebook validation; "
            "the deterministic template was used instead."
        )
        generation["source"] = "template"
        notebook = build_notebook(spec, generation_meta=generation)
        payload = notebook_to_dict(notebook)
        report = validate_notebook(payload)
        overrides = {}

    if not report["passed"]:
        errors = report["errors"][:5]
        raise HTTPException(
            status_code=500,
            detail={"message": "Generated notebook failed validation.", "errors": errors},
        )

    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "notebook": payload,
        "filename": notebook_filename(request.model, request.dataset),
        "validation": report,
        "generation": {**generation, "duration_ms": elapsed_ms},
        "meta": {
            "model": request.model,
            "model_label": MODELS[request.model]["label"],
            "dataset": request.dataset,
            "dataset_label": DATASETS[request.dataset]["label"],
            "dataset_source": DATASETS[request.dataset]["source"],
            "dataset_source_url": DATASETS[request.dataset]["source_url"],
            "license": DATASETS[request.dataset]["license"],
            "settings": spec["settings"],
        },
    }


@app.post("/api/generate/file")
def generate_file(request: GenerateRequest) -> FileResponse:
    """Same as /api/generate but streams a ready-to-open .ipynb file."""

    result = generate(request)
    notebook = result["notebook"]
    import nbformat

    node = nbformat.from_dict(notebook)
    filename = result["filename"]
    temp_path = Path(SAMPLES_DIR) / "generated" / filename
    write_notebook(node, temp_path)
    return FileResponse(
        temp_path,
        media_type="application/x-ipynb+json",
        filename=filename,
    )
