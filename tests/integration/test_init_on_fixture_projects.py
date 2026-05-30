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


def _assert_init_outputs(repo: Path, expected_stack: str) -> None:
    ai = repo / ".ai"
    assert (ai / "project-inventory.json").exists()
    assert (ai / "command-catalog.yaml").exists()
    assert (ai / "harness-config.yaml").exists()
    assert (ai / "weapon-library-selection.yaml").exists()
    assert (ai / "scan-report.md").exists()
    assert (ai / "maturity-report.md").exists()
    assert (ai / "maturity-score.yaml").exists()
    assert (ai / "evolution-plan.md").exists()
    assert (ai / "guides" / "project-context.md").exists()
    assert (ai / "guides" / "coding-rules.md").exists()
    assert (ai / "guides" / "architecture.md").exists()
    assert (ai / "guides" / "task-templates" / "bugfix.md").exists()
    assert (ai / "guides" / "task-templates" / "lightweight-feature.md").exists()
    assert (ai / "sensors" / "verification.md").exists()
    assert (ai / "sensors" / "test-strategy.md").exists()
    assert (ai / "skills" / "lightweight" / "SKILL.md").exists()
    assert (ai / "skills" / "bugfix" / "SKILL.md").exists()

    ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text())
    CommandCatalog.model_validate(yaml.safe_load((ai / "command-catalog.yaml").read_text()))
    config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text()))
    assert config.workflows["lightweight"].skill_path == ".ai/skills/lightweight/SKILL.md"
    assert config.workflows["bugfix"].skill_path == ".ai/skills/bugfix/SKILL.md"

    weapon_selection = yaml.safe_load((ai / "weapon-library-selection.yaml").read_text(encoding="utf-8"))
    assert weapon_selection["schema_version"] == "1.0"
    assert weapon_selection["source"] == "built_in_weapon_library"
    assert weapon_selection["primary_stack"] == expected_stack
    assert "common" in weapon_selection["selected_stacks"]
    assert expected_stack in weapon_selection["selected_stacks"]
    assert any(weapon_id.startswith("common.guide.") for weapon_id in weapon_selection["guide_weapon_ids"])
    assert any(weapon_id.startswith(f"{expected_stack}.guide.") for weapon_id in weapon_selection["guide_weapon_ids"])
    assert any(weapon_id.startswith("common.sensor.") for weapon_id in weapon_selection["sensor_weapon_ids"])
    assert any(weapon_id.startswith(f"{expected_stack}.sensor.") for weapon_id in weapon_selection["sensor_weapon_ids"])

    project_context = (ai / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "## 武器库匹配结果" in project_context
    assert "common.guide." in project_context
    assert f"{expected_stack}.guide." in project_context
    assert "## 当前项目事实" in project_context
    assert "## Harness Builder 推荐补齐项" in project_context
    assert "## 人工确认点" in project_context

    verification = (ai / "sensors" / "verification.md").read_text(encoding="utf-8")
    assert "## 武器库匹配结果" in verification
    assert "common.sensor." in verification
    assert f"{expected_stack}.sensor." in verification
    assert "## 已发现的验证命令" in verification
    assert "## 缺失验证能力" in verification
    assert "## 推荐验证活动" in verification
    assert "## 失败处理策略" in verification

    lightweight_skill = (ai / "skills" / "lightweight" / "SKILL.md").read_text(encoding="utf-8")
    bugfix_skill = (ai / "skills" / "bugfix" / "SKILL.md").read_text(encoding="utf-8")
    assert "轻量级开发工作流" in lightweight_skill
    assert "缺陷修复工作流" in bugfix_skill


def test_init_generates_ai_assets_for_java_fixture(tmp_path: Path):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    result = CliRunner().invoke(app, ["init", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo, "java-spring")
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text())
    assert inventory["primary_stack"] == "java-spring"


def test_init_generates_ai_assets_for_dotnet_fixture(tmp_path: Path):
    repo = _copy_fixture(tmp_path, "mini-dotnet-webapi")
    result = CliRunner().invoke(app, ["init", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo, "dotnet-aspnet")
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text())
    assert inventory["primary_stack"] == "dotnet-aspnet"
