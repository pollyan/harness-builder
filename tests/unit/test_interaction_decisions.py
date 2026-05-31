from __future__ import annotations

import pytest
from pydantic import ValidationError

from harness_builder_agent.schemas.interaction_decision import (
    CandidateDecision,
    ContextConfirmation,
    FinalConfirmation,
    InteractionDecisions,
    RepoConfirmation,
    ScanConfirmation,
    WorkflowConfirmation,
)
from harness_builder_agent.tools.interaction_decisions import (
    apply_candidate_decisions,
    default_non_interactive_decisions,
    interaction_decisions_markdown,
)


def test_interaction_decisions_schema_accepts_interactive_confirmation():
    decisions = InteractionDecisions(
        mode="interactive",
        repo=RepoConfirmation(path="/repo", confirmed=True),
        scan_confirmation=ScanConfirmation(status="accepted", notes=["确认 Java Spring 判断"]),
        context_confirmation=ContextConfirmation(
            status="confirmed",
            confirmed_paths=["/repo/team-rules.md"],
            inline_contexts=["所有 Controller 只能调用 Service"],
        ),
        candidate_decisions=[
            CandidateDecision(candidate_id="llm-guide-risk-001", decision="accepted", notes="团队认可"),
            CandidateDecision(candidate_id="llm-sensor-command-001", decision="edited", notes="先保持候选，后续确认稳定性"),
        ],
        workflow_confirmation=WorkflowConfirmation(
            shown_workflows=["lightweight", "bugfix"],
            confirmed=True,
            notes=["轻量任务和缺陷修复两个工作流符合当前团队习惯"],
            impact_scopes=[
                "interaction_decisions",
                "project_context",
                "human_input_needed",
                "review_only_workflow_note",
            ],
            review_status="pending_harness_maintainer_review",
            routing_policy_effect="review_only_no_direct_policy_change",
        ),
        final_confirmation=FinalConfirmation(status="confirmed"),
    )

    payload = decisions.model_dump(mode="json")

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "interactive"
    assert payload["repo"]["confirmed"] is True
    assert payload["candidate_decisions"][0]["decision"] == "accepted"
    assert payload["candidate_decisions"][1]["decision"] == "edited"
    assert payload["workflow_confirmation"]["shown_workflows"] == ["lightweight", "bugfix"]
    assert payload["workflow_confirmation"]["confirmed"] is True
    assert payload["workflow_confirmation"]["impact_scopes"] == [
        "interaction_decisions",
        "project_context",
        "human_input_needed",
        "review_only_workflow_note",
    ]
    assert payload["workflow_confirmation"]["review_status"] == "pending_harness_maintainer_review"
    assert payload["workflow_confirmation"]["routing_policy_effect"] == "review_only_no_direct_policy_change"


def test_interaction_decisions_schema_rejects_invalid_candidate_decision():
    with pytest.raises(ValidationError):
        CandidateDecision(candidate_id="candidate-1", decision="promote")


def test_default_non_interactive_decisions_record_missing_human_confirmation():
    decisions = default_non_interactive_decisions("/repo", context_paths=["/repo/team-rules.md"])

    assert decisions.mode == "non_interactive"
    assert decisions.repo.confirmed is False
    assert decisions.scan_confirmation.status == "not_confirmed"
    assert decisions.context_confirmation.status == "not_confirmed"
    assert decisions.context_confirmation.confirmed_paths == []
    assert decisions.workflow_confirmation.impact_scopes == []
    assert decisions.workflow_confirmation.review_status == "not_required"
    assert decisions.workflow_confirmation.routing_policy_effect == "not_applicable"
    assert decisions.final_confirmation.status == "not_confirmed"


def test_apply_candidate_decisions_updates_statuses_and_reasons():
    report = {
        "schema_version": "1.0",
        "source": "llm_scan_proposal",
        "candidates": [
            {"id": "llm-guide-risk-001", "status": "candidate", "human_confirmation_required": True},
            {"id": "llm-sensor-command-001", "status": "candidate", "human_confirmation_required": True},
            {"id": "llm-guide-keep-001", "status": "candidate", "human_confirmation_required": True},
        ],
    }
    decisions = InteractionDecisions(
        mode="interactive",
        repo=RepoConfirmation(path="/repo", confirmed=True),
        candidate_decisions=[
            CandidateDecision(candidate_id="llm-guide-risk-001", decision="accepted", notes="认可"),
            CandidateDecision(candidate_id="llm-sensor-command-001", decision="rejected", notes="命令不稳定"),
            CandidateDecision(candidate_id="llm-guide-keep-001", decision="edited", notes="保持候选，但说明适用范围"),
        ],
    )

    updated = apply_candidate_decisions(report, decisions)
    by_id = {item["id"]: item for item in updated["candidates"]}

    assert by_id["llm-guide-risk-001"]["status"] == "confirmed"
    assert by_id["llm-guide-risk-001"]["human_confirmation_required"] is False
    assert by_id["llm-guide-risk-001"]["decision_notes"] == "认可"
    assert by_id["llm-sensor-command-001"]["status"] == "rejected"
    assert by_id["llm-sensor-command-001"]["decision_notes"] == "命令不稳定"
    assert by_id["llm-guide-keep-001"]["status"] == "candidate"
    assert by_id["llm-guide-keep-001"]["decision_notes"] == "保持候选，但说明适用范围"


def test_interaction_decisions_markdown_summarizes_decisions():
    decisions = InteractionDecisions(
        mode="interactive",
        repo=RepoConfirmation(path="/repo", confirmed=True),
        scan_confirmation=ScanConfirmation(status="accepted"),
        context_confirmation=ContextConfirmation(status="confirmed", inline_contexts=["团队测试策略"]),
        workflow_confirmation=WorkflowConfirmation(
            shown_workflows=["lightweight", "bugfix"],
            confirmed=True,
            notes=["缺陷修复需要先定位原因"],
            impact_scopes=[
                "interaction_decisions",
                "project_context",
                "human_input_needed",
                "review_only_workflow_note",
            ],
            review_status="pending_harness_maintainer_review",
            routing_policy_effect="review_only_no_direct_policy_change",
        ),
        final_confirmation=FinalConfirmation(status="confirmed"),
    )

    markdown = interaction_decisions_markdown(decisions)

    assert "# Interaction Decisions" in markdown
    assert "mode: interactive" in markdown
    assert "scan: accepted" in markdown
    assert "团队测试策略" in markdown
    assert "workflow_confirmed: True" in markdown
    assert "workflow_impact_scopes: interaction_decisions, project_context, human_input_needed, review_only_workflow_note" in markdown
    assert "workflow_review_status: pending_harness_maintainer_review" in markdown
    assert "workflow_routing_policy_effect: review_only_no_direct_policy_change" in markdown
    assert "缺陷修复需要先定位原因" in markdown
