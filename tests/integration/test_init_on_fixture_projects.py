from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app
from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceLog
from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools import interactive_init
from harness_builder_agent.tools.experience_index import write_experience_index
from harness_builder_agent.tools.scan_repo import scan_repository

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _copy_fixture(tmp_path: Path, name: str) -> Path:
    target = tmp_path / name
    shutil.copytree(FIXTURES / name, target, ignore=shutil.ignore_patterns(".ai"))
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
    assert (ai / "init-summary.md").exists()
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

    init_summary = (ai / "init-summary.md").read_text(encoding="utf-8")
    assert "# Init Summary" in init_summary
    assert "## 当前成熟度" in init_summary
    assert "## 主要阻断项" in init_summary
    assert "## 建议下一步" in init_summary
    assert "## Benchmark 健康度" in init_summary
    assert "benchmark_status=not_run" in init_summary
    assert "quality_status=not_available" in init_summary
    assert "harness-builder-agent benchmark --repo" in init_summary
    assert "not equivalent to benchmark passed" in init_summary
    assert "## 推荐入口文件" in init_summary
    assert "## 本次未执行的事项" in init_summary
    assert ".ai/maturity-report.md" in init_summary
    assert ".ai/human-input-needed.md" in init_summary
    assert ".ai/task-runs" in init_summary

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
    assert ".ai/init-summary.md" in artifact_paths
    assert ".ai/llm-scan-proposal.json" in artifact_paths
    assert ".ai/interaction-decisions.yaml" in artifact_paths
    assert ".ai/guides/project-context.md" in artifact_paths
    assert ".ai/sensors/verification.md" in artifact_paths
    assert ".ai/skills/lightweight/SKILL.md" in artifact_paths
    assert ".ai/skills/standard/SKILL.md" in artifact_paths
    decision_log = (latest / "decision-log.md").read_text(encoding="utf-8")
    assert "Interaction Decisions" in decision_log


def _latest_init_trace(repo: Path) -> dict:
    runs = sorted((repo / ".ai" / "runs").iterdir())
    assert runs
    return yaml.safe_load((runs[-1] / "trace.yaml").read_text(encoding="utf-8"))


def _latest_init_artifacts(repo: Path) -> dict:
    runs = sorted((repo / ".ai" / "runs").iterdir())
    assert runs
    return yaml.safe_load((runs[-1] / "artifacts.yaml").read_text(encoding="utf-8"))


def _formal_asset_snapshot(repo: Path) -> dict[str, str]:
    ai = repo / ".ai"
    paths = [
        ai / "project-inventory.json",
        ai / "command-catalog.yaml",
        ai / "harness-config.yaml",
        ai / "scan-metadata.yaml",
        ai / "llm-scan-proposal.json",
        ai / "weapon-library-selection.yaml",
        ai / "guides" / "project-context.md",
        ai / "guides" / "coding-rules.md",
        ai / "guides" / "architecture.md",
        ai / "guides" / "task-templates" / "bugfix.md",
        ai / "guides" / "task-templates" / "lightweight-feature.md",
        ai / "sensors" / "verification.md",
        ai / "sensors" / "test-strategy.md",
        ai / "skills" / "lightweight" / "SKILL.md",
        ai / "skills" / "bugfix" / "SKILL.md",
        ai / "skills" / "standard" / "SKILL.md",
    ]
    return {str(path.relative_to(repo)): path.read_text(encoding="utf-8") for path in paths}


def _assert_formal_assets_unchanged(repo: Path, snapshot: dict[str, str]) -> None:
    for relative_path, content in snapshot.items():
        assert (repo / relative_path).read_text(encoding="utf-8") == content


