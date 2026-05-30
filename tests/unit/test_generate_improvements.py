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
