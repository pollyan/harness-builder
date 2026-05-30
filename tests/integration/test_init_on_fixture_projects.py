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
from harness_builder_agent.tools.scan_repo import scan_repository

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _copy_fixture(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(FIXTURES / name, target)
    return target


def _fake_scan(repo: Path, expected_stack: str):
    if expected_stack == "java-spring":
        response = {
            "primary_stack": "java-spring",
            "stacks": ["java", "maven", "spring-boot"],
            "modules": [{"name": "app", "path": ".", "kind": "backend"}],
            "architecture_signals": [],
            "risk_areas": [],
            "command_candidates": [
                {"id": "unit_test", "command": "mvn test", "type": "test", "gate": "hard", "source": "pom.xml", "confidence": "high"}
            ],
            "configs": [],
            "ci_files": [],
            "confidence": "high",
            "needs_human_confirmation": False,
            "reasoning_summary": "Java Spring project.",
        }
    else:
        response = {
            "primary_stack": "dotnet-aspnet",
            "stacks": ["dotnet", "aspnet-core"],
            "modules": [{"name": "MiniApi", "path": "src", "kind": "backend"}],
            "architecture_signals": [],
            "risk_areas": [],
            "command_candidates": [
                {
                    "id": "unit_test",
                    "command": "dotnet test",
                    "type": "test",
                    "gate": "hard",
                    "source": "mini-dotnet-webapi.sln",
                    "confidence": "high",
                }
            ],
            "configs": [],
            "ci_files": [],
            "confidence": "high",
            "needs_human_confirmation": False,
            "reasoning_summary": ".NET ASP.NET project.",
        }
    return scan_repository(repo, llm_caller=lambda _messages: json.dumps(response))


def _assert_init_outputs(repo: Path, expected_stack: str, expected_context_text: str | None = None) -> None:
    ai = repo / ".ai"
    assert (ai / "project-inventory.json").exists()
    assert (ai / "command-catalog.yaml").exists()
    assert (ai / "harness-config.yaml").exists()
    assert (ai / "scan-metadata.yaml").exists()
    assert (ai / "llm-scan-proposal.json").exists()
    assert (ai / "weapon-library-selection.yaml").exists()
    assert (ai / "scan-report.md").exists()
    assert (ai / "maturity-report.md").exists()
    assert (ai / "maturity-score.yaml").exists()
    assert (ai / "evolution-plan.md").exists()
    assert (ai / "context-inputs.yaml").exists()
    assert (ai / "questionnaire.yaml").exists()
    assert (ai / "human-input-needed.md").exists()
    assert (ai / "review" / "llm-enhancement-candidates.md").exists()
    assert (ai / "review" / "candidate-guides.md").exists()
    assert (ai / "review" / "candidate-sensors.md").exists()
    assert (ai / "experience" / "weapon-library-candidates.yaml").exists()
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
    scan_metadata = yaml.safe_load((ai / "scan-metadata.yaml").read_text(encoding="utf-8"))
    assert scan_metadata["llm_status"] == "succeeded"
    llm_proposal = json.loads((ai / "llm-scan-proposal.json").read_text(encoding="utf-8"))
    assert llm_proposal["primary_stack"] == expected_stack

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

    questionnaire = yaml.safe_load((ai / "questionnaire.yaml").read_text(encoding="utf-8"))
    ids = {item["interaction_id"] for item in questionnaire["questions"]}
    assert "confirm:team-context" in ids
    assert "confirm:guide-candidates" in ids
    assert "confirm:sensor-gates" in ids
    human_input = (ai / "human-input-needed.md").read_text(encoding="utf-8")
    assert "# Human Input Needed" in human_input
    if expected_context_text:
        assert expected_context_text in human_input

    candidate_report = yaml.safe_load((ai / "experience" / "weapon-library-candidates.yaml").read_text(encoding="utf-8"))
    assert candidate_report["source"] == "llm_scan_proposal"
    assert candidate_report["candidates"]
    assert all(item["status"] == "candidate" for item in candidate_report["candidates"])
    assert all(item["human_confirmation_required"] is True for item in candidate_report["candidates"])

    runs = sorted((ai / "runs").iterdir())
    assert runs
    latest = runs[-1]
    trace = yaml.safe_load((latest / "trace.yaml").read_text(encoding="utf-8"))
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert {"scan", "weapon-selection", "asset-write"}.issubset(set(trace["stages"]))
    assert trace["summary"]["primary_stack"] == expected_stack

    artifacts = yaml.safe_load((latest / "artifacts.yaml").read_text(encoding="utf-8"))
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/project-inventory.json" in artifact_paths
    assert ".ai/llm-scan-proposal.json" in artifact_paths
    assert ".ai/guides/project-context.md" in artifact_paths
    assert ".ai/sensors/verification.md" in artifact_paths
    assert ".ai/skills/lightweight/SKILL.md" in artifact_paths


def test_init_generates_ai_assets_for_java_fixture(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    context = tmp_path / "team-rules.md"
    context.write_text("团队规则：Controller 只能调用 Service。", encoding="utf-8")
    monkeypatch.setattr("harness_builder_agent.cli.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--context", str(context)])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo, "java-spring", expected_context_text="团队规则")
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text())
    assert inventory["primary_stack"] == "java-spring"


def test_init_generates_ai_assets_for_dotnet_fixture(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-dotnet-webapi")
    monkeypatch.setattr("harness_builder_agent.cli.scan_repository", lambda repo_path: _fake_scan(repo_path, "dotnet-aspnet"))
    result = CliRunner().invoke(app, ["init", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo, "dotnet-aspnet")
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text())
    assert inventory["primary_stack"] == "dotnet-aspnet"


def test_init_defaults_to_current_working_directory(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.chdir(repo)
    monkeypatch.setattr("harness_builder_agent.cli.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(app, ["init"])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo, "java-spring")
