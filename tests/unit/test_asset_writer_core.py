from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.core import llm_scan_proposal, scan_metadata, write_core_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace


def _inventory(repo: Path, stack_extensions: dict | None = None) -> ProjectInventory:
    return ProjectInventory(
        repo_name=repo.name,
        root_path=str(repo),
        primary_stack="java-spring",
        stacks=["java", "maven", "spring-boot"],
        modules=[{"name": "app", "path": ".", "kind": "backend"}],
        evidence=[{"path": "pom.xml", "reason": "maven build file"}],
        configs=[{"path": "src/main/resources/application.yml", "kind": "spring-config"}],
        ci_files=[{"path": ".github/workflows/ci.yml", "kind": "github-actions"}],
        stack_extensions=stack_extensions or {},
    )


def _commands() -> CommandCatalog:
    return CommandCatalog(
        commands=[CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml")]
    )


def _weapon_selection() -> WeaponLibrarySelection:
    return WeaponLibrarySelection(
        primary_stack="java-spring",
        selected_stacks=["common", "java-spring"],
        guide_weapon_ids=["java-spring.guide.layering"],
        sensor_weapon_ids=["common.sensor.tests"],
    )


def test_write_core_assets_writes_schema_files_and_records_trace(tmp_path: Path):
    inventory = _inventory(tmp_path)
    config = HarnessConfig.default()
    scan_payload = {"schema_version": "1.0", "llm_status": "succeeded", "prompt_version": "test", "warnings": []}
    proposal_payload = {
        "schema_version": "1.0",
        "primary_stack": "java-spring",
        "stacks": ["java", "maven"],
        "modules": [{"name": "app", "path": ".", "kind": "backend"}],
        "architecture_signals": [],
        "risk_areas": [],
        "command_candidates": [],
        "configs": [],
        "ci_files": [],
        "confidence": "high",
        "needs_human_confirmation": False,
        "reasoning_summary": "Maven project.",
    }
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    write_core_assets(
        tmp_path / ".ai",
        inventory,
        _commands(),
        config,
        scan_payload,
        proposal_payload,
        _weapon_selection(),
        trace=trace,
    )
    trace.finish("completed", {"primary_stack": "java-spring"})

    assert (tmp_path / ".ai" / "project-inventory.json").exists()
    assert yaml.safe_load((tmp_path / ".ai" / "command-catalog.yaml").read_text(encoding="utf-8"))["commands"][0][
        "command"
    ] == "mvn test"
    assert yaml.safe_load((tmp_path / ".ai" / "harness-config.yaml").read_text(encoding="utf-8"))["version"] == 1
    assert yaml.safe_load((tmp_path / ".ai" / "scan-metadata.yaml").read_text(encoding="utf-8")) == scan_payload
    assert (tmp_path / ".ai" / "llm-scan-proposal.json").exists()
    assert yaml.safe_load((tmp_path / ".ai" / "weapon-library-selection.yaml").read_text(encoding="utf-8"))[
        "primary_stack"
    ] == "java-spring"

    artifacts = yaml.safe_load((tmp_path / ".ai" / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text())
    assert {"path": ".ai/project-inventory.json", "kind": "inventory"} in artifacts["artifacts"]


def test_scan_metadata_uses_payload_from_stack_extensions(tmp_path: Path):
    payload = {
        "schema_version": "1.0",
        "llm_status": "succeeded",
        "prompt_version": "scan-v2",
        "evidence_file_count": 3,
        "warnings": ["low confidence"],
    }

    assert scan_metadata(_inventory(tmp_path, {"scan_metadata": payload})) == payload


def test_llm_scan_proposal_uses_payload_from_stack_extensions(tmp_path: Path):
    payload = {
        "schema_version": "1.0",
        "primary_stack": "java-spring",
        "stacks": ["java", "maven"],
        "modules": [{"name": "app", "path": ".", "kind": "backend"}],
        "architecture_signals": ["Controller layer is present"],
        "risk_areas": [{"path": "application.yml", "reason": "configuration risk"}],
        "command_candidates": [{"id": "unit_test", "command": "mvn test"}],
        "configs": [],
        "ci_files": [],
        "confidence": "high",
        "needs_human_confirmation": False,
        "reasoning_summary": "Maven project.",
    }

    assert llm_scan_proposal(_inventory(tmp_path, {"llm_scan_proposal": payload})) == payload


def test_scan_metadata_and_llm_scan_proposal_fallback_when_extensions_are_absent(tmp_path: Path):
    inventory = _inventory(tmp_path, {"detected_file_count": 7})

    assert scan_metadata(inventory) == {
        "schema_version": "1.0",
        "llm_status": "unknown",
        "prompt_version": "unknown",
        "evidence_file_count": 7,
        "warnings": [],
    }
    assert llm_scan_proposal(inventory) == {
        "schema_version": "1.0",
        "primary_stack": "java-spring",
        "stacks": ["java", "maven", "spring-boot"],
        "modules": [{"name": "app", "path": ".", "kind": "backend"}],
        "architecture_signals": [],
        "risk_areas": [],
        "command_candidates": [],
        "configs": [{"path": "src/main/resources/application.yml", "kind": "spring-config"}],
        "ci_files": [{"path": ".github/workflows/ci.yml", "kind": "github-actions"}],
        "confidence": "low",
        "needs_human_confirmation": True,
        "reasoning_summary": "Legacy scan metadata was not available.",
    }
