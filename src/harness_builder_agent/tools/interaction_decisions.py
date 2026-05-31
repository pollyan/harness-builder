from __future__ import annotations

from copy import deepcopy

from harness_builder_agent.schemas.interaction_decision import (
    CandidateDecision,
    ContextConfirmation,
    FinalConfirmation,
    InteractionDecisions,
    RepoConfirmation,
    ScanConfirmation,
    WorkflowConfirmation,
)

CONTEXT_IMPACT_SCOPES = [
    "interaction_decisions",
    "project_context",
    "human_input_needed",
    "guide_context",
    "review_only_team_context",
]


def default_non_interactive_decisions(repo_path: str, context_paths: list[str] | None = None) -> InteractionDecisions:
    status = "not_confirmed" if context_paths else "not_provided"
    return InteractionDecisions(
        mode="non_interactive",
        repo=RepoConfirmation(path=repo_path, confirmed=False),
        scan_confirmation=ScanConfirmation(status="not_confirmed"),
        context_confirmation=ContextConfirmation(status=status),
        candidate_decisions=[],
        final_confirmation=FinalConfirmation(status="not_confirmed"),
    )


def accepted_interactive_decisions(
    repo_path: str,
    *,
    context_paths: list[str] | None = None,
    inline_contexts: list[str] | None = None,
    candidate_ids: list[str] | None = None,
    accept_candidates: bool = False,
    scan_notes: list[str] | None = None,
    primary_stack_override: str | None = None,
    candidate_decisions: list[CandidateDecision] | None = None,
    workflow_confirmation: WorkflowConfirmation | None = None,
) -> InteractionDecisions:
    confirmed_paths = context_paths or []
    inline_values = [item for item in (inline_contexts or []) if item.strip()]
    if confirmed_paths or inline_values:
        context_status = "confirmed"
        context_impact_scopes = CONTEXT_IMPACT_SCOPES
        context_review_status = "pending_harness_maintainer_review"
        context_policy_effect = "context_only_no_direct_policy_change"
    else:
        context_status = "not_provided"
        context_impact_scopes = []
        context_review_status = "not_required"
        context_policy_effect = "not_applicable"
    decisions = candidate_decisions or [
        CandidateDecision(candidate_id=candidate_id, decision="accepted" if accept_candidates else "kept")
        for candidate_id in (candidate_ids or [])
    ]
    scan_status = "amended" if (scan_notes or primary_stack_override) else "accepted"
    return InteractionDecisions(
        mode="interactive",
        repo=RepoConfirmation(path=repo_path, confirmed=True),
        scan_confirmation=ScanConfirmation(
            status=scan_status,
            primary_stack_override=primary_stack_override,
            notes=scan_notes or [],
        ),
        context_confirmation=ContextConfirmation(
            status=context_status,
            confirmed_paths=confirmed_paths,
            inline_contexts=inline_values,
            impact_scopes=context_impact_scopes,
            review_status=context_review_status,
            policy_effect=context_policy_effect,
        ),
        candidate_decisions=decisions,
        workflow_confirmation=workflow_confirmation or WorkflowConfirmation(),
        final_confirmation=FinalConfirmation(status="confirmed"),
    )


def apply_candidate_decisions(report: dict, decisions: InteractionDecisions) -> dict:
    updated = deepcopy(report)
    by_id = {item.candidate_id: item for item in decisions.candidate_decisions}
    for candidate in updated.get("candidates", []):
        decision = by_id.get(candidate.get("id"))
        if not decision:
            continue
        candidate["decision_notes"] = decision.notes
        if decision.decision == "accepted":
            candidate["status"] = "confirmed"
            candidate["human_confirmation_required"] = False
        elif decision.decision == "rejected":
            candidate["status"] = "rejected"
            candidate["human_confirmation_required"] = False
        elif decision.decision == "edited":
            candidate["status"] = "candidate"
            candidate["human_confirmation_required"] = True
        else:
            candidate["status"] = "candidate"
            candidate["human_confirmation_required"] = True
    return updated


def interaction_decisions_markdown(decisions: InteractionDecisions) -> str:
    context_lines = decisions.context_confirmation.inline_contexts or ["无"]
    candidate_lines = [
        f"- `{item.candidate_id}`: {item.decision} {item.notes}".rstrip()
        for item in decisions.candidate_decisions
    ] or ["- 无逐项 candidate 决策。"]
    scan_lines = decisions.scan_confirmation.notes or ["无"]
    workflow_lines = decisions.workflow_confirmation.notes or ["无"]
    return (
        "# Interaction Decisions\n\n"
        f"- mode: {decisions.mode}\n"
        f"- repo_confirmed: {decisions.repo.confirmed}\n"
        f"- scan: {decisions.scan_confirmation.status}\n"
        f"- primary_stack_override: {decisions.scan_confirmation.primary_stack_override or '无'}\n"
        f"- context: {decisions.context_confirmation.status}\n"
        f"- context_impact_scopes: {', '.join(decisions.context_confirmation.impact_scopes) or '无'}\n"
        f"- context_review_status: {decisions.context_confirmation.review_status}\n"
        f"- context_policy_effect: {decisions.context_confirmation.policy_effect}\n"
        f"- workflow_confirmed: {decisions.workflow_confirmation.confirmed}\n"
        f"- shown_workflows: {', '.join(decisions.workflow_confirmation.shown_workflows) or '无'}\n"
        f"- workflow_impact_scopes: {', '.join(decisions.workflow_confirmation.impact_scopes) or '无'}\n"
        f"- workflow_review_status: {decisions.workflow_confirmation.review_status}\n"
        f"- workflow_routing_policy_effect: {decisions.workflow_confirmation.routing_policy_effect}\n"
        f"- final: {decisions.final_confirmation.status}\n\n"
        "## Scan Supplements\n\n"
        + "\n".join(f"- {item}" for item in scan_lines)
        + "\n\n"
        "## Inline Context\n\n"
        + "\n".join(f"- {item}" for item in context_lines)
        + "\n\n## Workflow Notes\n\n"
        + "\n".join(f"- {item}" for item in workflow_lines)
        + "\n\n## Candidate Decisions\n\n"
        + "\n".join(candidate_lines)
        + "\n"
    )
