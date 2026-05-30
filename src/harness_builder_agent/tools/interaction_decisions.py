from __future__ import annotations

from copy import deepcopy

from harness_builder_agent.schemas.interaction_decision import (
    CandidateDecision,
    ContextConfirmation,
    FinalConfirmation,
    InteractionDecisions,
    RepoConfirmation,
    ScanConfirmation,
)


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
) -> InteractionDecisions:
    confirmed_paths = context_paths or []
    inline_values = [item for item in (inline_contexts or []) if item.strip()]
    if confirmed_paths or inline_values:
        context_status = "confirmed"
    else:
        context_status = "not_provided"
    candidate_decisions = [
        CandidateDecision(candidate_id=candidate_id, decision="accepted" if accept_candidates else "kept")
        for candidate_id in (candidate_ids or [])
    ]
    return InteractionDecisions(
        mode="interactive",
        repo=RepoConfirmation(path=repo_path, confirmed=True),
        scan_confirmation=ScanConfirmation(status="accepted"),
        context_confirmation=ContextConfirmation(
            status=context_status,
            confirmed_paths=confirmed_paths,
            inline_contexts=inline_values,
        ),
        candidate_decisions=candidate_decisions,
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
    return (
        "# Interaction Decisions\n\n"
        f"- mode: {decisions.mode}\n"
        f"- repo_confirmed: {decisions.repo.confirmed}\n"
        f"- scan: {decisions.scan_confirmation.status}\n"
        f"- context: {decisions.context_confirmation.status}\n"
        f"- final: {decisions.final_confirmation.status}\n\n"
        "## Inline Context\n\n"
        + "\n".join(f"- {item}" for item in context_lines)
        + "\n\n## Candidate Decisions\n\n"
        + "\n".join(candidate_lines)
        + "\n"
    )
