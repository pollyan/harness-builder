from __future__ import annotations

from typing import Any

from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory


def build_harness_config(inventory: ProjectInventory) -> HarnessConfig:
    config = HarnessConfig.default()
    standard = next((rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation"), None)
    if standard is None:
        return config

    rationale_notes: list[str] = []
    for risk in risk_areas_from_inventory(inventory)[:5]:
        path = str(risk.get("path") or risk.get("area") or "").strip()
        if not path:
            continue
        reason = str(risk.get("reason") or risk.get("summary") or "需要人工确认。").strip()
        trigger = f"risk_area:{path}"
        if trigger not in standard.triggers:
            standard.triggers.append(trigger)
        rationale_notes.append(f"Scanned risk area `{path}` requires standard workflow review: {reason}")

    if rationale_notes:
        standard.rationale = standard.rationale.rstrip(".") + ". " + " ".join(rationale_notes)
    return config


def risk_areas_from_inventory(inventory: ProjectInventory) -> list[dict[str, Any]]:
    risk_areas = inventory.stack_extensions.get("risk_areas", [])
    if isinstance(risk_areas, list) and risk_areas:
        return [item for item in risk_areas if isinstance(item, dict)]
    proposal = inventory.stack_extensions.get("llm_scan_proposal", {})
    if isinstance(proposal, dict):
        proposal_risks = proposal.get("risk_areas", [])
        if isinstance(proposal_risks, list):
            return [item for item in proposal_risks if isinstance(item, dict)]
    return []
