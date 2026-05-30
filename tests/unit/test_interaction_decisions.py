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
            CandidateDecision(candidate_id="llm-guide-risk-001", decision="accepted", notes="团队认可")
        ],
        final_confirmation=FinalConfirmation(status="confirmed"),
    )

    payload = decisions.model_dump(mode="json")

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "interactive"
    assert payload["repo"]["confirmed"] is True
    assert payload["candidate_decisions"][0]["decision"] == "accepted"


def test_interaction_decisions_schema_rejects_invalid_candidate_decision():
    with pytest.raises(ValidationError):
        CandidateDecision(candidate_id="candidate-1", decision="promote")
