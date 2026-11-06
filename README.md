# GenAI Notebook Generator (TF2/Keras)

A full-stack tool that generates validated, runnable Google Colab notebooks for
three TensorFlow/Keras model families:

| Model | Type | Datasets | Required sample |
| --- | --- | --- | --- |
| DCGAN | Image generation | Fashion-MNIST, MNIST, CIFAR-10 | `samples/dcgan_fashion_mnist.ipynb` |
| VAE | Image reconstruction | Fashion-MNIST, MNIST, CIFAR-10 | Generated on demand |
| Char-RNN | Text generation | Tiny Shakespeare | `samples/char_rnn_tiny_shakespeare.ipynb` |

Every image notebook includes a BLIP image-captioning cell. Every notebook starts
with a dataset-license Markdown cell and is validated before download.

## Stack

- Backend: FastAPI, Pydantic 2, `nbformat`, TensorFlow 2.x, Hugging Face BLIP.
- Frontend: React 18, Vite 5, Tailwind CSS 3, Lucide icons.
- LLM: optional Groq or OpenAI-compatible chat completions with deterministic
  template fallback.
- Design: warm dark UI using `#A14646`, `#DA6556`, `#EB895B`, and `#FDB773`
  with layered mesh/grid overlays.

## Quick Start

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: <http://127.0.0.1:8000/docs>

The backend boots without an LLM key. `use_llm=true` requests fall back to the
deterministic templates when no provider is configured.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. Vite proxies `/api` to
`http://127.0.0.1:8000`.

For a static build:

```powershell
npm run build
```

Set `VITE_API_BASE_URL` when the API is on another origin. See
`frontend/.env.example`.

## LLM Configuration

Edit `backend/.env`:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
LLM_MODEL=llama-3.3-70b-versatile
# LLM_BASE_URL=https://api.groq.com/openai/v1

# Or use an OpenAI-compatible endpoint:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=...
# LLM_MODEL=gpt-4o-mini
# LLM_BASE_URL=https://api.openai.com/v1

