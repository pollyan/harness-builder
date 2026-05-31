from __future__ import annotations

import json
import re
from collections.abc import Callable

from pydantic import ValidationError

from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig
from harness_builder_agent.prompts.loader import load_prompt_sections

ASSET_CANDIDATE_PROMPT_VERSION = "llm-asset-candidate-v2"
ASSET_CANDIDATE_PROMPT_RESOURCE = "llm_asset_candidate_v2.md"


def generate_asset_candidates_with_llm(
    score: MaturityReport,
    evidence_pack: MaturityEvidencePack,
    improvement_candidates: ImprovementCandidateReport,
    maturity_review: MaturityReviewReport,
    experience_summary: ExperienceSummaryReport | None = None,
    caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
) -> AssetCandidateReport:
    messages = build_asset_candidate_messages(
        score,
        evidence_pack,
        improvement_candidates,
        maturity_review,
        experience_summary=experience_summary,
    )
    content = caller(messages) if caller else call_deepseek(messages, config=config)
    if not content.strip():
        raise ValueError("DeepSeek asset candidate response is empty")
    candidate_ids = {candidate.id for candidate in improvement_candidates.candidates}
    return parse_asset_candidate_response(content, candidate_ids)


def build_asset_candidate_messages(
    score: MaturityReport,
    evidence_pack: MaturityEvidencePack,
    improvement_candidates: ImprovementCandidateReport,
    maturity_review: MaturityReviewReport,
    experience_summary: ExperienceSummaryReport | None = None,
) -> list[dict[str, str]]:
    system_prompt, user_prompt = load_prompt_sections(ASSET_CANDIDATE_PROMPT_RESOURCE)
    payload = {
        "prompt_version": ASSET_CANDIDATE_PROMPT_VERSION,
        "maturity_score": score.model_dump(mode="json"),
        "maturity_evidence": evidence_pack.model_dump(mode="json"),
        "improvement_candidates": improvement_candidates.model_dump(mode="json"),
        "maturity_review": maturity_review.model_dump(mode="json"),
        "experience_summary": experience_summary.model_dump(mode="json") if experience_summary else None,
    }
    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": f"{user_prompt}\n\nCandidate generation input JSON:\n{json.dumps(payload, ensure_ascii=False)}",
        },
    ]


def parse_asset_candidate_response(content: str, candidate_ids: set[str]) -> AssetCandidateReport:
    raw = _extract_json_text(content)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek asset candidate response must be valid JSON") from exc
    try:
        report = AssetCandidateReport.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"DeepSeek asset candidate response failed schema validation: {exc}") from exc

    unknown = sorted(
        {
            candidate.source_candidate_id
            for candidate in report.candidates
            if candidate.source_candidate_id
            and candidate.source_review_decision != "missing"
            and candidate.source_candidate_id not in candidate_ids
        }
    )
    if unknown:
        raise ValueError(f"DeepSeek asset candidate response referenced unknown source_candidate_id: {', '.join(unknown)}")

    bad_paths = [candidate.suggested_path for candidate in report.candidates if not candidate.suggested_path.startswith(".ai/")]
    if bad_paths:
        raise ValueError(f"DeepSeek asset candidate suggested_path must be under .ai/: {', '.join(sorted(bad_paths))}")
    return report


def _extract_json_text(content: str) -> str:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped
