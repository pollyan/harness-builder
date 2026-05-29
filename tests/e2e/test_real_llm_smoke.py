from __future__ import annotations

import json
import os
import urllib.request

import pytest


def _load_local_env() -> None:
    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        return

    with open(env_path, encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key, value)


def test_deepseek_real_llm_smoke():
    _load_local_env()
    if not os.getenv("DEEPSEEK_API_KEY"):
        pytest.skip("DEEPSEEK_API_KEY is not configured")

    api_key = os.environ["DEEPSEEK_API_KEY"]
    base_url = os.getenv("HARNESS_BUILDER_LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.getenv("HARNESS_BUILDER_LLM_MODEL", "deepseek-v4-pro")
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a concise test responder."},
                {"role": "user", "content": "Reply with the word ok."},
            ],
            "stream": False,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        body = json.loads(response.read().decode("utf-8"))

    assert body["choices"][0]["message"]["content"]
