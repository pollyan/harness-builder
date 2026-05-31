from __future__ import annotations

import json
import re
from collections.abc import Callable

from pydantic import ValidationError

from harness_builder_agent.schemas.scan import EvidenceBundle, LLMScanProposal
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig
from harness_builder_agent.prompts.registry import LLM_FIRST_SCAN_V2, build_machine_prompt_messages

SCAN_PROMPT_VERSION = LLM_FIRST_SCAN_V2.version


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
    payload = evidence.model_dump(mode="json", exclude_none=True)
    return build_machine_prompt_messages(LLM_FIRST_SCAN_V2.key, payload)


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
