from __future__ import annotations

import json
import re
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
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _copy_fixture(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(FIXTURES / name, target)
    return target


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def _fake_scan(repo: Path, expected_stack: str):
    if expected_stack == "java-spring":
        response = {
            "primary_stack": "java-spring",
            "stacks": ["java", "maven", "spring-boot"],
            "modules": [{"name": "app", "path": ".", "kind": "backend"}],
            "architecture_signals": ["Controller 层应保持轻量，业务逻辑进入 Service。"],
            "risk_areas": [{"path": "src/main/resources/application.yml", "reason": "配置变更会影响运行环境。"}],
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
            "architecture_signals": ["Controller 和 service 边界需要维护。"],
            "risk_areas": [{"path": "src/appsettings.json", "reason": "配置变更需要环境确认。"}],
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
    assert (ai / "interaction-decisions.yaml").exists()
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
    assert (ai / "skills" / "standard" / "SKILL.md").exists()

    ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text())
    CommandCatalog.model_validate(yaml.safe_load((ai / "command-catalog.yaml").read_text()))
    config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text()))
    assert config.workflows["lightweight"].skill_path == ".ai/skills/lightweight/SKILL.md"
    assert config.workflows["bugfix"].skill_path == ".ai/skills/bugfix/SKILL.md"
    assert config.workflows["standard"].skill_path == ".ai/skills/standard/SKILL.md"
    routing_rule_ids = {rule.id for rule in config.workflow_routing.rules}
    assert config.workflow_routing.default_workflow == "lightweight"
    assert {"bugfix-intent", "low-risk-lightweight", "standard-escalation"}.issubset(routing_rule_ids)
    standard_routing_rule = next(rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation")
    assert standard_routing_rule.selected_workflow == "standard"
    assert standard_routing_rule.human_confirmation_required is True
    assert "security_or_permission" in standard_routing_rule.triggers
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
    standard_skill = (ai / "skills" / "standard" / "SKILL.md").read_text(encoding="utf-8")
    assert "轻量级开发工作流" in lightweight_skill
    assert "缺陷修复工作流" in bugfix_skill
    assert "标准开发工作流" in standard_skill
    assert "Requirement Alignment" in standard_skill

    questionnaire = yaml.safe_load((ai / "questionnaire.yaml").read_text(encoding="utf-8"))
    ids = {item["interaction_id"] for item in questionnaire["questions"]}
    assert "confirm:team-context" in ids
    assert "confirm:guide-candidates" in ids
    assert "confirm:sensor-gates" in ids
    interaction_decisions = yaml.safe_load((ai / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert interaction_decisions["schema_version"] == "1.0"
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
    assert ".ai/interaction-decisions.yaml" in artifact_paths
    assert ".ai/guides/project-context.md" in artifact_paths
    assert ".ai/sensors/verification.md" in artifact_paths
    assert ".ai/skills/lightweight/SKILL.md" in artifact_paths
    assert ".ai/skills/standard/SKILL.md" in artifact_paths
    decision_log = (latest / "decision-log.md").read_text(encoding="utf-8")
    assert "Interaction Decisions" in decision_log


def test_init_generates_ai_assets_for_java_fixture(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    context = tmp_path / "team-rules.md"
    context.write_text("团队规则：Controller 只能调用 Service。", encoding="utf-8")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--context", str(context), "--non-interactive"])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo, "java-spring", expected_context_text="团队规则")
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "## 团队上下文" in project_context
    assert "Controller 只能调用 Service" in project_context
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text())
    assert inventory["primary_stack"] == "java-spring"


def test_init_generates_ai_assets_for_dotnet_fixture(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-dotnet-webapi")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "dotnet-aspnet"))
    result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo, "dotnet-aspnet")
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text())
    assert inventory["primary_stack"] == "dotnet-aspnet"


def test_init_defaults_to_current_working_directory(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.chdir(repo)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(app, ["init", "--non-interactive"])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo, "java-spring")


def test_init_non_tty_requires_explicit_non_interactive(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    shutil.rmtree(repo / ".ai", ignore_errors=True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="")

    assert result.exit_code != 0
    assert "non-interactive" in _strip_ansi(result.output)
    assert not (repo / ".ai" / "project-inventory.json").exists()


def test_init_non_interactive_generates_existing_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])

    assert result.exit_code == 0, result.output
    _assert_init_outputs(repo, "java-spring")
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["mode"] == "non_interactive"
    assert decisions["final_confirmation"]["status"] == "not_confirmed"


def test_init_default_guided_mode_accepts_happy_path(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="\n\n\n\n\n\n\nconfirm\n",
    )

    assert result.exit_code == 0, result.output
    assert "扫描发现" in result.output
    assert "主要技术栈" in result.output
    assert "团队规则" in result.output
    assert "建议生成的规则" in result.output
    assert "建议生成的传感器" in result.output
    assert "推荐工作流" in result.output
    assert "最终确认" in result.output
    assert "primary_stack" not in result.output
    _assert_init_outputs(repo, "java-spring")
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["mode"] == "interactive"
    assert decisions["repo"]["confirmed"] is True
    assert decisions["scan_confirmation"]["status"] == "accepted"
    assert decisions["workflow_confirmation"]["shown_workflows"] == ["lightweight", "bugfix"]
    assert decisions["workflow_confirmation"]["confirmed"] is True
    assert decisions["final_confirmation"]["status"] == "confirmed"


def test_guided_init_records_scan_notes_and_team_rules_in_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n"
            "模块 app 实际包含批处理入口，修改任务需要额外说明。\n"
            "团队规则：Controller 只能调用 Service，配置变更必须说明回滚方式。\n"
            "\n\n\n"
            "bugfix 工作流适合缺陷修复。\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["scan_confirmation"]["status"] == "amended"
    assert "批处理入口" in decisions["scan_confirmation"]["notes"][0]
    assert "Controller 只能调用 Service" in decisions["context_confirmation"]["inline_contexts"][0]
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "## 人工补充与修正" in project_context
    assert "批处理入口" in project_context
    assert "bugfix 工作流适合缺陷修复" in project_context


def test_guided_init_stack_correction_updates_inventory_and_decisions(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="\nstack=node\n\n\n\n\n\nconfirm\n",
    )

    assert result.exit_code == 0, result.output
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text(encoding="utf-8"))
    assert inventory["primary_stack"] == "node"
    assert inventory["stack_extensions"]["human_overrides"]["primary_stack"] == "node"
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["scan_confirmation"]["status"] == "amended"
    assert decisions["scan_confirmation"]["primary_stack_override"] == "node"


