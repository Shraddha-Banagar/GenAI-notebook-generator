from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_and_catalog():
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    catalog = client.get("/api/catalog")
    assert catalog.status_code == 200
    payload = catalog.json()
    assert len(payload["models"]) == 3
    assert len(payload["datasets"]) == 4
    assert payload["palette"]["primary"] == "#A14646"


def test_generate_without_llm():
    response = client.post(
        "/api/generate",
        json={
            "model": "dcgan",
            "dataset": "fashion_mnist",
            "epochs": 1,
            "batch_size": 16,
            "use_llm": False,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["filename"] == "dcgan_fashion_mnist.ipynb"
    assert payload["validation"]["passed"] is True
    assert payload["generation"]["source"] == "template"
    assert payload["notebook"]["cells"][0]["cell_type"] == "markdown"
    assert "Dataset license" in "".join(payload["notebook"]["cells"][0]["source"])


def test_generate_char_rnn_without_llm():
    response = client.post(
        "/api/generate",
        json={
            "model": "char_rnn",
            "dataset": "tiny_shakespeare",
            "epochs": 2,
            "batch_size": 32,
            "use_llm": False,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["validation"]["passed"] is True
    metadata = payload["notebook"]["metadata"]["genai"]
    assert metadata["model_kind"] == "text"
    assert payload["meta"]["license"]["name"] == "Public Domain"


def test_incompatible_dataset_rejected():
    response = client.post(
        "/api/generate",
        json={
            "model": "dcgan",
            "dataset": "tiny_shakespeare",
            "epochs": 1,
            "batch_size": 16,
            "use_llm": False,
        },
    )
    assert response.status_code == 422


def test_validate_endpoint_flags_dangerous_code():
    response = client.post("/api/validate", json={"code": "import subprocess"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["passed"] is False
    assert payload["errors"]


def test_samples_endpoint():
    response = client.get("/api/samples")
    assert response.status_code == 200
    samples = response.json()["samples"]
    assert {sample["id"] for sample in samples} == {
        "dcgan_fashion_mnist",
        "char_rnn_tiny_shakespeare",
    }
    for sample in samples:
        download = client.get(sample["download_url"])
        assert download.status_code == 200
        assert download.headers["content-type"].startswith("application/x-ipynb+json")
