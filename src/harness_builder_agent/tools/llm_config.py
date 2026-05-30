from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-pro"
    timeout_seconds: int = 60
    temperature: float = 0.1
    max_tokens: int = 8192

    @classmethod
    def from_env(cls, env_path: Path | None = None, load_dotenv: bool = True) -> "DeepSeekConfig":
        if load_dotenv:
            _load_dotenv(env_path or Path.cwd() / ".env")

        api_key = os.getenv("HARNESS_BUILDER_LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required for LLM-first scan")

        return cls(
            api_key=api_key,
            base_url=os.getenv("HARNESS_BUILDER_LLM_BASE_URL", "https://api.deepseek.com").rstrip("/"),
            model=os.getenv("HARNESS_BUILDER_LLM_MODEL", "deepseek-v4-pro"),
            timeout_seconds=int(os.getenv("HARNESS_BUILDER_LLM_TIMEOUT_SECONDS", "60")),
            temperature=float(os.getenv("HARNESS_BUILDER_LLM_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("HARNESS_BUILDER_LLM_MAX_TOKENS", "8192")),
        )


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
