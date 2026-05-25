"""DeepSeek OpenAI-compatible client wrapper for Scanner v2.

Encapsulates DeepSeek API calls in an independently testable module.
Uses only standard library (urllib.request) for HTTP.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional
from urllib.request import Request, urlopen


@dataclass
class DeepSeekConfig:
    """Configuration for DeepSeek API calls.

    Environment variable fallback:
      - DEEPSEEK_API_KEY
      - DEEPSEEK_BASE_URL
      - DEEPSEEK_MODEL
    """

    api_key: str = ""
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-flash"
    max_tokens: int = 4096
    temperature: float = 0.0
    timeout: int = 60

    @classmethod
    def from_env(cls) -> DeepSeekConfig:
        """Build config from environment variables with defaults."""
        return cls(
            api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            model=os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        )


def call_deepseek(
    user_message: str,
    system_prompt: Optional[str] = None,
    config: Optional[DeepSeekConfig] = None,
) -> Optional[str]:
    """Call DeepSeek chat completions endpoint.

    Args:
        user_message: The user message to send.
        system_prompt: Optional system prompt prepended to messages.
        config: Optional config; uses from_env() if not provided.

    Returns:
        Response content string, or None on any error / missing API key.
    """
    if config is None:
        config = DeepSeekConfig.from_env()

    if not config.api_key:
        return None

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    body = json.dumps({
        "model": config.model,
        "messages": messages,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
    }).encode()

    url = f"{config.base_url.rstrip('/')}/chat/completions"
    req = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
    )

    try:
        with urlopen(req, timeout=config.timeout) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None
