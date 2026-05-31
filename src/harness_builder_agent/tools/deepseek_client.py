from __future__ import annotations

import json
import urllib.request
from typing import Any

from harness_builder_agent.tools.llm_config import DeepSeekConfig

MAX_EMPTY_CONTENT_ATTEMPTS = 2


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
    last_empty_detail = ""
    for _attempt in range(MAX_EMPTY_CONTENT_ATTEMPTS):
        with urllib.request.urlopen(request, timeout=cfg.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        choice = body["choices"][0]
        message = choice.get("message", {})
        content = message.get("content") or ""
        if content.strip():
            return content
        last_empty_detail = (
            f"finish_reason={choice.get('finish_reason')!r}; "
            f"message_keys={sorted(message.keys())}; "
            f"reasoning_content_present={bool(message.get('reasoning_content'))}"
        )
    raise ValueError(f"DeepSeek response content is empty after retry; {last_empty_detail}")
