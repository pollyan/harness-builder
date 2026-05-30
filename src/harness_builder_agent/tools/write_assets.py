from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.asset_writers.core import llm_scan_proposal, scan_metadata, write_core_assets
from harness_builder_agent.tools.asset_writers.guides import write_guide_assets
from harness_builder_agent.tools.asset_writers.human_confirmation import write_human_confirmation_assets
from harness_builder_agent.tools.asset_writers.reports import write_report_assets
from harness_builder_agent.tools.asset_writers.sensors import write_sensor_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.human_confirmation import build_questionnaire, read_context_inputs
from harness_builder_agent.tools.llm_enhancement_candidates import (
    build_llm_enhancement_candidates,
    candidate_guides_markdown,
    candidate_sensors_markdown,
    enhancement_summary_markdown,
)
from harness_builder_agent.tools.weapon_library import select_weapon_library


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def write_initial_assets(
    repo: Path,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    trace: GenerationTrace | None = None,
    context_paths: list[Path] | None = None,
) -> Path:
    ai = repo / ".ai"
    config = HarnessConfig.default()
    weapon_selection = select_weapon_library(inventory, commands)
    scan_metadata_payload = scan_metadata(inventory)
    llm_scan_proposal_payload = llm_scan_proposal(inventory)
    context_inputs = read_context_inputs(context_paths or [])
    questionnaire = build_questionnaire(context_inputs, scan_metadata_payload)
    enhancement_candidates = build_llm_enhancement_candidates(inventory, commands)
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
    write_human_confirmation_assets(ai, context_inputs, questionnaire, trace=trace)
    if trace:
        trace.event(
            "human-confirmation",
            "completed",
            "Human confirmation assets generated.",
            {"context_count": len(context_inputs["contexts"]), "question_count": len(questionnaire["questions"])},
        )

    write_report_assets(ai, inventory, commands, config, weapon_selection, trace=trace)

    write_guide_assets(ai, inventory, weapon_selection, trace=trace)

    write_sensor_assets(ai, commands, weapon_selection, trace=trace)
    _copy_workflow_skills(ai)
    _record_artifact(trace, ai / "skills" / "lightweight" / "SKILL.md", "skill")
    _record_artifact(trace, ai / "skills" / "bugfix" / "SKILL.md", "skill")
    _write_text(ai / "experience" / "pending-improvements.md", "# Pending Improvements\n\nNo reviewed improvements yet.\n")
    _record_artifact(trace, ai / "experience" / "pending-improvements.md", "experience")
    _write_yaml(ai / "experience" / "weapon-library-candidates.yaml", enhancement_candidates)
    _record_artifact(trace, ai / "experience" / "weapon-library-candidates.yaml", "weapon_library_candidates")
    _write_text(ai / "review" / "llm-enhancement-candidates.md", enhancement_summary_markdown(enhancement_candidates))
    _record_artifact(trace, ai / "review" / "llm-enhancement-candidates.md", "review")
    _write_text(ai / "review" / "candidate-guides.md", candidate_guides_markdown(enhancement_candidates))
    _record_artifact(trace, ai / "review" / "candidate-guides.md", "review")
    _write_text(ai / "review" / "candidate-sensors.md", candidate_sensors_markdown(enhancement_candidates))
    _record_artifact(trace, ai / "review" / "candidate-sensors.md", "review")
    if trace:
        trace.event("asset-write", "completed", "Initial harness asset writing completed.", {"artifact_count": len(trace.artifacts)})
    return ai


def _record_artifact(trace: GenerationTrace | None, path: Path, kind: str) -> None:
    if trace:
        trace.artifact(path, kind)


def _copy_workflow_skills(ai: Path) -> None:
    template_root = files("harness_builder_agent").joinpath("templates", "skills")
    for name in ("lightweight", "bugfix"):
        content = template_root.joinpath(name, "SKILL.md").read_text(encoding="utf-8")
        _write_text(ai / "skills" / name / "SKILL.md", content)
