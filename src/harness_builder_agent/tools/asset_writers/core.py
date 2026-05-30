from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_json, write_yaml
from harness_builder_agent.tools.generation_trace import GenerationTrace


def scan_metadata(inventory: ProjectInventory) -> dict[str, Any]:
    metadata = inventory.stack_extensions.get("scan_metadata")
    if isinstance(metadata, dict):
        return metadata
    return {
        "schema_version": "1.0",
        "llm_status": "unknown",
        "prompt_version": "unknown",
        "evidence_file_count": inventory.stack_extensions.get("detected_file_count", 0),
        "warnings": [],
    }


def llm_scan_proposal(inventory: ProjectInventory) -> dict[str, Any]:
    proposal = inventory.stack_extensions.get("llm_scan_proposal")
    if isinstance(proposal, dict):
        return proposal
    return {
        "schema_version": "1.0",
        "primary_stack": inventory.primary_stack,
        "stacks": inventory.stacks,
        "modules": inventory.modules,
        "architecture_signals": [],
        "risk_areas": [],
        "command_candidates": [],
        "configs": inventory.configs,
        "ci_files": inventory.ci_files,
        "confidence": "low",
        "needs_human_confirmation": True,
        "reasoning_summary": "Legacy scan metadata was not available.",
    }


def write_core_assets(
    ai: Path,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    config: HarnessConfig,
    scan_metadata_payload: dict[str, Any],
    llm_scan_proposal_payload: dict[str, Any],
    weapon_selection: WeaponLibrarySelection,
    trace: GenerationTrace | None = None,
) -> None:
    write_json(ai / "project-inventory.json", inventory.model_dump(mode="json"))
    record_artifact(trace, ai / "project-inventory.json", "inventory")
    write_yaml(ai / "command-catalog.yaml", commands.model_dump(mode="json"))
    record_artifact(trace, ai / "command-catalog.yaml", "command_catalog")
    write_yaml(ai / "harness-config.yaml", config.model_dump(mode="json"))
    record_artifact(trace, ai / "harness-config.yaml", "config")
    write_yaml(ai / "scan-metadata.yaml", scan_metadata_payload)
    record_artifact(trace, ai / "scan-metadata.yaml", "scan_metadata")
    write_json(ai / "llm-scan-proposal.json", llm_scan_proposal_payload)
    record_artifact(trace, ai / "llm-scan-proposal.json", "llm_scan_proposal")
    write_yaml(ai / "weapon-library-selection.yaml", weapon_selection.model_dump(mode="json"))
    record_artifact(trace, ai / "weapon-library-selection.yaml", "weapon_library_selection")