def test_guided_init_structured_scan_corrections_update_modules_commands_and_risks(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n"
            "module=frontend|frontend|frontend; command=frontend_test|npm test|test|hard|frontend/package.json|high; risk=frontend/package.json|前端依赖需要单独确认\n"
            "\n\n\n\n"
            "\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text(encoding="utf-8"))
    assert {"name": "frontend", "path": "frontend", "kind": "frontend"} in inventory["modules"]
    assert {"path": "frontend/package.json", "reason": "前端依赖需要单独确认"} in inventory["stack_extensions"]["risk_areas"]
    assert inventory["stack_extensions"]["human_overrides"]["modules"][0]["path"] == "frontend"
    assert inventory["stack_extensions"]["human_overrides"]["risk_areas"][0]["path"] == "frontend/package.json"
    catalog = yaml.safe_load((repo / ".ai" / "command-catalog.yaml").read_text(encoding="utf-8"))
    assert any(command["id"] == "frontend_test" and command["command"] == "npm test" for command in catalog["commands"])
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "frontend" in project_context
    assert "npm test" in project_context


def test_guided_init_reviews_candidates_one_by_one(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n\n\n"
            "a\n"
            "r\n"
            "e\n测试命令需要先确认 CI 稳定性。\n"
            "\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "llm-guide-architecture-001" in result.output
    assert "llm-guide-risk-001" in result.output
    assert "llm-sensor-command-001" in result.output
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    by_id = {item["candidate_id"]: item for item in decisions["candidate_decisions"]}
    assert by_id["llm-guide-architecture-001"]["decision"] == "accepted"
    assert by_id["llm-guide-risk-001"]["decision"] == "rejected"
    assert by_id["llm-sensor-command-001"]["decision"] == "edited"
    candidate_report = yaml.safe_load((repo / ".ai" / "experience" / "weapon-library-candidates.yaml").read_text(encoding="utf-8"))
    candidate_by_id = {item["id"]: item for item in candidate_report["candidates"]}
    assert candidate_by_id["llm-guide-architecture-001"]["status"] == "confirmed"
    assert candidate_by_id["llm-guide-risk-001"]["status"] == "rejected"
    assert candidate_by_id["llm-sensor-command-001"]["decision_notes"] == "测试命令需要先确认 CI 稳定性。"


def test_guided_init_final_summary_can_go_back_to_team_rules(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n\n"
            "初始规则需要修改。\n"
            "\n\n\n"
            "\n"
            "back\n"
            "rules\n"
            "最终团队规则：配置变更必须说明影响环境。\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "返回修改" in result.output
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["context_confirmation"]["inline_contexts"] == ["最终团队规则：配置变更必须说明影响环境。"]
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "最终团队规则" in project_context
    assert "初始规则需要修改" not in project_context
