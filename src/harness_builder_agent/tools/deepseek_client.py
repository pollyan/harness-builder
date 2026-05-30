from __future__ import annotations

import json
import urllib.request
from typing import Any

from harness_builder_agent.tools.llm_config import DeepSeekConfig


def call_deepseek(messages: list[dict[str, str]], config: DeepSeekConfig | None = None) -> str:
    cfg = config or DeepSeekConfig.from_env()
    payload: dict[str, Any] = {
        "model": cfg.model,
        "messages": messages,
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "stream": False,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        f"{cfg.base_url}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=cfg.timeout_seconds) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]
