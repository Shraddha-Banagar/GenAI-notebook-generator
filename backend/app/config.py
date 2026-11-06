"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # python-dotenv is optional at runtime
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is a convenience only
    pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SAMPLES_DIR = Path(os.getenv("SAMPLES_DIR", BASE_DIR / "samples"))

PROVIDER_DEFAULTS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
}


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    app_name: str = "GenAI Notebook Generator"
    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "groq").lower())
    api_key: str = field(
        default_factory=lambda: (
            os.getenv("LLM_API_KEY")
            or os.getenv("GROQ_API_KEY")
            or os.getenv("OPENAI_API_KEY", "")
        )
    )
    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", ""))
    base_url: str = field(default_factory=lambda: os.getenv("LLM_BASE_URL", ""))
    timeout_seconds: float = field(default_factory=lambda: float(os.getenv("LLM_TIMEOUT", "90")))
    max_code_chars: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_CODE_CHARS", "60000")))
    cors_origins: list[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,"
                "http://localhost:4173,http://127.0.0.1:4173",
            )
        )
    )

    @property
    def resolved_base_url(self) -> str:
        if self.base_url:
            return self.base_url.rstrip("/")
        return PROVIDER_DEFAULTS.get(self.provider, PROVIDER_DEFAULTS["openai"])["base_url"]

    @property
    def resolved_model(self) -> str:
        if self.model:
            return self.model
        return PROVIDER_DEFAULTS.get(self.provider, PROVIDER_DEFAULTS["openai"])["model"]

    @property
    def llm_enabled(self) -> bool:
        return self.provider not in {"", "none", "off", "disabled"} and bool(self.api_key)

    def describe(self) -> dict[str, object]:
        return {
            "provider": self.provider,
            "model": self.resolved_model if self.llm_enabled else None,
            "configured": self.llm_enabled,
        }


settings = Settings()
