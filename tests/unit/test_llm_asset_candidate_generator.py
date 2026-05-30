from __future__ import annotations

import json

import pytest

from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidate, ImprovementCandidateReport
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.schemas.maturity_evidence import HarnessAssetEvidence, MaturityEvidencePack, WorkflowRoutingRuleEvidence
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.tools.llm_asset_candidate_generator import (
    build_asset_candidate_messages,
    generate_asset_candidates_with_llm,
    parse_asset_candidate_response,
)


def _score() -> MaturityReport:
    return MaturityReport(overall_level="L2", target_next_level="L3", evidence=["summary"])


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


def _workflow_recommendation_improvement_candidates() -> ImprovementCandidateReport:
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


def _experience_summary() -> ExperienceSummaryReport:
    return ExperienceSummaryReport(
        summary="Workflow gaps are repeated.",
        findings=[
            {
                "id": "workflow-gap-routing",
                "kind": "workflow_gap",
                "title": "Workflow routing gap",
                "summary": "Experience findings point to missing routing rules.",
                "evidence_sources": [".ai/experience/experience-summary.yaml"],
                "confidence": "medium",
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


def test_generate_asset_candidates_accepts_workflow_policy_candidate():
    report = parse_asset_candidate_response(
        json.dumps(
            {
                "candidates": [
                    {
                        "id": "workflow-routing-standard-escalation",
                        "kind": "workflow_policy",
                        "source_candidate_id": "candidate-1",
                        "source_review_decision": "support",
                        "suggested_path": ".ai/harness-config.yaml",
                        "title": "Refine standard escalation routing",
                        "rationale": "Uses routing evidence.",
                        "draft_content": "workflow_routing:\n  rules:\n    - id: standard-escalation",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ]
            }
        ),
        {"candidate-1"},
    )

    assert report.candidates[0].kind == "workflow_policy"
    assert report.candidates[0].suggested_path == ".ai/harness-config.yaml"


def test_build_asset_candidate_messages_includes_experience_summary_when_present():
    messages = build_asset_candidate_messages(
        _score(),
        _evidence_pack(),
        _improvement_candidates(),
        _maturity_review(),
        experience_summary=_experience_summary(),
    )
    content = messages[-1]["content"]
    assert '"experience_summary"' in content
    assert "workflow-gap-routing" in content
    assert "workflow_routing_rules" in content
    assert "standard-escalation" in content
    assert "security_or_permission" in content
    assert "When drafting workflow_policy candidates" in content
    assert "pending_harness_maintainer_review" in content
    assert "review-only Experience Summary findings" in content


def test_build_asset_candidate_messages_guides_workflow_recommendation_candidate():
    evidence = _evidence_pack()
    evidence.maturity_inputs.append(".ai/review/workflow-routing-recommendation.yaml")

    messages = build_asset_candidate_messages(
        _score(),
        evidence,
        _workflow_recommendation_improvement_candidates(),
        MaturityReviewReport(
            summary="Workflow recommendation review should become a routing policy draft.",
            candidate_reviews=[
                {
                    "candidate_id": "experience-workflow-recommendation-review",
                    "decision": "support",
                    "rationale": "Routing policy should be reviewed.",
                }
            ],
        ),
    )

    content = messages[-1]["content"]
    assert "experience-workflow-recommendation-review" in content
    assert ".ai/review/workflow-routing-recommendation.yaml" in content
    assert "workflow_policy" in content
    assert ".ai/harness-config.yaml" in content
    assert "pending_harness_maintainer_review" in content
    assert "review-only workflow recommendation evidence" in content


def test_build_asset_candidate_messages_uses_null_experience_summary_when_absent():
    messages = build_asset_candidate_messages(_score(), _evidence_pack(), _improvement_candidates(), _maturity_review())
    assert '"experience_summary": null' in messages[-1]["content"]
