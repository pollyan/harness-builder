from __future__ import annotations

import json
import re
from collections.abc import Callable

from pydantic import ValidationError

from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig
from harness_builder_agent.prompts.loader import load_prompt_sections

EXPERIENCE_SUMMARY_PROMPT_VERSION = "llm-experience-summary-v1"
EXPERIENCE_SUMMARY_PROMPT_RESOURCE = "llm_experience_summary_v1.md"


def summarize_experience_with_llm(
    index: ExperienceIndex,
    sources: dict[str, str],
    caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
) -> ExperienceSummaryReport:
    messages = build_experience_summary_messages(index, sources)
    content = caller(messages) if caller else call_deepseek(messages, config=config)
    if not content.strip():
        raise ValueError("DeepSeek experience summary response is empty")
    return parse_experience_summary_response(content, set(sources))


def build_experience_summary_messages(index: ExperienceIndex, sources: dict[str, str]) -> list[dict[str, str]]:
    system_prompt, user_prompt = load_prompt_sections(EXPERIENCE_SUMMARY_PROMPT_RESOURCE)
    payload = {
        "prompt_version": EXPERIENCE_SUMMARY_PROMPT_VERSION,
        "experience_index": index.model_dump(mode="json"),
        "sources": sources,
    }
    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": f"{user_prompt}\n\nExperience input JSON:\n{json.dumps(payload, ensure_ascii=False)}",
        },
    ]


def parse_experience_summary_response(content: str, evidence_sources: set[str]) -> ExperienceSummaryReport:
    raw = _extract_json_text(content)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek experience summary response must be valid JSON") from exc
    try:
        report = ExperienceSummaryReport.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"DeepSeek experience summary response failed schema validation: {exc}") from exc
    bad_paths = sorted({source for finding in report.findings for source in finding.evidence_sources if not source.startswith(".ai/")})
    if bad_paths:
        raise ValueError(f"DeepSeek experience summary evidence_sources must be under .ai/: {', '.join(bad_paths)}")
    unknown = sorted({source for finding in report.findings for source in finding.evidence_sources if source not in evidence_sources})
    if unknown:
        raise ValueError(f"DeepSeek experience summary referenced unknown evidence_sources: {', '.join(unknown)}")
    return report


def _extract_json_text(content: str) -> str:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped
