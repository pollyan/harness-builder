from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.interaction_decision import InteractionDecisions
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.asset_writers.candidates import write_candidate_assets
from harness_builder_agent.tools.asset_writers.core import llm_scan_proposal, scan_metadata, write_core_assets
from harness_builder_agent.tools.asset_writers.guides import write_guide_assets
from harness_builder_agent.tools.asset_writers.human_confirmation import write_human_confirmation_assets
from harness_builder_agent.tools.asset_writers.reports import write_report_assets
from harness_builder_agent.tools.asset_writers.sensors import write_sensor_assets
from harness_builder_agent.tools.asset_writers.skills import write_skill_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.human_confirmation import build_questionnaire, read_context_inputs
from harness_builder_agent.tools.interaction_decisions import apply_candidate_decisions, default_non_interactive_decisions
from harness_builder_agent.tools.llm_enhancement_candidates import build_llm_enhancement_candidates
from harness_builder_agent.tools.weapon_library import select_weapon_library


def write_initial_assets(
    repo: Path,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    trace: GenerationTrace | None = None,
    context_paths: list[Path] | None = None,
    interaction_decisions: InteractionDecisions | None = None,
) -> Path:
    ai = repo / ".ai"
    config = build_harness_config(inventory)
    weapon_selection = select_weapon_library(inventory, commands)
    scan_metadata_payload = scan_metadata(inventory)
    llm_scan_proposal_payload = llm_scan_proposal(inventory)
    context_inputs = read_context_inputs(context_paths or [])
    decisions = interaction_decisions or default_non_interactive_decisions(
        str(repo),
        context_paths=[str(path) for path in (context_paths or [])],
    )
    risk_areas = inventory.stack_extensions.get("risk_areas", [])
    questionnaire = build_questionnaire(context_inputs, scan_metadata_payload, risk_areas=risk_areas)
    raw_candidates = build_llm_enhancement_candidates(inventory, commands).model_dump(mode="json")
    enhancement_candidates = apply_candidate_decisions(raw_candidates, decisions)
    if trace:
        trace.event(
            "weapon-selection",
            "completed",
            "Weapon library selection completed.",
            {
                "source": weapon_selection.source,
                "selected_stacks": weapon_selection.selected_stacks,
                "guide_weapon_count": len(weapon_selection.guide_weapon_ids),
                "sensor_weapon_count": len(weapon_selection.sensor_weapon_ids),
            },
        )
        trace.event("asset-write", "started", "Initial harness asset writing started.")

    write_core_assets(
        ai,
        inventory,
        commands,
        config,
        scan_metadata_payload,
        llm_scan_proposal_payload,
        weapon_selection,
        trace=trace,
    )
    write_human_confirmation_assets(ai, context_inputs, questionnaire, trace=trace, interaction_decisions=decisions)
    if trace:
        trace.event(
            "human-confirmation",
            "completed",
            "Human confirmation assets generated.",
            {"context_count": len(context_inputs["contexts"]), "question_count": len(questionnaire["questions"])},
        )

    write_report_assets(ai, inventory, commands, config, weapon_selection, interaction_decisions=decisions, trace=trace)

    write_guide_assets(ai, inventory, commands, weapon_selection, context_inputs, decisions, trace=trace)

    write_sensor_assets(ai, commands, weapon_selection, inventory=inventory, trace=trace)
    write_skill_assets(ai, trace=trace)
    write_candidate_assets(ai, enhancement_candidates, trace=trace)
    if trace:
        trace.event("asset-write", "completed", "Initial harness asset writing completed.", {"artifact_count": len(trace.artifacts)})
    return ai


def build_harness_config(inventory: ProjectInventory) -> HarnessConfig:
    config = HarnessConfig.default()
    standard = next((rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation"), None)
    if standard is None:
        return config

    rationale_notes: list[str] = []
    for risk in _risk_areas(inventory)[:5]:
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


def _risk_areas(inventory: ProjectInventory) -> list[dict[str, Any]]:
    risk_areas = inventory.stack_extensions.get("risk_areas", [])
    if isinstance(risk_areas, list) and risk_areas:
        return [item for item in risk_areas if isinstance(item, dict)]
    proposal = inventory.stack_extensions.get("llm_scan_proposal", {})
    if isinstance(proposal, dict):
        proposal_risks = proposal.get("risk_areas", [])
        if isinstance(proposal_risks, list):
            return [item for item in proposal_risks if isinstance(item, dict)]
    return []
