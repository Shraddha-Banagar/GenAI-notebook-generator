"""Reusable image-dataset setup, loading, BLIP and export sections."""

from __future__ import annotations

from typing import Any

from ..catalog import DATASETS
from .common import dedent, section

IMAGE_META: dict[str, dict[str, Any]] = {
    "fashion_mnist": {
        "loader": "fashion_mnist",
        "size": 28,
        "channels": 1,
        "reshape": True,
        "max_images": 20000,
        "display": "grayscale clothing",
    },
    "mnist": {
        "loader": "mnist",
        "size": 28,
        "channels": 1,
        "reshape": True,
        "max_images": 20000,
        "display": "grayscale digits",
    },
    "cifar10": {
        "loader": "cifar10",
        "size": 32,
        "channels": 3,
        "reshape": False,
        "max_images": 20000,
        "display": "colour objects",
    },
}


def image_meta(dataset_key: str) -> dict[str, Any]:
    return IMAGE_META[dataset_key]


def environment_sections(
    model_label: str,
    dataset_key: str,
    batch_size: int,
    epochs: int,
) -> list[dict[str, Any]]:
    dataset = DATASETS[dataset_key]
    meta = image_meta(dataset_key)
    setup = section(
        "setup",
        "1. Environment Setup",
        f"""
        Install the two optional runtime dependencies used by this notebook
        (`transformers` for BLIP, `pillow` for image export) and import the
        TensorFlow 2 / Keras stack. Google Colab already ships a GPU-enabled
        TensorFlow and PyTorch runtime.

        **Model:** {model_label} · **Dataset:** {dataset["label"]} ({dataset["shape"]})
        """,
        [
            """
            # Colab already provides TensorFlow 2.x and PyTorch. Only BLIP's
            # runtime dependencies need to be installed.
            !pip -q install "transformers>=4.40,<5" "pillow>=10.0.0"
            """,
            f"""
            %matplotlib inline
            import math
            import os
            import random

            import matplotlib.pyplot as plt
            import numpy as np
            import tensorflow as tf
            from PIL import Image

            SEED = 42
            BATCH_SIZE = {batch_size}
            EPOCHS = {epochs}
            LATENT_DIM = 128
            MAX_IMAGES = {meta["max_images"]}
            AUTOTUNE = tf.data.AUTOTUNE

            random.seed(SEED)
            np.random.seed(SEED)
            tf.random.set_seed(SEED)

            print("TensorFlow:", tf.__version__)
            print("GPU devices:", tf.config.list_physical_devices("GPU"))

            def to_display(images):
                \"\"\"Convert [-1, 1] tensors/arrays into uint8 display images.\"\"\"
                array = images.numpy() if hasattr(images, "numpy") else np.asarray(images)
                array = np.clip((array + 1.0) * 127.5, 0.0, 255.0).astype("uint8")
                if array.ndim == 4 and array.shape[-1] == 1:
                    array = array[..., 0]
                return array

            def show_images(images, title="", n=16, save_path=None):
                array = to_display(images)
                n = int(min(n, len(array)))
                cols = 4
                rows = int(np.ceil(n / cols))
                fig, axes = plt.subplots(rows, cols, figsize=(cols * 2.1, rows * 2.1))
                axes = np.array(axes).reshape(-1)
                for ax in axes:
                    ax.axis("off")
                for ax, image in zip(axes, array[:n]):
                    if image.ndim == 2:
                        ax.imshow(image, cmap="gray")
                    else:
                        ax.imshow(image)
                if title:
                    fig.suptitle(title, fontsize=14)
                plt.tight_layout()
                if save_path:
                    fig.savefig(save_path, dpi=140, bbox_inches="tight")
                plt.show()
                plt.close(fig)
            """,
        ],
        icon="terminal",
    )

    reshape = (
        f'images = images.reshape((-1, {meta["size"]}, {meta["size"]}, {meta["channels"]}))'
        if meta["reshape"]
        else "images = images[..., :3]"
    )
    data = section(
        "data",
        "2. Data Loading",
        f"""
        {dataset["description"]} Images are downloaded through
        `tf.keras.datasets` (no manual files), capped at **{meta["max_images"]:,}**
        samples for a fast Colab run, scaled to `[-1, 1]`, and batched.
        """,
        [
            f"""
            (x_train, _), (x_test, _) = tf.keras.datasets.{meta["loader"]}.load_data()
            images = np.concatenate([x_train, x_test], axis=0)[:MAX_IMAGES]

            {reshape}
            images = images.astype("float32")
            images = (images - 127.5) / 127.5

            IMAGE_SIZE = {meta["size"]}
            CHANNELS = images.shape[-1]
            print("images:", images.shape, "min/max:", float(images.min()), float(images.max()))

            train_ds = (
                tf.data.Dataset.from_tensor_slices(images)
                .shuffle(buffer_size=min(len(images), 10000), seed=SEED)
                .batch(BATCH_SIZE, drop_remainder=True)
                .prefetch(AUTOTUNE)
            )
            print("batches per epoch:", len(train_ds))

            sample_batch = next(iter(train_ds))
            show_images(sample_batch, title="{dataset["label"]} training samples", n=16)
            """,
        ],
        icon="database",
    )
    return [setup, data]


