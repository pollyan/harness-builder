from __future__ import annotations

import json

import pytest

from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidate, ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.tools.llm_asset_candidate_generator import (
    generate_asset_candidates_with_llm,
    parse_asset_candidate_response,
)


def _score() -> MaturityReport:
    return MaturityReport(overall_level="L2", target_next_level="L3", evidence=["summary"])


def _evidence_pack() -> MaturityEvidencePack:
    return MaturityEvidencePack(
        repo_name="demo",
        primary_stack="java-spring",
        maturity_inputs=[".ai/project-inventory.json"],
    )


def _improvement_candidates() -> ImprovementCandidateReport:
    return ImprovementCandidateReport(
        candidates=[
            ImprovementCandidate(
                id="candidate-1",
                candidate_type="guide_update",
                suggested_target=".ai/guides/project-context.md",
                rationale="Guide needs task scope.",
            )
        ]
    )


def _maturity_review() -> MaturityReviewReport:
    return MaturityReviewReport(
        summary="Review summary.",
        candidate_reviews=[
            {
                "candidate_id": "candidate-1",
                "decision": "support",
                "rationale": "Candidate is aligned.",
            }
        ],
    )


def test_generate_asset_candidates_with_llm_returns_schema_valid_candidates():
    report = generate_asset_candidates_with_llm(
        _score(),
        _evidence_pack(),
        _improvement_candidates(),
        _maturity_review(),
        caller=lambda _messages: json.dumps(
            {
                "candidates": [
                    {
                        "id": "guide-project-context-scope",
                        "kind": "guide",
                        "source_candidate_id": "candidate-1",
                        "source_review_decision": "support",
                        "suggested_path": ".ai/guides/project-context.md",
                        "title": "Scope project context guide",
                        "rationale": "Grounded in review.",
                        "draft_content": "## Candidate Addition\n\nAdd scope.",
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                        "acceptance_checks": ["Benchmark content:guides-quality passes."],
                        "risk_level": "medium",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ]
            }
        ),
    )

    assert report.candidates[0].source_candidate_id == "candidate-1"


def test_generate_asset_candidates_rejects_unknown_source_candidate_id():
    with pytest.raises(ValueError, match="unknown source_candidate_id"):
        parse_asset_candidate_response(
            json.dumps(
                {
                    "candidates": [
                        {
                            "id": "bad",
                            "kind": "guide",
                            "source_candidate_id": "missing",
                            "source_review_decision": "support",
                            "suggested_path": ".ai/guides/project-context.md",
                            "title": "Bad",
                            "rationale": "Bad source.",
                            "draft_content": "content",
                        }
                    ]
                }
            ),
            {"candidate-1"},
        )


def test_generate_asset_candidates_rejects_non_ai_path():
    with pytest.raises(ValueError, match="suggested_path must be under .ai/"):
        parse_asset_candidate_response(
            json.dumps(
                {
                    "candidates": [
                        {
                            "id": "bad",
                            "kind": "guide",
                            "source_candidate_id": "candidate-1",
                            "source_review_decision": "support",
                            "suggested_path": "README.md",
                            "title": "Bad",
                            "rationale": "Bad path.",
                            "draft_content": "content",
                        }
                    ]
                }
            ),
            {"candidate-1"},
        )
