from __future__ import annotations

import json

import pytest

from harness_builder_agent.schemas.experience_index import ExperienceSource
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidate, ImprovementCandidateReport
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.schemas.maturity_evidence import (
    ExperienceEvidence,
    HarnessAssetEvidence,
    MaturityEvidencePack,
    WorkflowRoutingRuleEvidence,
)
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.tools.llm_maturity_reviewer import (
    build_maturity_review_messages,
    parse_maturity_review_response,
    review_maturity_with_llm,
)


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
        harness_assets=HarnessAssetEvidence(
            workflow_routing_rule_count=1,
            has_standard_escalation_rule=True,
            workflow_routing_rules=[
                WorkflowRoutingRuleEvidence(
                    id="standard-escalation",
                    selected_workflow="standard",
                    task_type_hints=["feature"],
                    triggers=["high_risk_module", "security_or_permission"],
                    required_guides=[".ai/guides/architecture.md"],
                    required_sensors=[".ai/sensors/verification.md"],
                    human_confirmation_required=True,
                    rationale="Escalate risky work.",
                )
            ],
        ),
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


def _workflow_recommendation_candidates() -> ImprovementCandidateReport:
    return ImprovementCandidateReport(
        candidates=[
            ImprovementCandidate(
                id="experience-workflow-recommendation-review",
                candidate_type="workflow_policy_update",
                suggested_target=".ai/harness-config.yaml",
                rationale="Review workflow recommendation evidence.",
                evidence=[
                    "Workflow recommendation reviews: 1.",
                    "Recommendation artifacts are review-only and must not be treated as applied routing changes.",
                ],
                target_dimension="workflow",
                evidence_sources=[
                    ".ai/maturity-evidence.yaml",
                    ".ai/review/workflow-routing-recommendation.yaml",
                ],
            )
        ]
    )


def _experience_summary() -> ExperienceSummaryReport:
    return ExperienceSummaryReport(
        summary="Sensor coverage is the main repeated issue.",
        findings=[
            {
                "id": "sensor-coverage-gap",
                "kind": "sensor_feedback",
                "title": "Sensor coverage gap",
                "summary": "Pending improvements point to missing sensor coverage.",
                "evidence_sources": [".ai/experience/pending-improvements.md"],
                "confidence": "high",
            }
        ],
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


def test_build_maturity_review_messages_includes_experience_summary_when_present():
    messages = build_maturity_review_messages(_score(), _evidence_pack(), _candidates(), experience_summary=_experience_summary())
    content = messages[-1]["content"]
    assert '"experience_summary"' in content
    assert "sensor-coverage-gap" in content
    assert "standard-escalation" in content
    assert "security_or_permission" in content
    assert "review-only Experience Summary findings" in content


def test_build_maturity_review_messages_guides_workflow_recommendation_candidate():
    evidence = _evidence_pack()
    evidence.maturity_inputs.append(".ai/review/workflow-routing-recommendation.yaml")

    messages = build_maturity_review_messages(
        _score(),
        evidence,
        _workflow_recommendation_candidates(),
    )

    content = messages[-1]["content"]
    assert "experience-workflow-recommendation-review" in content
    assert ".ai/review/workflow-routing-recommendation.yaml" in content
    assert "workflow_routing_rules" in content
    assert "review-only workflow recommendation evidence" in content
    assert "support or revise" in content
    assert "must not claim" in content


def test_build_maturity_review_messages_guides_experience_source_details():
    evidence = _evidence_pack()
    evidence.experience = ExperienceEvidence(
        has_experience_index=True,
        sources=[
            ExperienceSource(path=".ai/review/maturity-review.yaml", kind="maturity_review", item_count=1),
            ExperienceSource(path=".ai/review/asset-candidates.yaml", kind="asset_candidates", item_count=2),
            ExperienceSource(path=".ai/review/workflow-routing-recommendation.yaml", kind="workflow_recommendation", item_count=1),
        ],
    )

    messages = build_maturity_review_messages(_score(), evidence, _candidates())

    content = messages[-1]["content"]
    assert "maturity_evidence.experience.sources" in content
    assert "path, kind, and item_count" in content
    assert ".ai/review/asset-candidates.yaml" in content
    assert "review-only source index" in content
    assert "not applied Harness changes" in content


def test_build_maturity_review_messages_uses_null_experience_summary_when_absent():
    messages = build_maturity_review_messages(_score(), _evidence_pack(), _candidates())
    assert '"experience_summary": null' in messages[-1]["content"]