def blip_section(dataset_key: str) -> dict[str, Any]:
    return section(
        "blip",
        "6. BLIP Sanity Check",
        """
        **U3 — vision-language sanity check.** This cell loads
        [`Salesforce/blip-image-captioning-base`](https://huggingface.co/Salesforce/blip-image-captioning-base)
        with Hugging Face Transformers and captions the image exported by the
        inference cell. Early in training the caption is usually generic
        ("a close up of a ..."); after enough epochs it should reflect the
        dataset domain. This is a qualitative signal, not a metric.

        > BLIP runs on PyTorch in this cell; the generative model itself stays
        > pure TensorFlow 2 / Keras. Colab pre-installs both frameworks.
        """,
        [
            """
            import torch
            from PIL import Image
            from transformers import BlipForConditionalGeneration, BlipProcessor

            caption_device = "cuda" if torch.cuda.is_available() else "cpu"

            processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            ).to(caption_device)
            blip_model.eval()

            caption_image = Image.open(IMAGE_FOR_CAPTION_PATH).convert("RGB")
            inputs = processor(images=caption_image, return_tensors="pt").to(
                caption_device
            )
            with torch.no_grad():
                output = blip_model.generate(**inputs, max_new_tokens=40, num_beams=3)
            caption = processor.decode(output[0], skip_special_tokens=True)

            os.makedirs("/content/outputs", exist_ok=True)
            with open("/content/outputs/blip_caption.txt", "w", encoding="utf-8") as handle:
                handle.write(caption + "\\n")

            print("BLIP caption:", caption)
            plt.figure(figsize=(4, 4))
            plt.imshow(caption_image)
            plt.axis("off")
            plt.title(f"BLIP: {caption}")
            plt.show()
            """,
        ],
        icon="sparkles",
    )


def export_section(
    dataset_key: str,
    model_slug: str,
    save_code: str,
    *,
    section_number: int = 7,
) -> dict[str, Any]:
    dataset = DATASETS[dataset_key]
    license_text = (
        f"{dataset['label']} - {dataset['license']['name']}\n"
        f"Source: {dataset['source_url']}\n"
        f"Attribution: {dataset['license']['attribution']}\n"
        f"Notes: {dataset['license']['notes']}\n"
    )
    save_block = dedent(save_code).replace("\n", "\n            ")
    return section(
        "export",
        f"{section_number}. Save & Export",
        f"""
        Persist the trained weights and write the dataset license alongside the
        artifacts so the output bundle stays self-documenting.

        **License:** {dataset["license"]["name"]} · {dataset["license"]["url"]}
        """,
        [
            f"""
            os.makedirs("/content/outputs", exist_ok=True)

            {save_block}

            with open("/content/outputs/DATASET_LICENSE.txt", "w", encoding="utf-8") as handle:
                handle.write({license_text!r})

            print("Saved artifacts to /content/outputs")
            print(os.listdir("/content/outputs"))
            """,
        ],
        icon="download",
    )
