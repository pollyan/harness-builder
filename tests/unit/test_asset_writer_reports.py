from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.reports import write_report_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace


def _inventory(repo: Path) -> ProjectInventory:
    return ProjectInventory(
        repo_name=repo.name,
        root_path=str(repo),
        primary_stack="java-spring",
        stacks=["java", "maven", "spring-boot"],
        modules=[{"name": "app", "path": ".", "kind": "backend"}],
        evidence=[{"path": "pom.xml", "reason": "maven build file"}],
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


def test_write_report_assets_writes_reports_scores_plan_and_records_trace(tmp_path: Path):
    ai = tmp_path / ".ai"
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    write_report_assets(ai, _inventory(tmp_path), _commands(), HarnessConfig.default(), _weapon_selection(), trace=trace)
    trace.finish("completed", {"primary_stack": "java-spring"})

    assert (ai / "scan-report.md").exists()
    assert (ai / "maturity-report.md").exists()
    assert (ai / "maturity-score.yaml").exists()
    assert (ai / "evolution-plan.md").exists()
    assert "## 证据" in (ai / "maturity-report.md").read_text(encoding="utf-8")
    assert yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8"))["schema_version"] == "1.0"

    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    assert {"path": ".ai/scan-report.md", "kind": "report"} in artifacts["artifacts"]
    assert {"path": ".ai/maturity-report.md", "kind": "report"} in artifacts["artifacts"]
    assert {"path": ".ai/maturity-score.yaml", "kind": "maturity_score"} in artifacts["artifacts"]
    assert {"path": ".ai/evolution-plan.md", "kind": "plan"} in artifacts["artifacts"]
