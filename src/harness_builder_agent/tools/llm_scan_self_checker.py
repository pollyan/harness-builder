from __future__ import annotations

import json
import re
from collections.abc import Callable

from pydantic import ValidationError

from harness_builder_agent.prompts.registry import LLM_SCAN_SELF_CHECK_V1, build_machine_prompt_messages
from harness_builder_agent.schemas.scan import EvidenceBundle, ScanMetadata, ScanSelfCheckReport
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig

SCAN_SELF_CHECK_PROMPT_VERSION = LLM_SCAN_SELF_CHECK_V1.version


def review_scan_followups_with_llm(
    evidence: EvidenceBundle,
    metadata: ScanMetadata,
    caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
) -> ScanSelfCheckReport:
    messages = build_scan_self_check_messages(evidence, metadata)
    content = caller(messages) if caller else call_deepseek(messages, config=config)
    if not content.strip():
        raise ValueError("DeepSeek scan self-check response is empty")
    return parse_scan_self_check_response(
        content,
        allowed_interaction_ids=_allowed_interaction_ids(metadata),
        allowed_evidence_sources=_allowed_evidence_sources(evidence, metadata),
    )


def build_scan_self_check_messages(evidence: EvidenceBundle, metadata: ScanMetadata) -> list[dict[str, str]]:
    payload = {
        "evidence": evidence.model_dump(mode="json", exclude_none=True),
        "scan_metadata": metadata.model_dump(mode="json", exclude_none=True),
    }
    return build_machine_prompt_messages(LLM_SCAN_SELF_CHECK_V1.key, payload)


def parse_scan_self_check_response(
    content: str,
    *,
    allowed_interaction_ids: set[str],
    allowed_evidence_sources: set[str],
) -> ScanSelfCheckReport:
    raw = _extract_json_text(content)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek scan self-check response must be valid JSON") from exc

    try:
        report = ScanSelfCheckReport.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"DeepSeek scan self-check response failed schema validation: {exc}") from exc

    for resolution in report.resolutions:
        if resolution.interaction_id not in allowed_interaction_ids:
            raise ValueError(f"DeepSeek scan self-check returned unknown interaction id: {resolution.interaction_id}")
        for source in resolution.evidence_sources:
            if source not in allowed_evidence_sources:
                raise ValueError(f"DeepSeek scan self-check returned unknown evidence source: {source}")
    return report


def _allowed_interaction_ids(metadata: ScanMetadata) -> set[str]:
    return {question.interaction_id for question in metadata.followup_questions}


def _allowed_evidence_sources(evidence: EvidenceBundle, metadata: ScanMetadata) -> set[str]:
    sources: set[str] = set()
    for group in (
        evidence.files,
        evidence.key_files,
        evidence.config_files,
        evidence.ci_files,
        evidence.documents,
        evidence.source_samples,
        evidence.priority_files,
        evidence.test_files,
        evidence.api_entrypoints,
        evidence.risk_files,
        evidence.llm_requested_files,
    ):
        sources.update(item.path for item in group)
    for question in metadata.followup_questions:
        sources.update(question.evidence)
    for warning in metadata.warnings:
        sources.add(warning.code)
        sources.update(warning.evidence)
    if metadata.evidence_expansion:
        sources.update(metadata.evidence_expansion.requested_paths)
        sources.update(metadata.evidence_expansion.read_paths)
        sources.update(metadata.evidence_expansion.risk_focus)
    return {source for source in sources if source and not source.startswith(".ai/")}


def _extract_json_text(content: str) -> str:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped
