from __future__ import annotations

import pytest
from pydantic import ValidationError

from harness_builder_agent.schemas.command_catalog import CommandDefinition
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
    accepted_interactive_decisions,
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
            impact_scopes=[
                "interaction_decisions",
                "project_context",
                "human_input_needed",
                "guide_context",
                "review_only_team_context",
            ],
            review_status="pending_harness_maintainer_review",
            policy_effect="context_only_no_direct_policy_change",
        ),
        candidate_decisions=[
            CandidateDecision(candidate_id="llm-guide-risk-001", decision="accepted", notes="团队认可"),
            CandidateDecision(candidate_id="llm-sensor-command-001", decision="edited", notes="先保持候选，后续确认稳定性"),
        ],
        workflow_confirmation=WorkflowConfirmation(
            shown_workflows=["lightweight", "bugfix", "standard"],
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
    assert payload["scan_confirmation"]["impact_scopes"] == []
    assert payload["scan_confirmation"]["review_status"] == "not_required"
    assert payload["scan_confirmation"]["fact_effect"] == "not_applicable"
    assert payload["context_confirmation"]["impact_scopes"] == [
        "interaction_decisions",
        "project_context",
        "human_input_needed",
        "guide_context",
        "review_only_team_context",
    ]
    assert payload["context_confirmation"]["review_status"] == "pending_harness_maintainer_review"
    assert payload["context_confirmation"]["policy_effect"] == "context_only_no_direct_policy_change"
    assert payload["candidate_decisions"][0]["decision"] == "accepted"
    assert payload["candidate_decisions"][1]["decision"] == "edited"
    assert payload["workflow_confirmation"]["shown_workflows"] == ["lightweight", "bugfix", "standard"]
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


def test_context_confirmation_rejects_invalid_impact_contract_values():
    with pytest.raises(ValidationError):
        ContextConfirmation(
            status="confirmed",
            impact_scopes=["workflow_routing"],
            review_status="applied",
            policy_effect="direct_policy_change",
        )


def test_default_non_interactive_decisions_record_missing_human_confirmation():
    decisions = default_non_interactive_decisions("/repo", context_paths=["/repo/team-rules.md"])

    assert decisions.mode == "non_interactive"
    assert decisions.repo.confirmed is False
    assert decisions.scan_confirmation.status == "not_confirmed"
    assert decisions.context_confirmation.status == "not_confirmed"
    assert decisions.context_confirmation.confirmed_paths == []
    assert decisions.context_confirmation.impact_scopes == []
    assert decisions.context_confirmation.review_status == "not_required"
    assert decisions.context_confirmation.policy_effect == "not_applicable"
    assert decisions.workflow_confirmation.impact_scopes == []
    assert decisions.workflow_confirmation.review_status == "not_required"
    assert decisions.workflow_confirmation.routing_policy_effect == "not_applicable"
    assert decisions.final_confirmation.status == "not_confirmed"


def test_accepted_interactive_decisions_records_context_impact_contract():
    decisions = accepted_interactive_decisions(
        "/repo",
        context_paths=["/repo/team-rules.md"],
        inline_contexts=["团队规则：Controller 只能调用 Service"],
    )

    assert decisions.context_confirmation.status == "confirmed"
    assert decisions.context_confirmation.confirmed_paths == ["/repo/team-rules.md"]
    assert decisions.context_confirmation.inline_contexts == ["团队规则：Controller 只能调用 Service"]
    assert decisions.context_confirmation.impact_scopes == [
        "interaction_decisions",
        "project_context",
        "human_input_needed",
        "guide_context",
        "review_only_team_context",
    ]
    assert decisions.context_confirmation.review_status == "pending_harness_maintainer_review"
    assert decisions.context_confirmation.policy_effect == "context_only_no_direct_policy_change"


def test_scan_confirmation_accepts_structured_supplement_contract():
    confirmation = ScanConfirmation(
        status="amended",
        primary_stack_override="node",
        notes=["frontend 还包含批处理入口"],
        modules=[{"path": "frontend", "kind": "frontend", "name": "frontend"}],
        commands=[
            CommandDefinition(
                id="frontend_test",
                command="npm test",
                type="test",
                gate="hard",
                source="frontend/package.json",
                confidence="high",
            )
        ],
        risk_areas=[{"path": "frontend/package.json", "reason": "前端依赖需要单独确认"}],
        impact_scopes=[
            "interaction_decisions",
            "project_inventory",
            "command_catalog",
            "project_context",
            "sensors",
            "workflow_routing_review",
            "human_input_needed",
            "maturity_preview",
        ],
        review_status="pending_harness_maintainer_review",
        fact_effect="user_supplied_correction_review_required",
    )

    payload = confirmation.model_dump(mode="json")

    assert payload["modules"] == [{"path": "frontend", "kind": "frontend", "name": "frontend"}]
    assert payload["commands"][0]["id"] == "frontend_test"
    assert payload["commands"][0]["source"] == "frontend/package.json"
    assert payload["risk_areas"] == [{"path": "frontend/package.json", "reason": "前端依赖需要单独确认"}]
    assert payload["review_status"] == "pending_harness_maintainer_review"
    assert payload["fact_effect"] == "user_supplied_correction_review_required"


def test_scan_confirmation_rejects_invalid_structured_contract_values():
    with pytest.raises(ValidationError):
        ScanConfirmation(
            status="amended",
            impact_scopes=["formal_policy"],
            review_status="applied",
            fact_effect="verified_fact",
        )


def test_accepted_interactive_decisions_records_structured_scan_supplement_contract():
    decisions = accepted_interactive_decisions(
        "/repo",
        scan_notes=["frontend 还包含批处理入口"],
        primary_stack_override="node",
        scan_modules=[{"path": "frontend", "kind": "frontend", "name": "frontend"}],
        scan_commands=[
            CommandDefinition(
                id="frontend_test",
                command="npm test",
                type="test",
                gate="hard",
                source="frontend/package.json",
                confidence="high",
            )
        ],
        scan_risk_areas=[{"path": "frontend/package.json", "reason": "前端依赖需要单独确认"}],
    )

    scan = decisions.scan_confirmation

    assert scan.status == "amended"
    assert scan.primary_stack_override == "node"
    assert scan.modules == [{"path": "frontend", "kind": "frontend", "name": "frontend"}]
    assert scan.commands[0].id == "frontend_test"
    assert scan.risk_areas == [{"path": "frontend/package.json", "reason": "前端依赖需要单独确认"}]
    assert scan.impact_scopes == [
        "interaction_decisions",
        "project_context",
        "human_input_needed",
        "maturity_preview",
        "project_inventory",
        "command_catalog",
        "sensors",
        "workflow_routing_review",
    ]
    assert scan.review_status == "pending_harness_maintainer_review"
    assert scan.fact_effect == "user_supplied_correction_review_required"


def test_accepted_interactive_decisions_without_scan_supplement_has_no_scan_impact_contract():
    decisions = accepted_interactive_decisions("/repo")

    assert decisions.scan_confirmation.status == "accepted"
    assert decisions.scan_confirmation.modules == []
    assert decisions.scan_confirmation.commands == []
    assert decisions.scan_confirmation.risk_areas == []
    assert decisions.scan_confirmation.impact_scopes == []
    assert decisions.scan_confirmation.review_status == "not_required"
    assert decisions.scan_confirmation.fact_effect == "not_applicable"


def test_accepted_interactive_decisions_without_context_has_no_context_impact_contract():
    decisions = accepted_interactive_decisions("/repo")

    assert decisions.context_confirmation.status == "not_provided"
    assert decisions.context_confirmation.impact_scopes == []
    assert decisions.context_confirmation.review_status == "not_required"
    assert decisions.context_confirmation.policy_effect == "not_applicable"


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
        scan_confirmation=ScanConfirmation(
            status="amended",
            notes=["frontend 还包含批处理入口"],
            modules=[{"path": "frontend", "kind": "frontend", "name": "frontend"}],
            commands=[
                CommandDefinition(
                    id="frontend_test",
                    command="npm test",
                    type="test",
                    gate="hard",
                    source="frontend/package.json",
                    confidence="high",
                )
            ],
            risk_areas=[{"path": "frontend/package.json", "reason": "前端依赖需要单独确认"}],
            impact_scopes=[
                "interaction_decisions",
                "project_inventory",
                "command_catalog",
                "project_context",
                "sensors",
                "workflow_routing_review",
                "human_input_needed",
                "maturity_preview",
            ],
            review_status="pending_harness_maintainer_review",
            fact_effect="user_supplied_correction_review_required",
        ),
        context_confirmation=ContextConfirmation(
            status="confirmed",
            inline_contexts=["团队测试策略"],
            impact_scopes=[
                "interaction_decisions",
                "project_context",
                "human_input_needed",
                "guide_context",
                "review_only_team_context",
            ],
            review_status="pending_harness_maintainer_review",
            policy_effect="context_only_no_direct_policy_change",
        ),
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
    assert "scan: amended" in markdown
    assert "scan_impact_scopes: interaction_decisions, project_inventory, command_catalog, project_context, sensors, workflow_routing_review, human_input_needed, maturity_preview" in markdown
    assert "scan_review_status: pending_harness_maintainer_review" in markdown
    assert "scan_fact_effect: user_supplied_correction_review_required" in markdown
    assert "`frontend` (frontend, frontend)" in markdown
    assert "`frontend_test`: npm test (test, hard, source=frontend/package.json, confidence=high)" in markdown
    assert "`frontend/package.json`: 前端依赖需要单独确认" in markdown
    assert "团队测试策略" in markdown
    assert "context_impact_scopes: interaction_decisions, project_context, human_input_needed, guide_context, review_only_team_context" in markdown
    assert "context_review_status: pending_harness_maintainer_review" in markdown
    assert "context_policy_effect: context_only_no_direct_policy_change" in markdown
    assert "workflow_confirmed: True" in markdown
    assert "workflow_impact_scopes: interaction_decisions, project_context, human_input_needed, review_only_workflow_note" in markdown
    assert "workflow_review_status: pending_harness_maintainer_review" in markdown
    assert "workflow_routing_policy_effect: review_only_no_direct_policy_change" in markdown
    assert "缺陷修复需要先定位原因" in markdown
