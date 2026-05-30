from __future__ import annotations

import json
import re
from collections.abc import Callable
from importlib import resources

from pydantic import ValidationError

from harness_builder_agent.schemas.scan import EvidenceBundle, LLMScanProposal
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig

SCAN_PROMPT_VERSION = "llm-first-scan-v2"
SCAN_PROMPT_RESOURCE = ("prompts", "llm_first_scan_v2.md")


def analyze_evidence_with_llm(
    evidence: EvidenceBundle,
    caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
) -> LLMScanProposal:
    messages = build_scan_messages(evidence)
    content = caller(messages) if caller else call_deepseek(messages, config=config)
    if not content.strip():
        raise ValueError("DeepSeek scan response is empty")
    return parse_llm_scan_response(content)


def build_scan_messages(evidence: EvidenceBundle) -> list[dict[str, str]]:
    system_prompt, user_prompt = _load_scan_prompt()
    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": (
                f"{user_prompt}\n\n"
                f"Evidence JSON:\n{evidence.model_dump_json(exclude_none=True)}"
            ),
        },
    ]


def _load_scan_prompt() -> tuple[str, str]:
    prompt = (
        resources.files("harness_builder_agent")
        .joinpath(*SCAN_PROMPT_RESOURCE)
        .read_text(encoding="utf-8")
        .strip()
    )
    system_marker = "## System Message"
    user_marker = "## User Message"
    if system_marker not in prompt or user_marker not in prompt:
        raise ValueError("Scan prompt asset must contain System Message and User Message sections")
    system_text, user_text = prompt.split(user_marker, 1)
    system_text = system_text.replace(system_marker, "", 1).strip()
    user_text = user_text.strip()
    return system_text, user_text


def parse_llm_scan_response(content: str) -> LLMScanProposal:
    raw = _extract_json_text(content)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek scan response must be valid JSON") from exc

    try:
        return LLMScanProposal.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"DeepSeek scan response failed schema validation: {exc}") from exc


def _extract_json_text(content: str) -> str:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped
