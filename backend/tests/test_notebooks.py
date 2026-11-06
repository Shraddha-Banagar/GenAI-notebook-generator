from pathlib import Path

import nbformat
from nbformat.validator import validate as validate_nbformat

from app.catalog import DATASETS
from app.notebook_builder import build_notebook, notebook_filename, notebook_to_dict
from app.templates import build_spec
from app.validation import validate_notebook

ROOT = Path(__file__).resolve().parents[2]


def _build(model: str, dataset: str, epochs: int = 1, batch_size: int = 16) -> dict:
    spec = build_spec(model, dataset, batch_size=batch_size, epochs=epochs)
    notebook = build_notebook(spec, generation_meta={"source": "template"})
    payload = notebook_to_dict(notebook)
    validate_nbformat(nbformat.from_dict(payload))
    return payload


def test_dcgan_notebook_structure_and_license():
    payload = _build("dcgan", "fashion_mnist")
    report = validate_notebook(payload)
    assert report["passed"]

    first = payload["cells"][0]
    assert first["cell_type"] == "markdown"
    first_source = "".join(first["source"])
    assert "Dataset license" in first_source
    assert DATASETS["fashion_mnist"]["license"]["name"] in first_source

    text = "\n".join(
        "".join(cell["source"]) for cell in payload["cells"]
    )
    assert "Salesforce/blip-image-captioning-base" in text
    assert "IMAGE_FOR_CAPTION_PATH" in text
    assert "def train_step" in text
    assert payload["metadata"]["genai"]["model_kind"] == "image"


def test_char_rnn_notebook_structure():
    payload = _build("char_rnn", "tiny_shakespeare")
    report = validate_notebook(payload)
    assert report["passed"]

    text = "\n".join("".join(cell["source"]) for cell in payload["cells"])
    assert "build_model" in text
    assert "generated_text" in text
    assert "BLIP" not in text
    assert payload["metadata"]["genai"]["model_kind"] == "text"
    assert "Public Domain" in "".join(payload["cells"][0]["source"])


def test_filenames_are_stable():
    assert notebook_filename("dcgan", "fashion_mnist") == "dcgan_fashion_mnist.ipynb"
    assert (
        notebook_filename("char_rnn", "tiny_shakespeare")
        == "char_rnn_tiny_shakespeare.ipynb"
    )


def test_committed_samples_validate():
    for filename in ["dcgan_fashion_mnist.ipynb", "char_rnn_tiny_shakespeare.ipynb"]:
        path = ROOT / "samples" / filename
        assert path.exists(), f"Missing sample {filename}"
        notebook = nbformat.read(path, as_version=4)
        validate_nbformat(notebook)
        payload = nbformat.from_dict(notebook)
        report = validate_notebook(payload)
        assert report["passed"], report["errors"]