def test_init_generates_ai_assets_for_java_fixture(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    context = tmp_path / "team-rules.md"
    context.write_text("团队规则：Controller 只能调用 Service。", encoding="utf-8")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--context", str(context), "--non-interactive"])

    assert result.exit_code == 0, result.output
    assert "当前成熟度" in result.output
    assert "Benchmark 健康度" in result.output
    assert "benchmark_status=not_run" in result.output
    assert "quality_status=not_available" in result.output
    assert "harness-builder-agent benchmark --repo" in result.output
    assert ".ai/init-summary.md" in result.output
    assert ".ai/maturity-report.md" in result.output
    _assert_init_outputs(repo, "java-spring", expected_context_text="团队规则")
    assert not (repo / ".ai" / "benchmark-report.yaml").exists()
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
    assert "当前成熟度" in result.output
    assert ".ai/init-summary.md" in result.output
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
    assert "扫描仓库" in result.output
    assert "正在收集仓库文件、构建配置、CI、测试和文档证据" in result.output
    assert "正在请求 LLM 做结构化扫描" in result.output
    assert "正在调和 LLM 判断与 evidence" in result.output
    assert "扫描完成" in result.output
    assert result.output.index("扫描仓库") < result.output.index("扫描发现")
    assert result.output.index("扫描完成") < result.output.index("扫描发现")
    assert "扫描发现" in result.output
    assert "风险区域" in result.output
    assert "不确定性" in result.output
    assert "验证缺口" in result.output
    assert "建议补充" in result.output
    assert result.output.index("扫描发现") < result.output.index("\n风险区域")
    assert result.output.index("建议补充") < result.output.index("团队规则")
    assert "主要技术栈" in result.output
    assert "团队规则" in result.output
    assert "建议生成的规则" in result.output
    assert "建议生成的传感器" in result.output
    assert "推荐工作流" in result.output
    assert "当前 Harness 成熟度初评" in result.output
    assert "当前从 L0 起步" in result.output
    assert "确认写入后预计建立" in result.output
    assert "下一目标" in result.output
    assert "主要阻断项" in result.output
    assert "推荐补齐动作" in result.output
    assert "写入前 Harness 设计预览" in result.output
    assert "将生成的 Guides" in result.output
    assert "将生成的 Sensors" in result.output
    assert "Workflow routing" in result.output
    assert "standard-escalation" in result.output
    assert "高风险" in result.output
    assert "最终确认" in result.output
    assert result.output.index("当前 Harness 成熟度初评") < result.output.index("最终确认")
    assert "当前成熟度" in result.output
    assert ".ai/init-summary.md" in result.output
    assert "primary_stack" not in result.output
    assert "overall_level" not in result.output
    assert "dimension_scores" not in result.output
    _assert_init_outputs(repo, "java-spring")
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["mode"] == "interactive"
    assert decisions["repo"]["confirmed"] is True
    assert decisions["scan_confirmation"]["status"] == "accepted"
    assert decisions["workflow_confirmation"]["shown_workflows"] == ["lightweight", "bugfix"]
    assert decisions["workflow_confirmation"]["confirmed"] is True
    assert decisions["final_confirmation"]["status"] == "confirmed"


def test_guided_init_scan_failure_prints_progress_and_no_formal_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    messages: list[str] = []
    original_echo = interactive_init.typer.echo

    def record_echo(message="", *args, **kwargs):
        messages.append(str(message))
        return original_echo(message, *args, **kwargs)

    def fail_scan(repo_path: Path):
        assert any("扫描仓库" in message for message in messages)
        raise RuntimeError("synthetic scan failure")

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.typer.echo", record_echo)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="\n")
    output = _strip_ansi(result.output)

    assert result.exit_code != 0
    assert "扫描仓库" in output
    assert "扫描阶段失败" in output
    assert "未写入正式 Harness 资产" in output
    assert "请检查 LLM 配置、网络或扫描错误后重试" in output
    assert "synthetic scan failure" in output
    assert output.index("扫描仓库") < output.index("扫描阶段失败")
    assert not (repo / ".ai" / "project-inventory.json").exists()
    assert not (repo / ".ai" / "harness-config.yaml").exists()
    assert not (repo / ".ai" / "guides").exists()
    assert not (repo / ".ai" / "sensors").exists()
    assert not (repo / ".ai" / "skills").exists()


def test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)

    def scan_with_attention_points(repo_path: Path):
        inventory = ProjectInventory(
            repo_name=repo_path.name,
            root_path=str(repo_path),
            primary_stack="java-spring",
            stacks=["java", "spring-boot"],
            modules=[{"name": "app", "path": ".", "kind": "backend"}],
            evidence=[{"path": "pom.xml", "reason": "build config"}],
            stack_extensions={
                "risk_areas": [{"path": "src/main/resources/application.yml", "reason": "配置变更影响运行环境"}],
                "needs_human_confirmation": True,
                "scan_warnings": [
                    {
                        "code": "test_evidence_not_found",
                        "message": "No dedicated test evidence bucket was found; test strategy needs human confirmation.",
                        "severity": "warning",
                        "evidence": [],
                    }
                ],
                "llm_scan_proposal": {"confidence": "low"},
            },
        )
        commands = CommandCatalog(
            commands=[
                {
                    "id": "integration_test",
                    "command": "mvn -Pintegration test",
                    "type": "test",
                    "gate": "soft",
                    "source": "pom.xml",
                    "confidence": "low",
                }
            ]
        )
        return inventory, commands

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", scan_with_attention_points)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="\n\n\n\n\n\n\nconfirm\n",
    )

    assert result.exit_code == 0, result.output
    assert "风险区域" in result.output
    assert "src/main/resources/application.yml" in result.output
    assert "配置变更影响运行环境" in result.output
    assert "不确定性" in result.output
    assert "需要人工确认" in result.output
    assert "LLM 扫描置信度为 low" in result.output
    assert "No dedicated test evidence bucket was found" in result.output
    assert "mvn -Pintegration test" in result.output
    assert "验证缺口" in result.output
    assert "暂未确认 hard gate" in result.output
    assert "低置信度验证命令" in result.output
    assert "建议补充" in result.output
    assert "真实可执行的 hard gate 命令" in result.output
    assert result.output.index("\n风险区域") < result.output.index("团队规则")


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


