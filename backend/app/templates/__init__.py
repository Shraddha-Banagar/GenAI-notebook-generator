"""Notebook section template registry (U1)."""

from __future__ import annotations

from typing import Any

from ..catalog import DATASETS, MODELS
from . import char_rnn, dcgan, vae

BUILDERS = {
    "dcgan": dcgan.build_sections,
    "vae": vae.build_sections,
    "char_rnn": char_rnn.build_sections,
}


class TemplateError(ValueError):
    pass


def build_spec(
    model_key: str,
    dataset_key: str,
    *,
    batch_size: int,
    epochs: int,
) -> dict[str, Any]:
    model = MODELS.get(model_key)
    dataset = DATASETS.get(dataset_key)
    if model is None:
        raise TemplateError(f"Unknown model '{model_key}'.")
    if dataset is None:
        raise TemplateError(f"Unknown dataset '{dataset_key}'.")
    if dataset_key not in model["datasets"]:
        raise TemplateError(
            f"{model['label']} does not support {dataset['label']}. "
            f"Choose one of: {', '.join(model['datasets'])}."
        )
    if batch_size < 1 or batch_size > 512:
        raise TemplateError("Batch size must be between 1 and 512.")
    if epochs < 1 or epochs > 100:
        raise TemplateError("Epochs must be between 1 and 100.")

    builder = BUILDERS[model_key]
    sections = builder(dataset_key, batch_size=batch_size, epochs=epochs)
    return {
        "model": model,
        "dataset": dataset,
        "sections": sections,
        "settings": {
            "batch_size": batch_size,
            "epochs": epochs,
            "seed": 42,
        },
    }
