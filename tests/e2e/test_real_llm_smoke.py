from __future__ import annotations

import json
import os
import urllib.request

import pytest


@pytest.mark.skipif(os.getenv("RUN_LLM_E2E") != "1", reason="RUN_LLM_E2E is not enabled")
@pytest.mark.skipif(not os.getenv("DEEPSEEK_API_KEY"), reason="DEEPSEEK_API_KEY is not configured")
def test_deepseek_real_llm_smoke():
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
