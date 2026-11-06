"""Static catalog of supported generative models and datasets.

This module is the single source of truth for:
  * model metadata shown by the frontend
  * dataset licensing injected into generated notebooks (U5)
  * dataset loading/preprocessing code used by the notebook templates
"""

from __future__ import annotations

from typing import Any

MODELS: dict[str, dict[str, Any]] = {
    "dcgan": {
        "id": "dcgan",
        "label": "DCGAN",
        "family": "Adversarial",
        "kind": "image",
        "icon": "images",
        "tagline": "Deep Convolutional GAN",
        "description": (
            "A convolutional generator/discriminator pair trained with a custom "
            "adversarial loop. Excellent for learning latent image synthesis."
        ),
        "datasets": ["fashion_mnist", "mnist", "cifar10"],
        "default_dataset": "fashion_mnist",
        "highlights": ["Custom train_step", "Latent walk sampling", "BLIP sanity check"],
    },
    "vae": {
        "id": "vae",
        "label": "VAE",
        "family": "Likelihood",
        "kind": "image",
        "icon": "layers",
        "tagline": "Variational Autoencoder",
        "description": (
            "An encoder/decoder with a Gaussian latent bottleneck and a KL "
            "regulariser. Produces smooth, interpolatable image manifolds."
        ),
        "datasets": ["fashion_mnist", "mnist", "cifar10"],
        "default_dataset": "fashion_mnist",
        "highlights": ["KL divergence loss", "Latent sampling", "BLIP sanity check"],
    },
    "char_rnn": {
        "id": "char_rnn",
        "label": "char-RNN",
        "family": "Autoregressive",
        "kind": "text",
        "icon": "type",
        "tagline": "Character-level GRU",
        "description": (
            "A stateful GRU language model trained character by character. "
            "Generates Shakespeare-style text with temperature control."
        ),
        "datasets": ["tiny_shakespeare"],
        "default_dataset": "tiny_shakespeare",
        "highlights": ["Stateful GRU", "Temperature sampling", "Checkpointing"],
    },
}

DATASETS: dict[str, dict[str, Any]] = {
    "fashion_mnist": {
        "id": "fashion_mnist",
        "label": "Fashion-MNIST",
        "kind": "image",
        "source": "tf.keras.datasets.fashion_mnist",
        "source_url": "https://github.com/zalandoresearch/fashion-mnist",
        "shape": "28 × 28 × 1",
        "samples": "70,000",
        "description": "70k grayscale clothing images across 10 classes.",
        "citation": "Xiao, Rasul & Vollgraf (2017). Fashion-MNIST: a Novel Image Dataset.",
        "license": {
            "name": "MIT",
            "url": "https://github.com/zalandoresearch/fashion-mnist/blob/master/LICENSE",
            "attribution": "Zalando SE",
            "commercial_use": True,
            "notes": "Permissive license; retain the copyright and permission notice.",
        },
        "loader": "fashion_mnist",
        "default_batch_size": 64,
    },
    "mnist": {
        "id": "mnist",
        "label": "MNIST",
        "kind": "image",
        "source": "tf.keras.datasets.mnist",
        "source_url": "https://yann.lecun.com/exdb/mnist/",
        "shape": "28 × 28 × 1",
        "samples": "70,000",
        "description": "70k handwritten digits — the classic generative modelling sandbox.",
        "citation": "LeCun, Cortes & Burges (1998). The MNIST Database of Handwritten Digits.",
        "license": {
            "name": "CC BY-SA 3.0",
            "url": "https://creativecommons.org/licenses/by-sa/3.0/",
            "attribution": "Yann LeCun and Corinna Cortes",
            "commercial_use": True,
            "notes": (
                "Widely distributed under CC BY-SA 3.0 terms. Derived works must be "
                "shared under a compatible license; verify the upstream terms."
            ),
        },
        "loader": "mnist",
        "default_batch_size": 64,
    },
    "cifar10": {
        "id": "cifar10",
        "label": "CIFAR-10",
        "kind": "image",
        "source": "tf.keras.datasets.cifar10",
        "source_url": "https://www.cs.toronto.edu/~kriz/cifar.html",
        "shape": "32 × 32 × 3",
        "samples": "60,000",
        "description": "60k colour images across 10 object classes.",
        "citation": "Krizhevsky (2009). Learning Multiple Layers of Features from Tiny Images.",
        "license": {
            "name": "Research use",
            "url": "https://www.cs.toronto.edu/~kriz/cifar.html",
            "attribution": "Alex Krizhevsky, University of Toronto",
            "commercial_use": False,
            "notes": (
                "CIFAR-10 does not ship an OSI-approved license. Treat it as "
                "research use and confirm terms with the dataset authors."
            ),
        },
        "loader": "cifar10",
        "default_batch_size": 64,
    },
    "tiny_shakespeare": {
        "id": "tiny_shakespeare",
        "label": "Tiny Shakespeare",
        "kind": "text",
        "source": "karpathy/char-rnn (GitHub)",
        "source_url": (
            "https://raw.githubusercontent.com/karpathy/char-rnn/"
            "master/data/tinyshakespeare/input.txt"
        ),
        "shape": "≈1.1 MB text · 65 unique chars",
        "samples": "≈1.1M characters",
        "description": "A compact public-domain corpus of Shakespeare's plays.",
        "citation": "Andrej Karpathy's char-rnn examples; Shakespeare source texts.",
        "license": {
            "name": "Public Domain",
            "url": "https://creativecommons.org/publicdomain/mark/1.0/",
            "attribution": "William Shakespeare (public-domain works)",
            "commercial_use": True,
            "notes": (
                "The corpus is derived from public-domain Shakespeare plays. "
                "No additional restrictions are asserted by the mirror."
            ),
        },
        "loader": "tiny_shakespeare",
        "default_batch_size": 64,
    },
}


def get_model(model_id: str) -> dict[str, Any] | None:
    return MODELS.get(model_id)


def get_dataset(dataset_id: str) -> dict[str, Any] | None:
    return DATASETS.get(dataset_id)


def model_datasets(model_id: str) -> list[dict[str, Any]]:
    model = MODELS.get(model_id)
    if not model:
        return []
    return [DATASETS[key] for key in model["datasets"]]


def public_catalog() -> dict[str, Any]:
    """Catalog payload for the React frontend."""

    return {
        "models": list(MODELS.values()),
        "datasets": list(DATASETS.values()),
        "palette": {
            "primary": "#A14646",
            "secondary": "#DA6556",
            "highlight": "#EB895B",
            "warning": "#FDB773",
        },
    }
