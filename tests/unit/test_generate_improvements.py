from harness_builder_agent.schemas.interaction_decision import InteractionDecisions, WorkflowConfirmation
from harness_builder_agent.schemas.maturity_evidence import ExperienceEvidence, MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.tools.generate_improvements import _candidates


def test_candidates_include_workflow_policy_follow_up_for_workflow_recommendation_review():
    score = MaturityReport(overall_level="L2", target_next_level="L3")
    evidence = MaturityEvidencePack(
        repo_name="demo",
        primary_stack="java-spring",
        experience=ExperienceEvidence(workflow_recommendation_count=1),
        maturity_inputs=[".ai/review/workflow-routing-recommendation.yaml"],
    )

    candidates = _candidates(score, evidence)

    candidate = next(item for item in candidates if item.id == "experience-workflow-recommendation-review")
    assert candidate.candidate_type == "workflow_policy_update"
    assert candidate.suggested_target == ".ai/harness-config.yaml"
    assert candidate.human_confirmation_required is True
    assert candidate.target_dimension == "workflow"
    assert ".ai/review/workflow-routing-recommendation.yaml" in candidate.evidence_sources
    assert any("Workflow recommendation reviews: 1" in item for item in candidate.evidence)


def test_candidates_skip_workflow_recommendation_follow_up_when_no_review_signal():
    score = MaturityReport(overall_level="L2", target_next_level="L3")
    evidence = MaturityEvidencePack(repo_name="demo", primary_stack="java-spring")

    candidates = _candidates(score, evidence)

    assert all(item.id != "experience-workflow-recommendation-review" for item in candidates)


def test_candidates_include_workflow_policy_follow_up_for_review_only_workflow_note():
    score = MaturityReport(overall_level="L2", target_next_level="L3")
    evidence = MaturityEvidencePack(
        repo_name="demo",
        primary_stack="java-spring",
        maturity_inputs=[".ai/interaction-decisions.yaml", ".ai/human-input-needed.md"],
    )
    decisions = InteractionDecisions(
        mode="interactive",
        repo={"path": ".", "confirmed": True},
        workflow_confirmation=WorkflowConfirmation(
            shown_workflows=["lightweight", "bugfix"],
            confirmed=True,
            notes=["支付权限变更应走 standard workflow。"],
            impact_scopes=[
                "interaction_decisions",
                "project_context",
                "human_input_needed",
                "review_only_workflow_note",
            ],
            review_status="pending_harness_maintainer_review",
            routing_policy_effect="review_only_no_direct_policy_change",
        ),
    )

    candidates = _candidates(score, evidence, decisions)

    candidate = next(item for item in candidates if item.id == "interaction-workflow-note-review")
    assert candidate.candidate_type == "workflow_policy_update"
    assert candidate.suggested_target == ".ai/harness-config.yaml"
    assert candidate.human_confirmation_required is True
    assert candidate.target_dimension == "workflow"
    assert candidate.source_next_step == "workflow-note-review"
    assert ".ai/interaction-decisions.yaml" in candidate.evidence_sources
    assert ".ai/human-input-needed.md" in candidate.evidence_sources
    assert any("支付权限变更应走 standard workflow" in item for item in candidate.evidence)
    assert "review-only" in candidate.rationale


def test_candidates_skip_workflow_note_follow_up_when_note_is_not_review_only_pending():
    score = MaturityReport(overall_level="L2", target_next_level="L3")
    evidence = MaturityEvidencePack(repo_name="demo", primary_stack="java-spring")
    decisions = InteractionDecisions(
        mode="interactive",
        repo={"path": ".", "confirmed": True},
        workflow_confirmation=WorkflowConfirmation(
            shown_workflows=["lightweight", "bugfix"],
            confirmed=True,
            notes=["支付权限变更应走 standard workflow。"],
            review_status="not_required",
            routing_policy_effect="not_applicable",
        ),
    )

    candidates = _candidates(score, evidence, decisions)

    assert all(item.id != "interaction-workflow-note-review" for item in candidates)
