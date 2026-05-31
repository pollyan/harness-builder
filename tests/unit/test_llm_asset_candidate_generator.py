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


def _allowed_sources() -> set[str]:
    return {".ai/maturity-evidence.yaml", ".ai/review/maturity-review.yaml"}


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
            allowed_evidence_sources=_allowed_sources(),
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
            allowed_evidence_sources=_allowed_sources(),
        )


def test_generate_asset_candidates_rejects_path_traversal_suggested_path():
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
                            "suggested_path": ".ai/../README.md",
                            "title": "Bad",
                            "rationale": "Path traversal.",
                            "draft_content": "content",
                        }
                    ]
                }
            ),
            {"candidate-1"},
            allowed_evidence_sources=_allowed_sources(),
        )


def test_generate_asset_candidates_rejects_workflow_policy_non_config_target():
    with pytest.raises(ValueError, match="workflow_policy candidates can only target .ai/harness-config.yaml"):
        parse_asset_candidate_response(
            json.dumps(
                {
                    "candidates": [
                        {
                            "id": "workflow-routing-standard-escalation",
                            "kind": "workflow_policy",
                            "source_candidate_id": "candidate-1",
                            "source_review_decision": "support",
                            "suggested_path": ".ai/guides/project-context.md",
                            "title": "Bad workflow target",
                            "rationale": "Workflow policy must target harness config.",
                            "draft_content": "Structured workflow policy patch.",
                            "workflow_policy_patch": {
                                "schema_version": "1.0",
                                "operation": "upsert_routing_rule",
                                "target": "workflow_routing.rules",
                                "rule": {
                                    "id": "standard-escalation",
                                    "selected_workflow": "standard",
                                    "rationale": "Escalate high-risk tasks.",
                                    "triggers": [
                                        "high_risk_module",
                                        "cross_module_design",
                                        "security_or_permission",
                                        "insufficient_sensor_coverage",
                                    ],
                                    "required_guides": [".ai/guides/project-context.md"],
                                    "required_sensors": [".ai/sensors/verification.md"],
                                    "human_confirmation_required": True,
                                },
                            },
                            "review_status": "pending_harness_maintainer_review",
                        }
                    ]
                }
            ),
            {"candidate-1"},
            allowed_evidence_sources=_allowed_sources(),
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
                        "draft_content": "Structured workflow policy patch.",
                        "workflow_policy_patch": {
                            "schema_version": "1.0",
                            "operation": "upsert_routing_rule",
                            "target": "workflow_routing.rules",
                            "rule": {
                                "id": "standard-escalation",
                                "selected_workflow": "standard",
                                "rationale": "Escalate high-risk tasks.",
                                "triggers": [
                                    "high_risk_module",
                                    "cross_module_design",
                                    "security_or_permission",
                                    "insufficient_sensor_coverage",
                                ],
                                "required_guides": [".ai/guides/project-context.md"],
                                "required_sensors": [".ai/sensors/verification.md"],
                                "human_confirmation_required": True,
                            },
                        },
                        "review_status": "pending_harness_maintainer_review",
                    }
                ]
            }
        ),
        {"candidate-1"},
        allowed_evidence_sources=_allowed_sources(),
    )

    assert report.candidates[0].kind == "workflow_policy"
    assert report.candidates[0].suggested_path == ".ai/harness-config.yaml"


def test_generate_asset_candidates_rejects_unknown_evidence_source():
    with pytest.raises(ValueError, match="unknown evidence_sources"):
        parse_asset_candidate_response(
            json.dumps(
                {
                    "candidates": [
                        {
                            "id": "bad-evidence",
                            "kind": "guide",
                            "source_candidate_id": "candidate-1",
                            "source_review_decision": "support",
                            "suggested_path": ".ai/guides/project-context.md",
                            "title": "Bad evidence",
                            "rationale": "Unknown evidence.",
                            "draft_content": "content",
                            "evidence_sources": [".ai/review/missing.yaml"],
                            "review_status": "pending_harness_maintainer_review",
                        }
                    ]
                }
            ),
            {"candidate-1"},
            allowed_evidence_sources=_allowed_sources(),
        )


def test_generate_asset_candidates_rejects_non_ai_evidence_source():
    with pytest.raises(ValueError, match="evidence_sources must be under .ai/"):
        parse_asset_candidate_response(
            json.dumps(
                {
                    "candidates": [
                        {
                            "id": "bad-evidence",
                            "kind": "guide",
                            "source_candidate_id": "candidate-1",
                            "source_review_decision": "support",
                            "suggested_path": ".ai/guides/project-context.md",
                            "title": "Bad evidence",
                            "rationale": "Bad evidence.",
                            "draft_content": "content",
                            "evidence_sources": ["README.md"],
                            "review_status": "pending_harness_maintainer_review",
                        }
                    ]
                }
            ),
            {"candidate-1"},
            allowed_evidence_sources=_allowed_sources(),
        )


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


def test_build_asset_candidate_messages_declares_complete_candidate_schema_and_output_limits():
    messages = build_asset_candidate_messages(_score(), _evidence_pack(), _improvement_candidates(), _maturity_review())
    content = messages[-1]["content"]

    for field in (
        "candidates[].id",
        "candidates[].kind",
        "candidates[].source_candidate_id",
        "candidates[].source_review_decision",
        "candidates[].suggested_path",
        "candidates[].title",
        "candidates[].rationale",
        "candidates[].draft_content",
        "candidates[].workflow_policy_patch",
        "candidates[].evidence_sources",
        "candidates[].acceptance_checks",
        "candidates[].risk_level",
        "candidates[].review_status",
    ):
        assert field in content
    assert "At most 5 candidates" in content
    assert '"id": "stable-kebab-case-id"' in content
    assert '"title": "Human review title"' in content
    assert '"rationale": "Why this candidate follows from the reviewed maturity evidence."' in content


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
    assert "workflow_policy_patch" in content
    assert '"operation": "upsert_routing_rule"' in content
    assert "pending_harness_maintainer_review" in content
    assert "review-only workflow recommendation evidence" in content


def test_build_asset_candidate_messages_guides_experience_source_details():
    evidence = _evidence_pack()
    evidence.experience = ExperienceEvidence(
        has_experience_index=True,
        sources=[
            ExperienceSource(path=".ai/review/maturity-review.yaml", kind="maturity_review", item_count=1),
            ExperienceSource(path=".ai/review/asset-candidates.yaml", kind="asset_candidates", item_count=2),
            ExperienceSource(path=".ai/review/workflow-routing-recommendation.yaml", kind="workflow_recommendation", item_count=1),
        ],
    )

    messages = build_asset_candidate_messages(_score(), evidence, _improvement_candidates(), _maturity_review())

    content = messages[-1]["content"]
    assert "maturity_evidence.experience.sources" in content
    assert "path, kind, and item_count" in content
    assert ".ai/review/maturity-review.yaml" in content
    assert "review-only source index" in content
    assert "Do not invent missing source paths" in content


def test_build_asset_candidate_messages_uses_null_experience_summary_when_absent():
    messages = build_asset_candidate_messages(_score(), _evidence_pack(), _improvement_candidates(), _maturity_review())
    assert '"experience_summary": null' in messages[-1]["content"]
