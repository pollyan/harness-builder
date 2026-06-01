from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.existing_harness_action_failures import fail_existing_harness_action
from harness_builder_agent.tools.existing_harness_deterministic_actions import (
    run_assess_action,
    run_benchmark_action,
    run_improve_action,
)
from harness_builder_agent.tools.existing_harness_intelligent_actions import (
    run_recommend_workflow_action,
    run_self_improve_action,
)
from harness_builder_agent.tools.existing_harness_review_actions import (
    run_review_candidate_action,
    run_review_human_input_action,
    run_review_initial_candidate_action,
)
from harness_builder_agent.tools.maintenance_triage import MaintenanceAction


def run_existing_harness_action(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    action: str,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    if action == "exit":
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness detected; user exited without rewriting formal assets.",
            {"primary_stack": inventory.primary_stack, "action": "exit"},
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "exit",
            },
        )
        return ai
    if action == "assess":
        return run_assess_action(repo, inventory, trace)
    if action == "improve":
        return run_improve_action(repo, ai, inventory, trace)
    if action == "benchmark":
        return run_benchmark_action(repo, ai, inventory, trace)
    if action == "recommend-workflow":
        return run_recommend_workflow_action(repo, inventory, trace)
    if action == "review-candidate":
        return run_review_candidate_action(repo, ai, inventory, trace)
    if action == "review-human-input":
        return run_review_human_input_action(repo, inventory, trace, maintenance_actions)
    if action == "review-initial-candidate":
        return run_review_initial_candidate_action(repo, ai, inventory, trace)
    if action == "self-improve":
        return run_self_improve_action(repo, inventory, trace)
    if action == "reinit":
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness detected; user chose to continue guided regeneration.",
            {"primary_stack": inventory.primary_stack, "action": "reinit"},
        )
        return None
    fail_existing_harness_action(
        trace,
        inventory,
        action,
        "Unknown existing Harness action.",
        "unknown_existing_harness_action",
    )
    return None