def test_guided_init_restates_user_supplements_before_write_and_persists_them(tmp_path: Path, monkeypatch):
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
    final_summary = result.output[result.output.index("最终确认"):]
    assert "已吸收的用户补充" in final_summary
    assert "补充影响" in final_summary
    assert "批处理入口" in final_summary
    assert "Controller 只能调用 Service" in final_summary
    assert "bugfix 工作流适合缺陷修复" in final_summary
    assert "影响 Guides 与写入前成熟度预览" in final_summary
    assert "影响团队上下文 Guide 与 human-input-needed" in final_summary
    assert "影响 Workflow 说明与后续人工确认记录" in final_summary

    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert "批处理入口" in decisions["scan_confirmation"]["notes"][0]
    assert "Controller 只能调用 Service" in decisions["context_confirmation"]["inline_contexts"][0]
    assert "bugfix 工作流适合缺陷修复" in decisions["workflow_confirmation"]["notes"][0]
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    human_input = (repo / ".ai" / "human-input-needed.md").read_text(encoding="utf-8")
    assert "批处理入口" in project_context
    assert "Controller 只能调用 Service" in project_context
    assert "bugfix 工作流适合缺陷修复" in project_context
    assert "批处理入口" in human_input
    assert "Controller 只能调用 Service" in human_input
    assert "bugfix 工作流适合缺陷修复" in human_input


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


