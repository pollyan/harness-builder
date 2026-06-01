from __future__ import annotations

import inspect

from harness_builder_agent.tools import existing_harness_action_runner as runner
from harness_builder_agent.tools import existing_harness_intelligent_actions as intelligent_actions
from harness_builder_agent.tools import existing_harness_review_actions as review_actions


def test_existing_harness_review_actions_have_dedicated_module() -> None:
    assert hasattr(review_actions, "run_review_candidate_action")
    assert hasattr(review_actions, "run_review_human_input_action")
    assert hasattr(review_actions, "run_review_initial_candidate_action")


def test_existing_harness_runner_delegates_review_actions() -> None:
    source = inspect.getsource(runner)

    assert "run_review_candidate_action(" in source
    assert "run_review_human_input_action(" in source
    assert "run_review_initial_candidate_action(" in source
    assert "review_candidate(" not in source
    assert "review_human_input(" not in source
    assert "review_weapon_candidate(" not in source
    assert "CandidateGovernanceLog" not in source
    assert "HumanInputGovernanceLog" not in source
    assert "WeaponCandidateGovernanceLog" not in source


def test_existing_harness_intelligent_actions_have_dedicated_module() -> None:
    assert hasattr(intelligent_actions, "run_recommend_workflow_action")
    assert hasattr(intelligent_actions, "run_self_improve_action")


def test_existing_harness_runner_delegates_intelligent_actions() -> None:
    source = inspect.getsource(runner)

    assert "run_recommend_workflow_action(" in source
    assert "run_self_improve_action(" in source
    assert "recommend_workflow(" not in source
    assert "run_self_improve(" not in source
    assert "WorkflowRecommendationReport" not in source
    assert "SelfImprovePackageManifest" not in source
