from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import PurePosixPath

from pydantic import ValidationError

from harness_builder_agent.prompts.registry import LLM_EVIDENCE_PLAN_V1, build_machine_prompt_messages
from harness_builder_agent.schemas.scan import EvidenceBundle, LLMEvidencePlan
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig

EVIDENCE_PLAN_PROMPT_VERSION = LLM_EVIDENCE_PLAN_V1.version


def plan_evidence_expansion_with_llm(
    evidence: EvidenceBundle,
    caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
) -> LLMEvidencePlan:
    messages = build_evidence_plan_messages(evidence)
    allowed_paths = {item.path for item in evidence.files}
    last_error: ValueError | None = None
    for attempt in range(2):
        content = caller(messages) if caller else call_deepseek(messages, config=config)
        if not content.strip():
            raise ValueError("DeepSeek evidence plan response is empty")
        try:
            return parse_llm_evidence_plan_response(content, allowed_paths)
        except ValueError as exc:
            last_error = exc
            if attempt == 1:
                break
            messages = _retry_messages(messages, content, exc)
    raise last_error if last_error else ValueError("DeepSeek evidence plan response failed validation")


def build_evidence_plan_messages(evidence: EvidenceBundle) -> list[dict[str, str]]:
    payload = evidence.model_dump(mode="json", exclude_none=True)
    return build_machine_prompt_messages(LLM_EVIDENCE_PLAN_V1.key, payload)


def _retry_messages(
    messages: list[dict[str, str]],
    invalid_content: str,
    error: ValueError,
) -> list[dict[str, str]]:
    return messages + [
        {"role": "assistant", "content": invalid_content},
        {
            "role": "user",
            "content": (
                "上一次 evidence plan 响应未通过契约校验。\n"
                f"校验错误：{error}\n\n"
                "请重新输出一个 JSON object。requested_paths 只能从 files[].path 中逐字复制路径；"
                "如果无法确认精确路径，请返回空的 requested_paths。不要发明、纠正或近似匹配路径。"
            ),
        },
    ]


def parse_llm_evidence_plan_response(content: str, allowed_paths: set[str]) -> LLMEvidencePlan:
    raw = _extract_json_text(content)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek evidence plan response must be valid JSON") from exc

    try:
        plan = LLMEvidencePlan.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"DeepSeek evidence plan response failed schema validation: {exc}") from exc

    for path in plan.requested_paths:
        _validate_requested_path(path, allowed_paths)
    return plan


def _validate_requested_path(path: str, allowed_paths: set[str]) -> None:
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"DeepSeek evidence plan requested path outside repository: {path}")
    if path.startswith(".ai/"):
        raise ValueError(f"DeepSeek evidence plan requested path outside repository: {path}")
    if path not in allowed_paths:
        raise ValueError(f"DeepSeek evidence plan requested unknown evidence path: {path}")


def _extract_json_text(content: str) -> str:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped
