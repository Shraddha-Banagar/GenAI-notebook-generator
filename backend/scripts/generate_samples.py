"""Generate the two sample notebooks committed to /samples.

Run from the repository root:

    python backend/scripts/generate_samples.py

The script uses the deterministic templates (no API key required), validates
every generated notebook, writes the .ipynb files, and emits a JSON report.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.catalog import DATASETS, MODELS  # noqa: E402
from app.notebook_builder import (  # noqa: E402
    build_notebook,
    notebook_filename,
    notebook_to_dict,
    write_notebook,
)
from app.templates import build_spec  # noqa: E402
from app.validation import validate_notebook  # noqa: E402

SAMPLES_DIR = ROOT_DIR / "samples"

SAMPLE_REQUESTS = [
    {"model": "dcgan", "dataset": "fashion_mnist", "epochs": 5, "batch_size": 64},
    {"model": "char_rnn", "dataset": "tiny_shakespeare", "epochs": 5, "batch_size": 64},
]


def main() -> int:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "deterministic-template",
        "samples": [],
    }

    for request in SAMPLE_REQUESTS:
        spec = build_spec(
            request["model"],
            request["dataset"],
            batch_size=request["batch_size"],
            epochs=request["epochs"],
        )
        generation_meta = {
            "source": "template",
            "provider": None,
            "llm_model": None,
            "fallback_reason": "Sample generation uses deterministic templates.",
        }
        notebook = build_notebook(spec, generation_meta=generation_meta)
        payload = notebook_to_dict(notebook)
        validation = validate_notebook(payload)

        if not validation["passed"]:
            print(f"FAILED validation for {request['model']}/{request['dataset']}")
            print(json.dumps(validation["errors"], indent=2))
            return 1

        filename = notebook_filename(request["model"], request["dataset"])
        path = write_notebook(notebook, SAMPLES_DIR / filename)

        sample_report = {
            "filename": filename,
            "model": request["model"],
            "model_label": MODELS[request["model"]]["label"],
            "dataset": request["dataset"],
            "dataset_label": DATASETS[request["dataset"]]["label"],
            "license": DATASETS[request["dataset"]]["license"],
            "settings": spec["settings"],
            "cells": len(payload["cells"]),
            "code_cells": validation["stats"]["code_cells"],
            "python_lines": validation["stats"]["python_lines"],
            "validation": validation,
            "bytes": path.stat().st_size,
        }
        report["samples"].append(sample_report)
        print(
            f"wrote {path.relative_to(ROOT_DIR)} "
            f"({sample_report['cells']} cells, {sample_report['bytes']:,} bytes) "
            f"validation={'passed' if validation['passed'] else 'failed'}"
        )

    report_path = SAMPLES_DIR / "generation_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {report_path.relative_to(ROOT_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
