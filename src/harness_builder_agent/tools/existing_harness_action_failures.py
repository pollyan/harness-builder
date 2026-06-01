from __future__ import annotations

from typing import Any

import typer

from harness_builder_agent.schemas.project_inventory import ProjectInventory


def fail_existing_harness_action(
    trace,
    inventory: ProjectInventory | Any,
    action: str,
    message: str,
    error: str,
    details: dict[str, Any] | None = None,
) -> None:
    event_details = {"primary_stack": inventory.primary_stack, "action": action, "error": error}
    if details:
        event_details.update(details)
    trace.event("existing-harness", "failed", message, event_details)
    summary = {
        "primary_stack": inventory.primary_stack,
        "existing_harness_action": action,
        "error": error,
    }
    if details:
        summary.update(details)
    trace.finish("failed", summary)
    typer.echo(f"{action} 失败：{error}")
    raise typer.Exit(code=1)
