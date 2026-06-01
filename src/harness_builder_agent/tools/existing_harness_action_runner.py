from __future__ import annotations

from collections.abc import Callable
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


ExistingHarnessActionHandler = Callable[
    [Path, Path, ProjectInventory | Any, Any, list[MaintenanceAction]],
    Path | None,
]


def _run_exit_action(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
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


def _run_assess_handler(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    return run_assess_action(repo, inventory, trace)


def _run_improve_handler(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    return run_improve_action(repo, ai, inventory, trace)


def _run_benchmark_handler(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    return run_benchmark_action(repo, ai, inventory, trace)


def _run_recommend_workflow_handler(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    return run_recommend_workflow_action(repo, inventory, trace)


def _run_review_candidate_handler(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    return run_review_candidate_action(repo, ai, inventory, trace)


def _run_review_human_input_handler(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    return run_review_human_input_action(repo, inventory, trace, maintenance_actions)


def _run_review_initial_candidate_handler(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    return run_review_initial_candidate_action(repo, ai, inventory, trace)


def _run_self_improve_handler(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    return run_self_improve_action(repo, inventory, trace)


def _run_reinit_action(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    trace.event(
        "existing-harness",
        "completed",
        "Existing Harness detected; user chose to continue guided regeneration.",
        {"primary_stack": inventory.primary_stack, "action": "reinit"},
    )
    return None


EXISTING_HARNESS_ACTION_HANDLERS: dict[str, ExistingHarnessActionHandler] = {
    "exit": _run_exit_action,
    "assess": _run_assess_handler,
    "improve": _run_improve_handler,
    "benchmark": _run_benchmark_handler,
    "recommend-workflow": _run_recommend_workflow_handler,
    "review-candidate": _run_review_candidate_handler,
    "review-human-input": _run_review_human_input_handler,
    "self-improve": _run_self_improve_handler,
    "reinit": _run_reinit_action,
    "review-initial-candidate": _run_review_initial_candidate_handler,
}


def run_existing_harness_action(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    action: str,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    handler = EXISTING_HARNESS_ACTION_HANDLERS.get(action)
    if handler:
        return handler(repo, ai, inventory, trace, maintenance_actions)
    fail_existing_harness_action(
        trace,
        inventory,
        action,
        "Unknown existing Harness action.",
        "unknown_existing_harness_action",
    )
    return None
