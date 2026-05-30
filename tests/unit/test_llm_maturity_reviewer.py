from __future__ import annotations

import json

import pytest

from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidate, ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.tools.llm_maturity_reviewer import parse_maturity_review_response, review_maturity_with_llm


def _score() -> MaturityReport:
    return MaturityReport(
        overall_level="L2",
        target_next_level="L3",
        dimension_scores={"guides": "L2"},
        evidence=["Guides exist."],
        blocking_reasons=["Guides are not task-routed."],
        recommended_next_steps=["Bind guides to workflows."],
    )


def _evidence_pack() -> MaturityEvidencePack:
    return MaturityEvidencePack(
        repo_name="demo",
        primary_stack="java-spring",
        maturity_inputs=[".ai/project-inventory.json", ".ai/command-catalog.yaml"],
        warnings=["runtime task-runs absent"],
    )


def _candidates() -> ImprovementCandidateReport:
    return ImprovementCandidateReport(
        candidates=[
            ImprovementCandidate(
                id="candidate-1",
                candidate_type="guide_update",
                suggested_target=".ai/guides/project-context.md",
                rationale="Bind guide to maturity gap.",
                target_dimension="guides",
                source_next_step="guides-bind-workflow",
                acceptance_checks=["Benchmark content:guides-quality passes."],
                evidence_sources=[".ai/maturity-evidence.yaml"],
            )
        ]
    )


def test_review_maturity_with_llm_returns_schema_valid_review():
    report = review_maturity_with_llm(
        _score(),
        _evidence_pack(),
        _candidates(),
        caller=lambda _messages: json.dumps(
            {
                "summary": "Review summary.",
                "reviewer_model": "deepseek-test",
                "candidate_reviews": [
                    {
                        "candidate_id": "candidate-1",
                        "decision": "support",
                        "rationale": "Candidate is aligned with maturity gap.",
                        "risks": [],
                        "suggested_acceptance_checks": ["Run benchmark."],
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                    }
                ],
                "missing_candidates": [],
                "global_risks": [],
            }
        ),
    )

    assert report.candidate_reviews[0].candidate_id == "candidate-1"


def test_review_maturity_with_llm_rejects_unknown_candidate_id():
    with pytest.raises(ValueError, match="unknown candidate_id"):
        review_maturity_with_llm(
            _score(),
            _evidence_pack(),
            _candidates(),
            caller=lambda _messages: json.dumps(
                {
                    "summary": "bad",
                    "candidate_reviews": [
                        {"candidate_id": "missing", "decision": "support", "rationale": "bad"}
                    ],
                }
            ),
        )


def test_parse_maturity_review_response_rejects_invalid_json():
    with pytest.raises(ValueError, match="must be valid JSON"):
        parse_maturity_review_response("not json", {"candidate-1"})
