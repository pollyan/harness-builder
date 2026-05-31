from __future__ import annotations

import json
import re
from collections.abc import Callable

from pydantic import ValidationError

from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig
from harness_builder_agent.prompts.registry import LLM_MATURITY_REVIEW_V2, build_machine_prompt_messages

REVIEW_PROMPT_VERSION = LLM_MATURITY_REVIEW_V2.version


def review_maturity_with_llm(
    score: MaturityReport,
    evidence_pack: MaturityEvidencePack,
    candidates: ImprovementCandidateReport,
    experience_summary: ExperienceSummaryReport | None = None,
    caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
) -> MaturityReviewReport:
    messages = build_maturity_review_messages(score, evidence_pack, candidates, experience_summary=experience_summary)
    content = caller(messages) if caller else call_deepseek(messages, config=config)
    if not content.strip():
        raise ValueError("DeepSeek maturity review response is empty")
    candidate_ids = {candidate.id for candidate in candidates.candidates}
    return parse_maturity_review_response(content, candidate_ids)


def build_maturity_review_messages(
    score: MaturityReport,
    evidence_pack: MaturityEvidencePack,
    candidates: ImprovementCandidateReport,
    experience_summary: ExperienceSummaryReport | None = None,
) -> list[dict[str, str]]:
    payload = {
        "prompt_version": REVIEW_PROMPT_VERSION,
        "maturity_score": score.model_dump(mode="json"),
        "maturity_evidence": evidence_pack.model_dump(mode="json"),
        "improvement_candidates": candidates.model_dump(mode="json"),
        "experience_summary": experience_summary.model_dump(mode="json") if experience_summary else None,
    }
    return build_machine_prompt_messages(LLM_MATURITY_REVIEW_V2.key, payload)


def parse_maturity_review_response(content: str, candidate_ids: set[str]) -> MaturityReviewReport:
    raw = _extract_json_text(content)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek maturity review response must be valid JSON") from exc
    try:
        report = MaturityReviewReport.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"DeepSeek maturity review response failed schema validation: {exc}") from exc
    unknown = sorted({item.candidate_id for item in report.candidate_reviews} - candidate_ids)
    if unknown:
        raise ValueError(f"DeepSeek maturity review response referenced unknown candidate_id: {', '.join(unknown)}")
    return report


def _extract_json_text(content: str) -> str:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped
