"""LLM-assisted code generation for the notebook templates (U2).

The LLM only fills the architecture / training / inference sections. Setup,
data loading, the BLIP cell and the license cell remain under the generator's
control. Every LLM section is statically validated (U4/U5) before it can be
injected; on any failure the caller falls back to the deterministic template.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from .catalog import DATASETS, MODELS
from .config import settings
from .validation import validate_code_sources

SECTION_KEYS = ("architecture", "training", "inference")

SYSTEM_PROMPT = """\
You are a senior TensorFlow 2 / Keras engineer who writes reliable Google Colab
notebooks. You return ONLY valid JSON. Never use TF1 APIs, standalone Keras
imports, shell commands, network calls, eval/exec, subprocess, or filesystem
deletion. Code must run on current Colab (TensorFlow 2.x, Keras 3, Python 3.10+)
on a T4 GPU. Keep runtime under 10 minutes for the requested epoch count.
"""

REQUIRED_TOKENS: dict[str, dict[str, list[str]]] = {
    "dcgan": {
        "architecture": ["generator = ", "discriminator = "],
        "training": ["train_step", "generator_optimizer", "discriminator_optimizer"],
        "inference": ["IMAGE_FOR_CAPTION_PATH", "Image.fromarray"],
    },
    "vae": {
        "architecture": ["class VAE", "vae = VAE"],
        "training": ["vae.compile", "vae.fit"],
        "inference": ["IMAGE_FOR_CAPTION_PATH", "vae"],
    },
    "char_rnn": {
        "architecture": ["model = build_model"],
        "training": ["model.fit"],
        "inference": ["generate_text", "generated_text"],
    },
}

MODEL_CONTRACTS: dict[str, str] = {
    "dcgan": """\
- Data cell already defines: train_ds, BATCH_SIZE, EPOCHS, IMAGE_SIZE, CHANNELS,
  LATENT_DIM, AUTOTUNE, np, tf, plt, show_images(), to_display().
- `architecture_code` MUST define `generator` and `discriminator` Keras models
  (build functions are fine as long as the variables exist).
- `training_code` MUST define `@tf.function train_step(images)` and the
  generator/discriminator optimizers, then run an epoch loop and plot losses.
- `inference_code` MUST generate a sample grid with show_images(), then write one
  sample to IMAGE_FOR_CAPTION_PATH using PIL Image and numpy.
- Images are in [-1, 1], grayscale (1 channel) or RGB (3 channels).""",
    "vae": """\
- Data cell already defines: train_ds, BATCH_SIZE, EPOCHS, IMAGE_SIZE, CHANNELS,
  LATENT_DIM, AUTOTUNE, np, tf, plt, show_images(), to_display().
- `architecture_code` MUST define a `vae` object exposing `.encoder`, `.decoder`,
  and `.generate(n, seed=None)`. Include the reparameterisation trick and KL loss.
- `training_code` MUST compile and fit `vae` with a reconstruction loss and plot
  the loss history.
- `inference_code` MUST compare reconstructions to originals, draw prior samples,
  and write one sample to IMAGE_FOR_CAPTION_PATH using PIL Image.
- Images are in [-1, 1], grayscale (1 channel) or RGB (3 channels).""",
    "char_rnn": """\
- Data cell already defines: dataset (batched tf.data), vocab, vocab_size,
  char2idx, idx2char, BATCH_SIZE, EPOCHS, SEQ_LENGTH, EMBEDDING_DIM, RNN_UNITS,
  AUTOTUNE, np, tf, plt.
- `architecture_code` MUST define `model` built by a function named
  `build_model(vocab_size, embedding_dim, rnn_units, batch_size)` using a
  stateful GRU and a Dense(vocab_size) output.
- `training_code` MUST compile with SparseCategoricalCrossentropy(from_logits=True),
  reset GRU states between epochs via a callback, fit `model`, and plot the loss.
- `inference_code` MUST define `generate_text(model, start_string, ...)`, build a
  batch-size-1 inference model, set its weights, assign the first sample to
  `generated_text`, and print it. No torch/transformers imports.
- Keras 3 Functional models have no model.reset_states(); reset the stateful GRU
  layer(s) explicitly (loop over model.layers and call reset_states()).""",
}


class LLMError(RuntimeError):
    pass


class LLMUnavailable(LLMError):
    pass


@dataclass
class LLMResult:
    overrides: dict[str, str]
    provider: str
    model: str
    notes: str = ""
    warnings: list[str] = field(default_factory=list)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = _strip_fences(text)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise LLMError("The LLM response did not contain a JSON object.")
        try:
            value = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMError(f"Could not parse the LLM JSON response: {exc}") from exc
    if not isinstance(value, dict):
        raise LLMError("The LLM response must be a JSON object.")
    return value


def _build_user_prompt(model_key: str, dataset_key: str, spec: dict[str, Any]) -> str:
    model = MODELS[model_key]
    dataset = DATASETS[dataset_key]
    baseline = {
        section["key"]: "\n".join(section["code"])
        for section in spec["sections"]
        if section["key"] in SECTION_KEYS
    }
    contract = MODEL_CONTRACTS[model_key]
    return f"""\
Generate the three implementation sections for a runnable Colab notebook.

MODEL: {model["label"]} ({model["description"]})
DATASET: {dataset["label"]} — {dataset["description"]}
SETTINGS: epochs={spec["settings"]["epochs"]}, batch_size={spec["settings"]["batch_size"]}, seed=42

INTERFACE CONTRACT (must be preserved exactly):
{contract}

RULES:
1. Return strict JSON with exactly these string keys:
   "architecture_code", "training_code", "inference_code", "notes".
2. Each *_code value is a COMPLETE Python cell (possibly multiple blocks), no
   Markdown fences, no setup/data-loading/install code.
3. Use only tf.keras / tensorflow.keras. No TF1 APIs, no standalone `import keras`,
   no subprocess/socket/pickle/eval/exec, no shell magics, no network downloads.
4. Inference code must leave the notebook in a state where the BLIP cell can read
   IMAGE_FOR_CAPTION_PATH (image models).
5. Be deterministic where practical (seeds) and keep memory within a T4 GPU.
6. "notes" is a short one-paragraph explanation of the design choices.

DETERMINISTIC BASELINE (improve it, but keep the contract):
--- architecture baseline ---
{baseline.get("architecture", "")}
--- training baseline ---
{baseline.get("training", "")}
--- inference baseline ---
{baseline.get("inference", "")}
"""


def _call_provider(prompt: str) -> tuple[str, str]:
    if not settings.llm_enabled:
        raise LLMUnavailable(
            "No LLM API key configured. Set LLM_API_KEY (or GROQ_API_KEY / "
            "OPENAI_API_KEY), or set LLM_PROVIDER=none to use templates only."
        )

    payload: dict[str, Any] = {
        "model": settings.resolved_model,
        "temperature": 0.2,
        "max_tokens": 5000,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }
    url = f"{settings.resolved_base_url}/chat/completions"

    try:
        response = httpx.post(
            url,
            headers=headers,
            json={**payload, "response_format": {"type": "json_object"}},
            timeout=settings.timeout_seconds,
        )
        if response.status_code in {400, 422}:
            response = httpx.post(
                url,
                headers=headers,
                json=payload,
                timeout=settings.timeout_seconds,
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500]
        raise LLMError(
            f"LLM provider returned HTTP {exc.response.status_code}: {detail}"
        ) from exc
    except httpx.HTTPError as exc:
        raise LLMError(f"Could not reach the LLM provider: {exc}") from exc

    body = response.json()
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("LLM response is missing choices[0].message.content.") from exc
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") for part in content if isinstance(part, dict)
        )
    return str(content), settings.resolved_model


def _check_required_tokens(model_key: str, overrides: dict[str, str]) -> list[str]:
    issues: list[str] = []
    for section, tokens in REQUIRED_TOKENS[model_key].items():
        source = overrides.get(section, "")
        for token in tokens:
            if token not in source:
                issues.append(f"{section} is missing required token {token!r}")
    return issues


def generate_overrides(
    model_key: str,
    dataset_key: str,
    spec: dict[str, Any],
) -> LLMResult:
    """Call the configured LLM and return validated replacement cells."""

    if model_key not in MODELS or dataset_key not in DATASETS:
        raise LLMError("Unknown model or dataset.")

    prompt = _build_user_prompt(model_key, dataset_key, spec)
    content, model_name = _call_provider(prompt)
    payload = _extract_json(content)

    overrides: dict[str, str] = {}
    for key in SECTION_KEYS:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise LLMError(f"LLM response is missing a non-empty '{key}' string.")
        if len(value) > settings.max_code_chars:
            raise LLMError(f"LLM section '{key}' exceeds the size limit.")
        overrides[key] = value.strip() + "\n"

    report = validate_code_sources(overrides.values(), section="llm")
    if not report["passed"]:
        messages = "; ".join(
            f"{finding['code']}: {finding['message']}" for finding in report["errors"]
        )
        raise LLMError(f"LLM code failed static validation: {messages}")

    token_issues = _check_required_tokens(model_key, overrides)
    if token_issues:
        raise LLMError(
            "LLM code did not honour the interface contract: " + "; ".join(token_issues)
        )

    notes = payload.get("notes")
    return LLMResult(
        overrides=overrides,
        provider=settings.provider,
        model=model_name,
        notes=notes if isinstance(notes, str) else "",
    )
