from __future__ import annotations

import json
import re
from collections.abc import Callable

from pydantic import ValidationError

from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig

REVIEW_PROMPT_VERSION = "llm-maturity-review-v1"


def review_maturity_with_llm(
    score: MaturityReport,
    evidence_pack: MaturityEvidencePack,
    candidates: ImprovementCandidateReport,
    caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
) -> MaturityReviewReport:
    messages = build_maturity_review_messages(score, evidence_pack, candidates)
    content = caller(messages) if caller else call_deepseek(messages, config=config)
    if not content.strip():
        raise ValueError("DeepSeek maturity review response is empty")
    candidate_ids = {candidate.id for candidate in candidates.candidates}
    return parse_maturity_review_response(content, candidate_ids)


def build_maturity_review_messages(
    score: MaturityReport,
    evidence_pack: MaturityEvidencePack,
    candidates: ImprovementCandidateReport,
) -> list[dict[str, str]]:
    schema_contract = """
Return one JSON object only. Do not include markdown commentary.

Field contract:
- schema_version: "1.0".
- summary: short review summary.
- reviewer_model: model name if known, otherwise null.
- candidate_reviews: array of candidate review objects.
- candidate_reviews[].candidate_id must reference an existing improvement candidate id.
- candidate_reviews[].decision must be one of support, revise, defer.
- candidate_reviews[].rationale must explain the judgment using maturity evidence.
- candidate_reviews[].risks must be an array of concrete risks.
- candidate_reviews[].suggested_acceptance_checks must be an array of concrete checks.
- candidate_reviews[].evidence_sources must reference provided .ai evidence paths.
- missing_candidates: array of missing improvement ideas, strings only.
- global_risks: array of cross-candidate risks.

Do not claim any Harness asset was edited. This is review-only output.
Prefer "revise" when a candidate is directionally useful but underspecified.
Prefer "defer" when evidence is too weak.
""".strip()
    payload = {
        "prompt_version": REVIEW_PROMPT_VERSION,
        "maturity_score": score.model_dump(mode="json"),
        "maturity_evidence": evidence_pack.model_dump(mode="json"),
        "improvement_candidates": candidates.model_dump(mode="json"),
    }
    return [
        {
            "role": "system",
            "content": (
                "You are the LLM maturity reviewer for Harness Builder. "
                "You review deterministic improvement candidates and return strict JSON only."
            ),
        },
        {
            "role": "user",
            "content": f"{schema_contract}\n\nReview input JSON:\n{json.dumps(payload, ensure_ascii=False)}",
        },
    ]


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
