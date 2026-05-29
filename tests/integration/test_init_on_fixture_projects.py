from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app
from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _copy_fixture(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(FIXTURES / name, target)
    return target


def _assert_init_outputs(repo: Path) -> None:
    ai = repo / ".ai"
    assert (ai / "project-inventory.json").exists()
    assert (ai / "command-catalog.yaml").exists()
    assert (ai / "harness-config.yaml").exists()
    assert (ai / "scan-report.md").exists()
    assert (ai / "maturity-report.md").exists()
    assert (ai / "evolution-plan.md").exists()
    assert (ai / "guides" / "project-context.md").exists()
    assert (ai / "guides" / "coding-rules.md").exists()
    assert (ai / "guides" / "architecture.md").exists()
    assert (ai / "guides" / "task-templates" / "bugfix.md").exists()
    assert (ai / "guides" / "task-templates" / "lightweight-feature.md").exists()
    assert (ai / "sensors" / "verification.md").exists()
    assert (ai / "sensors" / "test-strategy.md").exists()

    ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text())
    CommandCatalog.model_validate(yaml.safe_load((ai / "command-catalog.yaml").read_text()))
    HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text()))


def test_init_generates_ai_assets_for_java_fixture(tmp_path: Path):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    result = CliRunner().invoke(app, ["init", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo)
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text())
    assert inventory["primary_stack"] == "java-spring"


def test_init_generates_ai_assets_for_dotnet_fixture(tmp_path: Path):
    repo = _copy_fixture(tmp_path, "mini-dotnet-webapi")
    result = CliRunner().invoke(app, ["init", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo)
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text())
    assert inventory["primary_stack"] == "dotnet-aspnet"
