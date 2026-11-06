"""Runtime smoke test for the generated Keras cells.

This is intentionally small: it loads the committed sample notebooks, replaces
the data pipeline with a tiny synthetic/short corpus, runs 1 epoch and a few
generation steps, and verifies that architecture, training, inference and export
cells execute. It does not run BLIP (that needs a 1 GB model download).

    python backend/scripts/runtime_smoke.py
"""

from __future__ import annotations

import json
import os
import platform
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("MPLBACKEND", "Agg")

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

import nbformat  # noqa: E402
import numpy as np  # noqa: E402
import tensorflow as tf  # noqa: E402

from app.notebook_builder import build_notebook, write_notebook  # noqa: E402
from app.templates import build_spec  # noqa: E402
from app.validation import _prepare_python  # noqa: E402

SAMPLES = ROOT_DIR / "samples"
RUNTIME_REPORT = SAMPLES / "runtime_report.json"
RESULTS: list[dict[str, str]] = []


def source_of(cell) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def code_cells(notebook, section: str) -> list[str]:
    return [
        source_of(cell)
        for cell in notebook.cells
        if cell.cell_type == "code" and cell.metadata.get("genai_section") == section
    ]


def run(source: str, namespace: dict, label: str) -> None:
    python_source, _ = _prepare_python(source)
    exec(compile(python_source, f"<{label}>", "exec"), namespace)  # noqa: S102


def image_smoke(model_key: str, notebook_path: Path) -> None:
    notebook = nbformat.read(notebook_path, as_version=4)
    setup_cells = code_cells(notebook, "setup")
    assert len(setup_cells) >= 2, "expected pip + imports setup cells"
    namespace: dict = {"__name__": "__main__"}
    run(setup_cells[1], namespace, f"{model_key}-setup")
    namespace.update(EPOCHS=1, BATCH_SIZE=8, IMAGE_SIZE=28, CHANNELS=1)

    images = np.random.uniform(-1, 1, (16, 28, 28, 1)).astype("float32")
    namespace["train_ds"] = tf.data.Dataset.from_tensor_slices(images).batch(8)

    run(code_cells(notebook, "architecture")[0], namespace, f"{model_key}-architecture")
    run(code_cells(notebook, "training")[0], namespace, f"{model_key}-training")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir).as_posix()
        inference = code_cells(notebook, "inference")[0].replace(
            '"/content/' + model_key + '_sample.png"', f'"{temp}/{model_key}_sample.png"'
        )
        run(inference, namespace, f"{model_key}-inference")
        assert Path(f"{temp}/{model_key}_sample.png").exists()

        export = code_cells(notebook, "export")[0].replace('"/content/outputs', f'"{temp}/outputs')
        run(export, namespace, f"{model_key}-export")
        saved = list(Path(f"{temp}/outputs").glob("*"))
        assert any(path.suffix in {".keras", ".h5", ".txt"} for path in saved), saved

    RESULTS.append({"pipeline": f"{model_key}_image", "status": "passed"})
    print(f"[ok] {model_key} image pipeline")


def char_rnn_smoke(filename: str) -> None:
    notebook = nbformat.read(SAMPLES / filename, as_version=4)
    namespace: dict = {"__name__": "__main__"}
    run(code_cells(notebook, "setup")[0], namespace, "char-setup")
    namespace["EPOCHS"] = 1

    with tempfile.TemporaryDirectory() as temp_dir:
        corpus = (
            "ROMEO: But soft, what light through yonder window breaks?\n"
            "JULIET: O Romeo, Romeo! wherefore art thou Romeo?\n"
        ) * 400
        corpus_path = Path(temp_dir) / "corpus.txt"
        corpus_path.write_text(corpus, encoding="utf-8")
        namespace["tf"].keras.utils.get_file = lambda *args, **kwargs: str(corpus_path)

        run(code_cells(notebook, "data")[0], namespace, "char-data")
        namespace["dataset"] = namespace["dataset"].take(2)

        run(code_cells(notebook, "architecture")[0], namespace, "char-architecture")
        run(code_cells(notebook, "training")[0], namespace, "char-training")

        inference = code_cells(notebook, "inference")[0]
        inference = inference.replace("num_generate=500", "num_generate=20")
        inference = inference.replace(', 300, 0.6', ', 10, 0.6')
        run(inference, namespace, "char-inference")
        assert namespace["generated_text"].startswith("ROMEO: ")

        temp = Path(temp_dir).as_posix()
        export = code_cells(notebook, "export")[0].replace('"/content/outputs', f'"{temp}/outputs')
        run(export, namespace, "char-export")
        assert Path(f"{temp}/outputs/generated_text.txt").exists()

    RESULTS.append({"pipeline": "char_rnn_text", "status": "passed"})
    print("[ok] char-RNN text pipeline")


def main() -> int:
    global STARTED_AT
    STARTED_AT = time.perf_counter()
    RUNTIME_REPORT.unlink(missing_ok=True)

    valid_targets = {"dcgan", "vae", "char"}
    requested = set(sys.argv[1:])
    unknown = requested - valid_targets
    if unknown:
        print(f"unknown targets: {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2
    targets = requested or valid_targets

    if "dcgan" in targets:
        image_smoke("dcgan", SAMPLES / "dcgan_fashion_mnist.ipynb")

    if "vae" in targets:
        with tempfile.TemporaryDirectory() as temp_dir:
            vae_notebook = Path(temp_dir) / "vae_fashion_mnist.ipynb"
            spec = build_spec("vae", "fashion_mnist", batch_size=8, epochs=1)
            write_notebook(
                build_notebook(spec, generation_meta={"source": "template"}),
                vae_notebook,
            )
            image_smoke("vae", vae_notebook)

    if "char" in targets:
        char_rnn_smoke("char_rnn_tiny_shakespeare.ipynb")

    gpu_devices = [device.name for device in tf.config.list_physical_devices("GPU")]
    report = {
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round(time.perf_counter() - STARTED_AT, 1),
        "environment": {
            "python": platform.python_version(),
            "tensorflow": tf.__version__,
            "gpu_devices": gpu_devices,
        },
        "targets": sorted(targets),
        "pipelines": RESULTS,
        "passed": True,
        "note": (
            "Reduced-data CPU smoke test. BLIP captioning and full training were "
            "not executed; run the notebooks in Colab for full workloads."
        ),
    }
    RUNTIME_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"runtime smoke checks passed; wrote {RUNTIME_REPORT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