LLM_TIMEOUT=60
```

`LLM_API_KEY`, `GROQ_API_KEY`, and `OPENAI_API_KEY` are read in that order.
`LLM_MODEL` and `LLM_BASE_URL` override the provider defaults shown above.

The LLM can only replace the architecture, training, and inference cells.
Setup, dataset loading, BLIP captioning, export, and licensing cells remain
generator-controlled. Generated code must pass the same static validation and
required-token contract as the templates; otherwise the API reports the failure
and uses the template fallback.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service metadata |
| `GET` | `/api/health` | Health, registry IDs, and LLM status |
| `GET` | `/api/catalog` | Models, datasets, licenses, defaults |
| `GET` | `/api/samples` | Sample notebook metadata and download URLs |
| `GET` | `/api/samples/{sample_id}` | Download a sample `.ipynb` |
| `POST` | `/api/validate` | Validate notebook JSON or a notebook string |
| `POST` | `/api/generate` | Return generated notebook JSON |
| `POST` | `/api/generate/file` | Return a downloadable `.ipynb` |

Example:

```powershell
$body = @{
  model = "dcgan"
  dataset = "fashion_mnist"
  use_llm = $false
  epochs = 10
  batch_size = 64
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/api/generate `
  -ContentType application/json `
  -Body $body
```

Key response fields:

- `notebook`: nbformat 4.5 dictionary.
- `validation`: `passed`, errors, warnings, checks.
- `generation`: `template` or `llm`, plus `llm_attempted` and fallback reason.
- `meta`: model/dataset labels, license, source URL, and notebook path.

## Notebook Anatomy

Each notebook uses section-tagged code cells (`setup`, `data`, `architecture`,
`training`, `inference`, `blip`, `export`) and contains:

1. Title Markdown cell.
2. Dataset-license Markdown cell with a stable `Dataset license` heading.
3. Runtime setup (`tensorflow>=2.15,<2.20`).
4. Dataset loading and preprocessing.
5. Model architecture.
6. Training loop.
7. Inference and sample generation.
8. BLIP image captioning for image models.
9. Artifact export to `/content/outputs`, including the dataset license.

### U1: Notebook generation lifecycle

`backend/app/notebook_builder.py` builds an `nbformat` 4.5 document with stable
cell IDs, section metadata, license injection, and JSON serialization.
`backend/app/templates/` owns the code cells.

### U2: Optional LLM code generation

`backend/app/llm_service.py` asks for one JSON object containing three code
strings, extracts fenced JSON safely, checks required tokens, and validates the
combined notebook before accepting it.

### U3: Vision-language metadata

`backend/app/templates/image_common.py` downloads
`Salesforce/blip-image-captioning-base`, captions the generated sample, and
saves `blip_caption.txt`. The notebook records `genai.model_kind`; the validator
requires BLIP only for image notebooks.

### U4: TF2 compatibility validation

`backend/app/validation.py` checks Python syntax with `ast.parse`, rejects
TensorFlow 1.x patterns such as `tf.Session`, `tf.placeholder`, and
`tf.compat.v1`, and verifies that `import tensorflow` exists and that TF 2 APIs
are used.

### U5: License and safety validation

The validator enforces nbformat 4.5, unique cell IDs, a license cell first, and
a shell-command allow-list. Code is analyzed for dangerous imports and calls
(`subprocess`, `os.system`, `exec`, `eval`, `socket`, etc.) and unsafe
`getattr` attribute access.

## Samples

- `samples/dcgan_fashion_mnist.ipynb` - 16 cells, Fashion-MNIST DCGAN with BLIP.
- `samples/char_rnn_tiny_shakespeare.ipynb` - 13 cells, stateful GRU char-RNN.
- `samples/generation_report.json` - validation status and metadata.
- `samples/runtime_report.json` - reduced-data smoke-test environment and results
  (written by `backend/scripts/runtime_smoke.py`).

Both `.ipynb` files are exact JSON documents. To inspect one as a Python dict:

```powershell
python -c "import json,nbformat; print(json.dumps(nbformat.read('samples/dcgan_fashion_mnist.ipynb', as_version=4), indent=2))"
```

Regenerate samples after changing templates:

```powershell
python backend/scripts/generate_samples.py
```

The local runtime smoke test executes the generated cells with a tiny synthetic
image batch and a short Shakespeare subset. It needs TensorFlow locally:

```powershell
pip install -r backend/requirements-runtime.txt
python backend/scripts/runtime_smoke.py
# Or target specific pipelines:
python backend/scripts/runtime_smoke.py vae char
```

This validates DCGAN, VAE, export, BLIP-input image creation, char-RNN training,
text generation, and artifact export on CPU. Full BLIP captioning and full
training should be run in Colab with a GPU.

## Tests

```powershell
python -m pytest backend/tests -q
cd frontend; npm run build
```

The test suite covers validation failures, TF1 rejection, notebook structure,
license placement, BLIP requirements, sample integrity, and all API endpoints.

## Project Layout

```text
backend/
  app/
    catalog.py          Model and dataset registry
    config.py           Environment settings
    llm_service.py      Groq/OpenAI-compatible generation
    main.py             FastAPI routes
    notebook_builder.py nbformat assembly
    validation.py       Syntax, TF2, license, and safety checks
    templates/          Deterministic Keras notebook sections
  scripts/
    generate_samples.py
    runtime_smoke.py
  tests/
frontend/
  src/
    components/
    lib/api.js
    App.jsx
    index.css
samples/
  dcgan_fashion_mnist.ipynb
  char_rnn_tiny_shakespeare.ipynb
  generation_report.json
  runtime_report.json
```

## Notes

- Image notebooks use TensorFlow/Keras for the model and PyTorch/Transformers
  only for BLIP captioning.
- BLIP model download is roughly 1 GB and is cached by Hugging Face.
- The frontend never executes notebook code; execution stays inside Colab or
  the local smoke script.
- Datasets are downloaded from their original TensorFlow/Keras or Project
  Gutenberg sources; license text and source URLs are preserved in the
  notebooks and exported artifacts.