def test_guided_init_existing_harness_can_exit_without_overwriting_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output

    inventory_before = (repo / ".ai" / "project-inventory.json").read_text(encoding="utf-8")
    config_before = (repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8")
    summary_before = (repo / ".ai" / "init-summary.md").read_text(encoding="utf-8")

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness exit must not scan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="exit\n")

    assert result.exit_code == 0, result.output
    assert "已存在 Harness" in result.output
    assert "当前成熟度" in result.output
    assert "Experience / review signals" in result.output
    assert "Maintenance triage" in result.output
    assert "top_action_1=benchmark" in result.output
    assert "reason=benchmark_not_run" in result.output
    assert "source=.ai/benchmark-report.yaml" in result.output
    assert "next=benchmark" in result.output
    assert "pending_improvements=" in result.output
    assert "asset_candidates=" in result.output
    assert "candidate_governance=" in result.output
    assert "maturity_reviews=" in result.output
    assert "workflow_recommendations=" in result.output
    assert "runtime_task_runs=" in result.output
    assert "self_improve_package=" in result.output
    assert "human_input_needed=" in result.output
    assert "schema_content_failed_checks=" in result.output
    assert "exit" in result.output
    assert (repo / ".ai" / "project-inventory.json").read_text(encoding="utf-8") == inventory_before
    assert (repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8") == config_before
    assert (repo / ".ai" / "init-summary.md").read_text(encoding="utf-8") == summary_before

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert trace["summary"]["existing_harness_action"] == "exit"


def test_guided_init_existing_harness_shows_latest_workflow_recommendation_history(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    ai = repo / ".ai"
    history_dir = ai / "review" / "workflow-routing-recommendations"
    history_dir.mkdir(parents=True, exist_ok=True)
    history_entries = [
        {
            "recommendation_id": "task-1-20260531T120000Z",
            "task_id": "task-1",
            "created_at": "2026-05-31T12:00:00Z",
            "yaml_path": ".ai/review/workflow-routing-recommendations/task-1-20260531T120000Z.yaml",
            "markdown_path": ".ai/review/workflow-routing-recommendations/task-1-20260531T120000Z.md",
            "recommended_workflow": "bugfix",
            "risk_level": "medium",
            "confidence": "high",
            "review_status": "pending_harness_maintainer_review",
        },
        {
            "recommendation_id": "task-2-20260531T121500Z",
            "task_id": "task-2",
            "created_at": "2026-05-31T12:15:00Z",
            "yaml_path": ".ai/review/workflow-routing-recommendations/task-2-20260531T121500Z.yaml",
            "markdown_path": ".ai/review/workflow-routing-recommendations/task-2-20260531T121500Z.md",
            "recommended_workflow": "standard",
            "risk_level": "high",
            "confidence": "medium",
            "review_status": "pending_harness_maintainer_review",
        },
    ]
    (history_dir / "index.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "latest_recommendation_id": "task-2-20260531T121500Z",
                "recommendations": history_entries,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    write_experience_index(ai)

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="exit\n")

    assert result.exit_code == 0, result.output
    assert "workflow_recommendations=2" in result.output
    assert "latest_workflow_recommendation=task-2-20260531T121500Z" in result.output
    assert "task=task-2" in result.output
    assert "workflow=standard" in result.output
    assert "risk=high" in result.output
    assert "status=pending_harness_maintainer_review" in result.output
    assert "source=.ai/review/workflow-routing-recommendations/index.yaml" in result.output


def test_guided_init_existing_harness_shows_legacy_latest_workflow_recommendation(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    ai = repo / ".ai"
    review_dir = ai / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "workflow-routing-recommendation.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "task_id": "legacy-task",
                "task_brief": "Fix legacy checkout regression.",
                "recommended_workflow": "bugfix",
                "matched_rule_ids": ["bugfix-intent"],
                "risk_level": "medium",
                "confidence": "high",
                "rationale": "Legacy latest recommendation.",
                "required_guides": [".ai/guides/task-templates/bugfix.md"],
                "required_sensors": [".ai/sensors/verification.md"],
                "human_confirmation_required": False,
                "review_status": "pending_harness_maintainer_review",
                "evidence_sources": [".ai/harness-config.yaml", ".ai/maturity-evidence.yaml"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    write_experience_index(ai)

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="exit\n")

    assert result.exit_code == 0, result.output
    assert "workflow_recommendations=1" in result.output
    assert "latest_workflow_recommendation=legacy_latest" in result.output
    assert "task=legacy-task" in result.output
    assert "workflow=bugfix" in result.output
    assert "risk=medium" in result.output
    assert "source=.ai/review/workflow-routing-recommendation.yaml" in result.output


def test_guided_init_existing_harness_can_assess_without_overwriting_formal_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output

    inventory_before = (repo / ".ai" / "project-inventory.json").read_text(encoding="utf-8")
    config_before = (repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8")
    guide_before = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    sensor_before = (repo / ".ai" / "sensors" / "verification.md").read_text(encoding="utf-8")
    skill_before = (repo / ".ai" / "skills" / "lightweight" / "SKILL.md").read_text(encoding="utf-8")
    (repo / ".ai" / "maturity-score.yaml").unlink()
    (repo / ".ai" / "maturity-evidence.yaml").unlink()

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness assess must reuse existing Harness state, not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="assess\n")

    assert result.exit_code == 0, result.output
    assert "已存在 Harness" in result.output
    assert "assess" in result.output
    assert "成熟度评估已刷新" in result.output
    assert "当前成熟度" in result.output
    assert (repo / ".ai" / "project-inventory.json").read_text(encoding="utf-8") == inventory_before
    assert (repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8") == config_before
    assert (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8") == guide_before
    assert (repo / ".ai" / "sensors" / "verification.md").read_text(encoding="utf-8") == sensor_before
    assert (repo / ".ai" / "skills" / "lightweight" / "SKILL.md").read_text(encoding="utf-8") == skill_before

    maturity_score = yaml.safe_load((repo / ".ai" / "maturity-score.yaml").read_text(encoding="utf-8"))
    assert maturity_score["overall_level"].startswith("L")
    maturity_report = (repo / ".ai" / "maturity-report.md").read_text(encoding="utf-8")
    assert "## 推荐下一步" in maturity_report
    maturity_evidence = yaml.safe_load((repo / ".ai" / "maturity-evidence.yaml").read_text(encoding="utf-8"))
    assert maturity_evidence["primary_stack"] == "java-spring"
    assert maturity_evidence["inventory_summary"]["module_count"] >= 1
    init_summary = (repo / ".ai" / "init-summary.md").read_text(encoding="utf-8")
    assert "## 当前成熟度" in init_summary
    assert "## 建议下一步" in init_summary

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert trace["summary"]["existing_harness_action"] == "assess"
    artifacts = _latest_init_artifacts(repo)
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/maturity-score.yaml" in artifact_paths
    assert ".ai/maturity-report.md" in artifact_paths
    assert ".ai/maturity-evidence.yaml" in artifact_paths
    assert ".ai/init-summary.md" in artifact_paths


def test_guided_init_existing_harness_can_improve_without_overwriting_formal_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness improve must reuse existing Harness state, not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.assess_maturity.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="improve\n")

    assert result.exit_code == 0, result.output
    assert "已存在 Harness" in result.output
    assert "improve" in result.output
    assert "改进候选已生成" in result.output
    assert "优先候选" in result.output
    _assert_formal_assets_unchanged(repo, formal_before)

    candidates = ImprovementCandidateReport.model_validate(
        yaml.safe_load((repo / ".ai" / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    )
    assert candidates.candidates
    assert any(candidate.id in result.output for candidate in candidates.candidates)
    assert all(candidate.human_confirmation_required is True for candidate in candidates.candidates)
    assert all(candidate.suggested_target.startswith(".ai/") for candidate in candidates.candidates)
    assert all(".ai/maturity-evidence.yaml" in candidate.evidence_sources for candidate in candidates.candidates)
    pending = (repo / ".ai" / "experience" / "pending-improvements.md").read_text(encoding="utf-8")
    assert "## 待确认改进候选" in pending
    assert "Acceptance checks" in pending
    evolution = (repo / ".ai" / "evolution-plan.md").read_text(encoding="utf-8")
    assert "## 优先级路线图" in evolution
    experience_index = yaml.safe_load((repo / ".ai" / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert experience_index["pending_improvement_count"] >= 1

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert "scan" not in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "improve"
    artifacts = _latest_init_artifacts(repo)
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/maturity-score.yaml" in artifact_paths
    assert ".ai/maturity-report.md" in artifact_paths
    assert ".ai/maturity-evidence.yaml" in artifact_paths
    assert ".ai/init-summary.md" in artifact_paths
    assert ".ai/improvement-candidates.yaml" in artifact_paths
    assert ".ai/evolution-plan.md" in artifact_paths
    assert ".ai/experience/pending-improvements.md" in artifact_paths
    assert ".ai/experience/experience-index.yaml" in artifact_paths


def test_guided_init_existing_harness_can_benchmark_without_overwriting_formal_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness benchmark must validate existing assets, not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.assess_maturity.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="benchmark\n")

    assert result.exit_code == 0, result.output
    assert "已存在 Harness" in result.output
    assert "benchmark" in result.output
    assert "Benchmark 已通过" in result.output
    assert "quality=" in result.output
    assert ".ai/benchmark-report.yaml" in result.output
    _assert_formal_assets_unchanged(repo, formal_before)

    report = BenchmarkReport.model_validate(
        yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text(encoding="utf-8"))
    )
    assert report.status == "passed"
    assert report.quality_status in {"passed", "degraded"}
    check_ids = {check.id for check in report.checks}
    assert "schema:benchmark-report" in check_ids
    assert "profile_matches_stack" in check_ids

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert "scan" not in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "benchmark"
    assert trace["summary"]["benchmark_status"] == "passed"
    artifacts = _latest_init_artifacts(repo)
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/benchmark-report.yaml" in artifact_paths
    assert ".ai/maturity-score.yaml" in artifact_paths
    assert ".ai/improvement-candidates.yaml" in artifact_paths
    assert ".ai/experience/experience-index.yaml" in artifact_paths


def test_guided_init_existing_harness_benchmark_reports_failed_checks(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    catalog_path = repo / ".ai" / "command-catalog.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    catalog["commands"][0]["confidence"] = "low"
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True), encoding="utf-8")
    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness benchmark failure reporting must not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.assess_maturity.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="bench\n")

    assert result.exit_code == 0, result.output
    assert "Benchmark 未通过" in result.output
    assert "content:hard-gate-command-evidence" in result.output
    assert "failed_checks=1" in result.output
    _assert_formal_assets_unchanged(repo, formal_before)

    report = BenchmarkReport.model_validate(
        yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text(encoding="utf-8"))
    )
    assert report.status == "failed"
    failed_ids = {check.id for check in report.checks if not check.passed}
    assert failed_ids == {"content:hard-gate-command-evidence"}

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "failed"
    assert trace["summary"]["existing_harness_action"] == "benchmark"
    assert trace["summary"]["benchmark_status"] == "failed"
    assert trace["summary"]["failed_check_count"] == 1


def test_guided_init_existing_harness_can_recommend_workflow_without_overwriting_formal_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness recommend-workflow must reuse existing Harness state, not rescan")

    def fake_recommendation(task_id, task_brief, config, evidence_pack, caller=None, llm_config=None):
        assert task_id == "task-1"
        assert task_brief == "Fix checkout permission bug."
        assert "bugfix" in config.workflows
        assert evidence_pack.harness_assets.workflow_routing_rules
        return WorkflowRecommendationReport(
            task_id=task_id,
            task_brief=task_brief,
            recommended_workflow="bugfix",
            matched_rule_ids=["bugfix-intent"],
            risk_level="medium",
            confidence="high",
            rationale="Bugfix intent matches the configured bugfix routing rule.",
            required_guides=[".ai/guides/task-templates/bugfix.md"],
            required_sensors=[".ai/sensors/verification.md"],
            human_confirmation_required=False,
            evidence_sources=[".ai/harness-config.yaml", ".ai/maturity-evidence.yaml"],
        )

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.assess_maturity.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.recommend_workflow.recommend_workflow_with_llm", fake_recommendation)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="recommend-workflow\nFix checkout permission bug.\ntask-1\n",
    )

    assert result.exit_code == 0, result.output
    assert "已存在 Harness" in result.output
    assert "recommend-workflow" in result.output
    assert "工作流推荐已生成" in result.output
    assert "bugfix" in result.output
    assert ".ai/review/workflow-routing-recommendation.yaml" in result.output
    assert ".ai/review/workflow-routing-recommendations/index.yaml" in result.output
    assert ".ai/review/workflow-routing-recommendations.md" in result.output
    _assert_formal_assets_unchanged(repo, formal_before)

    yaml_path = repo / ".ai" / "review" / "workflow-routing-recommendation.yaml"
    markdown_path = repo / ".ai" / "review" / "workflow-routing-recommendation.md"
    recommendation = WorkflowRecommendationReport.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
    markdown = markdown_path.read_text(encoding="utf-8")
    assert recommendation.recommended_workflow == "bugfix"
    assert recommendation.review_status == "pending_harness_maintainer_review"
    assert "## Review Boundary" in markdown
    assert "pending_harness_maintainer_review" in markdown
    assert not (repo / ".ai" / "task-runs").exists()

    experience_index = yaml.safe_load((repo / ".ai" / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert experience_index["workflow_recommendation_count"] == 1
    maturity_evidence = yaml.safe_load((repo / ".ai" / "maturity-evidence.yaml").read_text(encoding="utf-8"))
    assert maturity_evidence["experience"]["workflow_recommendation_count"] == 1

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert "scan" not in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "recommend-workflow"
    assert trace["summary"]["recommended_workflow"] == "bugfix"
    artifacts = _latest_init_artifacts(repo)
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/review/workflow-routing-recommendation.yaml" in artifact_paths
    assert ".ai/review/workflow-routing-recommendation.md" in artifact_paths
    assert ".ai/review/workflow-routing-recommendations/index.yaml" in artifact_paths
    assert ".ai/review/workflow-routing-recommendations.md" in artifact_paths
    assert ".ai/experience/experience-index.yaml" in artifact_paths
    assert ".ai/maturity-evidence.yaml" in artifact_paths

    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", fail_scan)
    benchmark_result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])
    assert benchmark_result.exit_code == 0, benchmark_result.output
    benchmark_report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text(encoding="utf-8"))
    recommendation_check = next(check for check in benchmark_report["checks"] if check["id"] == "content:workflow-recommendation-review")
    assert recommendation_check["passed"] is True


def test_guided_init_existing_harness_can_record_candidate_governance_without_applying_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    review_dir = repo / ".ai" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "asset-candidates.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_maturity_review",
                "candidates": [
                    {
                        "id": "guide-project-context-scope",
                        "kind": "guide",
                        "source_candidate_id": None,
                        "source_review_decision": "support",
                        "suggested_path": ".ai/guides/project-context.md",
                        "title": "Scope project context guide",
                        "rationale": "Candidate is grounded in maturity evidence.",
                        "draft_content": "## Candidate Addition\n\nAdd task loading scope.",
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                        "acceptance_checks": ["Benchmark content:guides-quality passes."],
                        "risk_level": "medium",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness candidate governance must reuse existing Harness state, not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "review-candidate\n"
            "guide-project-context-scope\n"
            "accepted\n"
            "Maintainer accepted the direction but did not apply it yet.\n"
            "lead-reviewer\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "已存在 Harness" in result.output
    assert "review-candidate" in result.output
    assert "待治理候选" in result.output
    assert "Scope project context guide" in result.output
    assert "候选治理决策已记录" in result.output
    assert "accepted" in result.output
    _assert_formal_assets_unchanged(repo, formal_before)

    governance = CandidateGovernanceLog.model_validate(
        yaml.safe_load((review_dir / "candidate-governance.yaml").read_text(encoding="utf-8"))
    )
    assert governance.decisions[0].candidate_id == "guide-project-context-scope"
    assert governance.decisions[0].decision == "accepted"
    assert governance.decisions[0].reviewer == "lead-reviewer"
    assert governance.decisions[0].applied_paths == []
    markdown = (review_dir / "candidate-governance.md").read_text(encoding="utf-8")
    assert "## Review Boundary" in markdown
    experience_index = yaml.safe_load((repo / ".ai" / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert experience_index["candidate_governance_decision_count"] == 1

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert "scan" not in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "review-candidate"
    assert trace["summary"]["candidate_id"] == "guide-project-context-scope"
    assert trace["summary"]["decision"] == "accepted"
    artifacts = _latest_init_artifacts(repo)
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/review/candidate-governance.yaml" in artifact_paths
    assert ".ai/review/candidate-governance.md" in artifact_paths
    assert ".ai/experience/experience-index.yaml" in artifact_paths


def test_guided_init_existing_harness_can_apply_guide_candidate_with_review_boundary(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    review_dir = repo / ".ai" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "asset-candidates.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_maturity_review",
                "candidates": [
                    {
                        "id": "guide-project-context-scope",
                        "kind": "guide",
                        "source_candidate_id": None,
                        "source_review_decision": "support",
                        "suggested_path": ".ai/guides/project-context.md",
                        "title": "Scope project context guide",
                        "rationale": "Candidate is grounded in maturity evidence.",
                        "draft_content": "## Candidate Addition\n\nAdd task loading scope.",
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                        "acceptance_checks": ["Benchmark content:guides-quality passes."],
                        "risk_level": "medium",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness candidate apply must reuse existing Harness state, not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "review-candidate\n"
            "guide-project-context-scope\n"
            "applied\n"
            "Maintainer reviewed the evidence and accepted this guide addition.\n"
            "lead-reviewer\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "候选详情" in result.output
    assert "应用预览" in result.output
    assert "apply_preview=available" in result.output
    assert "target=.ai/guides/project-context.md" in result.output
    assert "apply_mode=append_markdown_candidate_block" in result.output
    assert "target_exists=true" in result.output
    assert "duplicate_marker=absent" in result.output
    assert "block_heading=## Applied Candidate: Scope project context guide" in result.output
    assert "source_report=.ai/review/asset-candidates.yaml" in result.output
    assert "diff_preview=unified_append" in result.output
    assert "+<!-- harness-builder:candidate-applied id=guide-project-context-scope -->" in result.output
    assert "+## Applied Candidate: Scope project context guide" in result.output
    assert "+## Candidate Addition" in result.output
    assert "+Add task loading scope." in result.output
    assert "risk=medium" in result.output
    assert ".ai/maturity-evidence.yaml" in result.output
    assert "Benchmark content:guides-quality passes." in result.output
    assert "候选治理决策已记录" in result.output
    assert "applied" in result.output
    assert "applied_paths=1" in result.output
    assert not (repo / ".ai" / "task-runs").exists()

    target = repo / ".ai" / "guides" / "project-context.md"
    updated = target.read_text(encoding="utf-8")
    assert formal_before[".ai/guides/project-context.md"] in updated
    assert "<!-- harness-builder:candidate-applied id=guide-project-context-scope -->" in updated
    assert "## Applied Candidate: Scope project context guide" in updated
    for relative_path, content in formal_before.items():
        if relative_path == ".ai/guides/project-context.md":
            continue
        assert (repo / relative_path).read_text(encoding="utf-8") == content

    governance = CandidateGovernanceLog.model_validate(
        yaml.safe_load((review_dir / "candidate-governance.yaml").read_text(encoding="utf-8"))
    )
    assert governance.decisions[0].candidate_id == "guide-project-context-scope"
    assert governance.decisions[0].decision == "applied"
    assert governance.decisions[0].reviewer == "lead-reviewer"
    assert governance.decisions[0].applied_paths == [".ai/guides/project-context.md"]
    experience_index = yaml.safe_load((repo / ".ai" / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert experience_index["candidate_governance_decision_count"] == 1

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert "scan" not in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "review-candidate"
    assert trace["summary"]["candidate_id"] == "guide-project-context-scope"
    assert trace["summary"]["decision"] == "applied"
    assert trace["summary"]["applied_path_count"] == 1
    artifacts = _latest_init_artifacts(repo)
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/review/candidate-governance.yaml" in artifact_paths
    assert ".ai/review/candidate-governance.md" in artifact_paths
    assert ".ai/experience/experience-index.yaml" in artifact_paths


def test_guided_init_existing_harness_previews_duplicate_candidate_marker_before_apply_failure(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    review_dir = repo / ".ai" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "asset-candidates.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_maturity_review",
                "candidates": [
                    {
                        "id": "guide-project-context-scope",
                        "kind": "guide",
                        "source_candidate_id": None,
                        "source_review_decision": "support",
                        "suggested_path": ".ai/guides/project-context.md",
                        "title": "Scope project context guide",
                        "rationale": "Candidate is grounded in maturity evidence.",
                        "draft_content": "## Candidate Addition\n\nAdd task loading scope.",
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                        "acceptance_checks": ["Benchmark content:guides-quality passes."],
                        "risk_level": "medium",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    target = repo / ".ai" / "guides" / "project-context.md"
    original = target.read_text(encoding="utf-8")
    target.write_text(
        f"{original}\n\n<!-- harness-builder:candidate-applied id=guide-project-context-scope -->\n"
        "## Applied Candidate: Scope project context guide\n\n"
        "Already applied.\n"
        "<!-- /harness-builder:candidate-applied -->\n",
        encoding="utf-8",
    )

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness candidate apply must reuse existing Harness state, not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "review-candidate\n"
            "guide-project-context-scope\n"
            "applied\n"
            "Maintainer tried to apply a duplicate candidate.\n"
            "lead-reviewer\n"
        ),
    )

    assert result.exit_code != 0
    assert "应用预览" in result.output
    assert "duplicate_marker=present" in result.output
    assert "candidate already applied" in result.output
    assert not (review_dir / "candidate-governance.yaml").exists()
    assert target.read_text(encoding="utf-8").count("<!-- harness-builder:candidate-applied id=guide-project-context-scope -->") == 1


def test_guided_init_existing_harness_rejects_workflow_policy_apply(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    review_dir = repo / ".ai" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "asset-candidates.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_maturity_review",
                "candidates": [
                    {
                        "id": "workflow-standard-domain-policy",
                        "kind": "workflow_policy",
                        "source_candidate_id": None,
                        "source_review_decision": "support",
                        "suggested_path": ".ai/harness-config.yaml",
                        "title": "Escalate domain policy changes",
                        "rationale": "Domain policy changes should use the standard workflow.",
                        "draft_content": "Structured workflow policy patch.",
                        "workflow_policy_patch": {
                            "schema_version": "1.0",
                            "operation": "upsert_routing_rule",
                            "target": "workflow_routing.rules",
                            "rule": {
                                "id": "standard-escalation",
                                "selected_workflow": "standard",
                                "rationale": "Escalate high-risk and domain policy changes to the standard workflow.",
                                "task_type_hints": ["feature", "policy"],
                                "triggers": [
                                    "unclear_impact_scope",
                                    "high_risk_module",
                                    "cross_module_design",
                                    "security_or_permission",
                                    "insufficient_sensor_coverage",
                                    "domain_policy_change",
                                ],
                                "required_guides": [".ai/guides/project-context.md", ".ai/guides/architecture.md"],
                                "required_sensors": [".ai/sensors/verification.md"],
                                "human_confirmation_required": True,
                            },
                        },
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                        "acceptance_checks": ["Benchmark content:workflow-routing-policy passes."],
                        "risk_level": "medium",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "review-candidate\n"
            "workflow-standard-domain-policy\n"
            "applied\n"
        ),
    )

    assert result.exit_code != 0
    assert "应用预览" in result.output
    assert "apply_preview=expert_command_required" in result.output
    assert "target=.ai/harness-config.yaml" in result.output
    assert "guided_workflow_policy_apply=false" in result.output
    assert "workflow_policy" in result.output
    assert "expert command" in result.output
    assert not (review_dir / "candidate-governance.yaml").exists()


def test_guided_init_existing_harness_can_self_improve_without_overwriting_formal_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness self-improve must reuse existing Harness state, not rescan")

    def fake_review(score, evidence_pack, candidates, experience_summary=None):
        return MaturityReviewReport(
            summary="Maturity candidates are ready for asset drafting.",
            reviewer_model="deepseek-test",
            candidate_reviews=[
                {
                    "candidate_id": candidates.candidates[0].id,
                    "decision": "support",
                    "rationale": "The candidate is grounded in maturity evidence.",
                    "suggested_acceptance_checks": ["Run benchmark."],
                    "evidence_sources": [".ai/maturity-evidence.yaml"],
                }
            ],
        )

    def fake_asset_candidates(score, evidence_pack, improvement_candidates, maturity_review, experience_summary=None):
        return AssetCandidateReport(
            candidates=[
                {
                    "id": "guide-project-context-scope",
                    "kind": "guide",
                    "source_candidate_id": improvement_candidates.candidates[0].id,
                    "source_review_decision": "support",
                    "suggested_path": ".ai/guides/project-context.md",
                    "title": "Scope project context guide",
                    "rationale": "The supported candidate needs a reviewable guide draft.",
                    "draft_content": "## Candidate Addition\n\nAdd task loading scope.",
                    "evidence_sources": [".ai/maturity-evidence.yaml"],
                    "acceptance_checks": ["Benchmark content:guides-quality passes."],
                    "risk_level": "medium",
                },
                {
                    "id": "sensor-verification-hard-gate",
                    "kind": "sensor",
                    "source_candidate_id": improvement_candidates.candidates[0].id,
                    "source_review_decision": "support",
                    "suggested_path": ".ai/sensors/verification.md",
                    "title": "Clarify verification hard gate",
                    "rationale": "The supported candidate needs a reviewable sensor draft.",
                    "draft_content": "## Candidate Addition\n\nClarify hard gate evidence.",
                    "evidence_sources": [".ai/maturity-evidence.yaml"],
                    "acceptance_checks": ["Benchmark content:sensors-quality passes."],
                    "risk_level": "medium",
                },
            ]
        )

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.assess_maturity.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.review_maturity.review_maturity_with_llm", fake_review)
    monkeypatch.setattr(
        "harness_builder_agent.tools.generate_asset_candidates.generate_asset_candidates_with_llm",
        fake_asset_candidates,
    )

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="self-improve\n")

    assert result.exit_code == 0, result.output
    assert "已存在 Harness" in result.output
    assert "self-improve" in result.output
    assert "自改进审查包已生成" in result.output
    assert ".ai/review/self-improve-package.yaml" in result.output
    _assert_formal_assets_unchanged(repo, formal_before)
    assert not (repo / ".ai" / "task-runs").exists()

    manifest = SelfImprovePackageManifest.model_validate(
        yaml.safe_load((repo / ".ai" / "review" / "self-improve-package.yaml").read_text(encoding="utf-8"))
    )
    markdown = (repo / ".ai" / "review" / "self-improve-package.md").read_text(encoding="utf-8")
    assert manifest.review_status == "pending_harness_maintainer_review"
    assert manifest.candidate_counts.maturity_reviews == 1
    assert manifest.candidate_counts.asset_candidates == 2
    assert "## Review Boundary" in markdown
    assert "pending_harness_maintainer_review" in markdown

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert "scan" not in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "self-improve"
    assert trace["summary"]["asset_candidate_count"] == 2
    artifacts = _latest_init_artifacts(repo)
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/review/self-improve-package.yaml" in artifact_paths
    assert ".ai/review/self-improve-package.md" in artifact_paths
    assert ".ai/review/asset-candidates.yaml" in artifact_paths
    assert ".ai/review/maturity-review.yaml" in artifact_paths
    assert ".ai/improvement-candidates.yaml" in artifact_paths

    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", fail_scan)
    benchmark_result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])
    assert benchmark_result.exit_code == 0, benchmark_result.output
    benchmark_report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text(encoding="utf-8"))
    package_check = next(check for check in benchmark_report["checks"] if check["id"] == "content:self-improve-package")
    assert package_check["passed"] is True


def test_guided_init_existing_harness_improve_refreshes_stale_experience_evidence(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    review = repo / ".ai" / "review"
    review.mkdir(parents=True, exist_ok=True)
    (review / "workflow-routing-recommendation.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "task_id": "manual-task",
                "task_brief": "修改高风险权限逻辑。",
                "recommended_workflow": "standard",
                "matched_rule_ids": ["standard-escalation"],
                "risk_level": "high",
                "confidence": "high",
                "rationale": "权限逻辑需要标准流程。",
                "required_guides": [".ai/guides/project-context.md"],
                "required_sensors": [".ai/sensors/verification.md"],
                "human_confirmation_required": True,
                "review_status": "pending_harness_maintainer_review",
                "evidence_sources": [".ai/harness-config.yaml", ".ai/maturity-evidence.yaml"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    stale_index = yaml.safe_load((repo / ".ai" / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert stale_index["workflow_recommendation_count"] == 0

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness improve must not rescan while refreshing evidence")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.assess_maturity.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="improve\n")

    assert result.exit_code == 0, result.output
    refreshed_index = yaml.safe_load((repo / ".ai" / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
    assert refreshed_index["workflow_recommendation_count"] == 1
    evidence = yaml.safe_load((repo / ".ai" / "maturity-evidence.yaml").read_text(encoding="utf-8"))
    assert evidence["experience"]["workflow_recommendation_count"] == 1
    candidates = yaml.safe_load((repo / ".ai" / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    workflow_candidate = next(item for item in candidates["candidates"] if item["id"] == "experience-workflow-recommendation-review")
    assert workflow_candidate["candidate_type"] == "workflow_policy_update"
    assert workflow_candidate["suggested_target"] == ".ai/harness-config.yaml"
    assert ".ai/review/workflow-routing-recommendation.yaml" in workflow_candidate["evidence_sources"]
