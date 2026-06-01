from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest
import typer

from harness_builder_agent.tools.existing_harness_action_runner import run_existing_harness_action
from harness_builder_agent.tools.existing_harness_review_actions import review_human_input_default_interaction_id
from harness_builder_agent.tools.maintenance_triage import MaintenanceAction


@dataclass
class FakeTrace:
    events: list[tuple[str, str, str, dict | None]] = field(default_factory=list)
    finishes: list[tuple[str, dict | None]] = field(default_factory=list)

    def event(self, stage: str, event_type: str, message: str, details: dict | None = None) -> None:
        self.events.append((stage, event_type, message, details))

    def finish(self, status: str, summary: dict | None = None) -> None:
        self.finishes.append((status, summary))

    def artifact(self, path: Path, kind: str) -> None:
        raise AssertionError(f"unexpected artifact for control-flow test: {path} ({kind})")


def test_existing_harness_action_runner_handles_exit_reinit_and_unknown(tmp_path: Path):
    repo = tmp_path / "repo"
    ai = repo / ".ai"
    ai.mkdir(parents=True)
    inventory = SimpleNamespace(primary_stack="java-spring")

    exit_trace = FakeTrace()
    assert run_existing_harness_action(repo, ai, inventory, "exit", exit_trace, []) == ai
    assert exit_trace.events[-1][1] == "completed"
    assert exit_trace.finishes[-1] == (
        "completed",
        {"primary_stack": "java-spring", "existing_harness_action": "exit"},
    )

    reinit_trace = FakeTrace()
    assert run_existing_harness_action(repo, ai, inventory, "reinit", reinit_trace, []) is None
    assert reinit_trace.events[-1][3] == {"primary_stack": "java-spring", "action": "reinit"}
    assert reinit_trace.finishes == []

    unknown_trace = FakeTrace()
    with pytest.raises(typer.Exit):
        run_existing_harness_action(repo, ai, inventory, "surprise", unknown_trace, [])
    assert unknown_trace.events[-1] == (
        "existing-harness",
        "failed",
        "Unknown existing Harness action.",
        {"primary_stack": "java-spring", "action": "surprise", "error": "unknown_existing_harness_action"},
    )
    assert unknown_trace.finishes[-1] == (
        "failed",
        {"primary_stack": "java-spring", "existing_harness_action": "surprise", "error": "unknown_existing_harness_action"},
    )


def test_existing_harness_action_runner_finds_human_input_default():
    actions = [
        MaintenanceAction(
            priority=20,
            action="review-candidate",
            reason="asset_candidates_pending",
            source=".ai/review/asset-candidates.yaml",
            next_action="review-candidate",
            count=1,
        ),
        MaintenanceAction(
            priority=25,
            action="review-human-input",
            reason="human_input_scan_followups_pending",
            source=".ai/questionnaire.yaml",
            next_action="review-human-input",
            count=1,
            detail="confirm:scan-followup:test-evidence",
        ),
    ]

    assert review_human_input_default_interaction_id(actions) == "confirm:scan-followup:test-evidence"
    assert review_human_input_default_interaction_id(actions[:1]) is None
