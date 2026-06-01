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
from harness_builder_agent.schemas.human_confirmation import Questionnaire
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.weapon_candidate_governance import WeaponCandidateGovernanceLog
from harness_builder_agent.schemas.scan import ScanMetadata
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools import interactive_init
from harness_builder_agent.tools.experience_index import write_experience_index
from harness_builder_agent.tools.scan_repo import ScanProgressEvent, scan_repository

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
    evidence_plan_response = json.dumps(
        {
            "schema_version": "1.0",
            "requested_paths": [],
            "risk_focus": [],
            "rationale": "Fixture scan did not require additional files.",
            "confidence": "high",
        }
    )
    return scan_repository(
        repo,
        llm_caller=lambda _messages: json.dumps(response),
        evidence_planner_caller=lambda _messages: evidence_plan_response,
    )


def _fake_scan_with_progress(repo: Path, expected_stack: str, *, progress=None):
    if progress is not None:
        for phase in [
            "collect-evidence",
            "plan-evidence-expansion",
            "expand-evidence",
            "llm-scan",
            "reconcile-scan",
        ]:
            progress(ScanProgressEvent(phase=phase, status="started", message=phase))
            progress(ScanProgressEvent(phase=phase, status="completed", message=phase))
    return _fake_scan(repo, expected_stack)


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
    ScanMetadata.model_validate(scan_metadata)
    assert scan_metadata["llm_status"] == "succeeded"
    assert scan_metadata["evidence_expansion"]["requested_paths"] == []
    assert scan_metadata["evidence_expansion"]["read_paths"] == []
    assert scan_metadata["evidence_expansion"]["read_file_count"] == 0
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
    assert "## 风险区域" in project_context
    assert "## 验证入口" in project_context
    assert "## 成熟度缺口关联" in project_context
    assert "## Harness Builder 推荐补齐项" in project_context
    assert "## 人工确认点" in project_context

    verification = (ai / "sensors" / "verification.md").read_text(encoding="utf-8")
    assert "## 武器库匹配结果" in verification
    assert "common.sensor." in verification
    assert f"{expected_stack}.sensor." in verification
    assert "## 已发现的验证命令" in verification
    assert "## 风险与验证映射" in verification
    assert "## 成熟度缺口关联" in verification
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
    assert "## 本仓库关键事实" in init_summary
    assert "## 主要阻断项" in init_summary
    assert "## 建议下一步" in init_summary
    assert "## 本次吸收的用户补充" in init_summary
    assert "## 资产如何补齐缺口" in init_summary
    assert "## 待人工确认" in init_summary
    assert ".ai/human-input-needed.md#处理方式" in init_summary
    assert "confirm:team-context" in init_summary
    assert "confirm:guide-candidates" in init_summary
    assert "confirm:sensor-gates" in init_summary
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
    assert all(item["review_boundary"] == "review_only_no_formal_asset_change" for item in candidate_report["candidates"])
    assert any(item["maturity_dimensions"] for item in candidate_report["candidates"])
    assert all("maturity_impact_summary" in item for item in candidate_report["candidates"])

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
    assert "== 初始化完成 ==" in result.output
    assert "本次已生成" in result.output
    assert "优先查看" in result.output
    assert "仍需人工确认" in result.output
    assert "本终端摘要是本次 init 的主要交付说明" in result.output
    assert "Benchmark 健康度" in result.output
    assert "benchmark_status=not_run" in result.output
    assert "quality_status=not_available" in result.output
    assert "harness-builder-agent benchmark --repo" in result.output
    assert ".ai/init-summary.md" in result.output
    assert ".ai/maturity-report.md" in result.output
    completion_summary = result.output[result.output.index("== 初始化完成 ==") :]
    assert completion_summary.index("当前成熟度：") < completion_summary.index("本次已生成：")
    assert completion_summary.index("建议下一步：") < completion_summary.index("本次已生成：")
    assert completion_summary.index("Benchmark 健康度：") < completion_summary.index("本次已生成：")
    assert completion_summary.index("优先查看：") < completion_summary.index("本次已生成：")
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
    assert "== 初始化完成 ==" in result.output
    assert "本次已生成" in result.output
    assert "优先查看" in result.output
    assert "仍需人工确认" in result.output
    assert "本终端摘要是本次 init 的主要交付说明" in result.output
    assert "本次吸收的用户补充" in result.output
    assert "本次未提供人工补充" in result.output
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
    assert "== 启动说明 ==" not in result.output
    assert "当前阶段：收集仓库 evidence" not in result.output
    assert "扫描后的成熟度初评" not in result.output


def test_init_default_guided_mode_accepts_happy_path(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr(
        "harness_builder_agent.tools.interactive_init.scan_repository",
        lambda repo_path, *, progress=None: _fake_scan_with_progress(repo_path, "java-spring", progress=progress),
    )

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="\n\n\n\n\n\n\nconfirm\n",
    )

    assert result.exit_code == 0, result.output
    scan_stage = "\n扫描仓库\n"
    assert "== 启动说明 ==" in result.output
    assert result.output.index("== 启动说明 ==") < result.output.index("继续生成 Harness?")
    assert result.output.index("== 启动说明 ==") < result.output.index(scan_stage)
    assert "将扫描仓库文件、构建配置、CI、测试、文档和源码样本证据" in result.output
    assert "需要你确认或补充技术栈、模块边界、风险区域、验证命令、团队规则和 Workflow 说明" in result.output
    assert "最终确认写入后将生成 project inventory、command catalog、Guides、Sensors、Workflow Skills、成熟度报告和待确认项" in result.output
    startup = result.output[result.output.index("== 启动说明 ==") : result.output.index("继续生成 Harness?")]
    assert "lightweight" in startup
    assert "bugfix" in startup
    assert "standard" in startup
    assert "本次会话会记录 generation trace，用于审计取消、失败和完成结果" in result.output
    assert "不会执行 Runtime" in result.output
    assert "不会创建 `.ai/task-runs`" in result.output
    assert "不会默认运行 benchmark" in result.output
    assert "最终输入 `confirm`/`确认` 前，不会写入或覆盖正式 Harness 资产；trace 只记录本次会话过程" in result.output
    assert scan_stage in result.output
    assert "正在收集仓库文件、构建配置、CI、测试和文档证据" in result.output
    assert "正在请求 LLM 做结构化扫描" in result.output
    assert "正在调和 LLM 判断与 evidence" in result.output
    assert "扫描完成" in result.output
    assert "当前阶段：收集仓库 evidence" in result.output
    assert "当前阶段：请求 LLM 规划补充 evidence" in result.output
    assert "当前阶段：读取 LLM 请求的补充 evidence" in result.output
    assert "当前阶段：请求 LLM 做最终结构化扫描" in result.output
    assert "当前阶段：调和扫描结果" in result.output
    assert result.output.index("当前阶段：收集仓库 evidence") < result.output.index("扫描完成")
    assert result.output.index(scan_stage) < result.output.index("扫描发现")
    assert result.output.index("扫描完成") < result.output.index("扫描发现")
    assert "扫描发现" in result.output
    assert "风险区域" in result.output
    assert "不确定性" in result.output
    assert "验证缺口" in result.output
    assert "建议补充" in result.output
    assert result.output.index("扫描发现") < result.output.index("\n风险区域")
    assert "扫描后的成熟度初评" in result.output
    assert "按当前扫描写入后预计建立" in result.output
    assert "主要差距" in result.output
    assert "建议优先补充" in result.output
    assert "Guides are structured" not in result.output
    assert "Workflow routing policy exists" not in result.output
    assert "Bind guides to workflow" not in result.output
    assert "Validate workflow routing" not in result.output
    assert "Guides 已结构化" in result.output
    assert "用全部 resolved 的 Runtime task-run 证据验证 Workflow routing" in result.output
    assert "hard gate 命令" in result.output
    assert "模块边界" in result.output
    assert "风险区域" in result.output
    assert "团队规则、架构边界或测试策略" in result.output
    assert result.output.index("扫描发现") < result.output.index("扫描后的成熟度初评")
    assert result.output.index("扫描后的成熟度初评") < result.output.index("需要你补充或修正的地方")
    assert result.output.index("扫描后的成熟度初评") < result.output.index("当前 Harness 成熟度初评")
    assert result.output.index("建议补充") < result.output.index("\n团队规则")
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
    preview = result.output[result.output.index("写入前 Harness 设计预览") : result.output.index("\n最终确认\n")]
    assert "扫描补充约束" in preview
    assert "暂无扫描补充；当前按扫描基线、团队规则和内置 Harness 基线生成" in preview
    guides_preview = preview[preview.index("将生成的 Guides") : preview.index("将生成的 Sensors")]
    sensors_preview = preview[preview.index("将生成的 Sensors") : preview.index("Workflow routing")]
    assert "关联成熟度" in guides_preview
    assert "解决阻断" in guides_preview
    assert "下一阶段贡献" in guides_preview
    assert "Guides 上下文" in guides_preview
    assert "Risk Control 风险控制" in guides_preview
    assert "关联成熟度" in sensors_preview
    assert "解决阻断" in sensors_preview
    assert "下一阶段贡献" in sensors_preview
    assert "Sensors 验证" in sensors_preview
    assert "Verification 验证成熟度" in sensors_preview
    assert "standard-escalation" in result.output
    assert "高风险" in result.output
    assert "最终确认" in result.output
    assert result.output.index("当前 Harness 成熟度初评") < result.output.index("\n最终确认\n")
    assert "当前成熟度" in result.output
    assert "== 初始化完成 ==" in result.output
    assert "本次已生成" in result.output
    assert "优先查看" in result.output
    assert "仍需人工确认" in result.output
    assert "本终端摘要是本次 init 的主要交付说明" in result.output
    assert ".ai/init-summary.md" in result.output
    assert "primary_stack" not in result.output
    assert "overall_level" not in result.output
    assert "dimension_scores" not in result.output
    _assert_init_outputs(repo, "java-spring")
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["mode"] == "interactive"
    assert decisions["repo"]["confirmed"] is True
    assert decisions["scan_confirmation"]["status"] == "accepted"
    assert "- standard：适合复杂、高风险、跨模块、安全 / 数据或影响不清任务" in result.output
    assert decisions["workflow_confirmation"]["shown_workflows"] == ["lightweight", "bugfix", "standard"]
    assert decisions["workflow_confirmation"]["confirmed"] is True
    assert decisions["final_confirmation"]["status"] == "confirmed"


def test_guided_init_final_confirm_rejects_unknown_input_before_write(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="\n\n\n\n\n\n\ncnofirm\nconfirm\n",
    )

    assert result.exit_code == 0, result.output
    assert "未识别的最终确认输入" in result.output
    assert "请输入 `confirm`/`确认`、`back`/`返回`、`cancel`/`取消`" in result.output
    assert "或直接输入 `scan`/`扫描`、`rules`/`团队规则`、`candidates`/`候选`、`workflow`/`工作流`" in result.output
    assert result.output.index("未识别的最终确认输入") < result.output.index("== 初始化完成 ==")
    _assert_init_outputs(repo, "java-spring")


def test_guided_init_final_confirm_accepts_chinese_confirm_alias(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="\n\n\n\n\n\n\n确认\n",
    )

    assert result.exit_code == 0, result.output
    assert "输入 confirm/确认 写入，back/返回 修改，cancel/取消 取消" in result.output
    _assert_init_outputs(repo, "java-spring")
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["final_confirmation"]["status"] == "confirmed"


def test_guided_init_final_summary_accepts_chinese_return_alias_to_team_rules(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n\n"
            "初始中文规则需要修改。\n"
            "\n\n\n"
            "\n"
            "返回\n"
            "团队规则\n"
            "最终中文团队规则：配置变更必须说明影响环境。\n"
            "确认\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "返回修改" in result.output
    assert "团队规则返回修改" in result.output
    assert "返回哪一部分？scan/扫描=扫描修正，rules/团队规则=团队规则，candidates/候选=候选项，workflow/工作流=Workflow补充" in result.output
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["context_confirmation"]["inline_contexts"] == ["最终中文团队规则：配置变更必须说明影响环境。"]
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "最终中文团队规则" in project_context
    assert "初始中文规则需要修改" not in project_context


def test_guided_init_final_summary_accepts_direct_chinese_candidate_target(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n\n\n"
            "\n\n\n\n"
            "候选\n"
            "a\n"
            "r\n"
            "e\n"
            "直接返回候选后的备注。\n"
            "确认\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "可直接输入 scan/扫描、rules/团队规则、candidates/候选、workflow/工作流 返回对应部分" in result.output
    assert "返回修改" in result.output
    assert result.output.count("逐项审查模型候选") == 2
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    by_id = {item["candidate_id"]: item for item in decisions["candidate_decisions"]}
    assert by_id["llm-guide-architecture-001"]["decision"] == "accepted"
    assert by_id["llm-guide-risk-001"]["decision"] == "rejected"
    assert by_id["llm-sensor-command-001"]["decision"] == "edited"
    assert by_id["llm-sensor-command-001"]["notes"] == "直接返回候选后的备注。"


def test_guided_init_explains_python_flask_react_multistack(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)

    def scan_multistack(repo_path: Path):
        inventory = ProjectInventory(
            repo_name=repo_path.name,
            root_path=str(repo_path),
            primary_stack="python-flask",
            stacks=["python", "flask", "react", "typescript", "vite"],
            modules=[
                {"name": "api", "path": ".", "kind": "backend"},
                {"name": "web", "path": "frontend", "kind": "frontend"},
            ],
            evidence=[
                {"path": "pyproject.toml", "reason": "Flask dependency"},
                {"path": "frontend/package.json", "reason": "React / TypeScript app"},
            ],
            configs=[{"path": "pyproject.toml", "kind": "python"}, {"path": "frontend/package.json", "kind": "node"}],
            stack_extensions={
                "stack_profile": {
                    "primary_label": "Python Flask 后端",
                    "composition_label": "Python Flask 后端 + React / TypeScript 前端",
                    "supported_stacks": ["python-flask", "node"],
                    "module_roles": [
                        {"name": "api", "path": ".", "kind": "backend"},
                        {"name": "web", "path": "frontend", "kind": "frontend"},
                    ],
                },
                "llm_scan_proposal": {
                    "architecture_signals": ["Flask API and React frontend"],
                    "risk_areas": [],
                    "command_candidates": [
                        {"id": "pytest", "command": "pytest", "source": "pyproject.toml"},
                        {"id": "npm_test", "command": "npm test", "source": "frontend/package.json"},
                    ],
                },
            },
        )
        commands = CommandCatalog(
            commands=[
                {
                    "id": "pytest",
                    "command": "pytest",
                    "type": "test",
                    "gate": "hard",
                    "source": "pyproject.toml",
                    "confidence": "high",
                },
                {
                    "id": "npm_test",
                    "command": "npm test",
                    "type": "test",
                    "gate": "hard",
                    "source": "frontend/package.json",
                    "confidence": "medium",
                },
            ]
        )
        return inventory, commands

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", scan_multistack)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="\n\n\n\n\n\n\nconfirm\n",
    )

    assert result.exit_code == 0, result.output
    assert "Python Flask 后端 + React / TypeScript 前端" in result.output
    assert "stack=python-flask" in result.output
    assert "可以直接用自然语言说明多栈、噪声目录或真实主模块" in result.output
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text(encoding="utf-8"))
    assert inventory["primary_stack"] == "python-flask"
    assert {"backend", "frontend"}.issubset({module["kind"] for module in inventory["modules"]})
    assert inventory["stack_extensions"]["stack_profile"]["composition_label"] == "Python Flask 后端 + React / TypeScript 前端"
    weapon_selection = yaml.safe_load((repo / ".ai" / "weapon-library-selection.yaml").read_text(encoding="utf-8"))
    assert {"common", "python-flask", "node"}.issubset(set(weapon_selection["selected_stacks"]))
    assert any(item.startswith("python-flask.guide.") for item in weapon_selection["guide_weapon_ids"])
    assert any(item.startswith("node.guide.") for item in weapon_selection["guide_weapon_ids"])


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
    assert "Traceback" not in output
    assert not isinstance(result.exception, RuntimeError)
    assert output.index("扫描仓库") < output.index("扫描阶段失败")
    run_dirs = sorted((repo / ".ai" / "runs").iterdir())
    assert len(run_dirs) == 1
    trace = yaml.safe_load((run_dirs[0] / "trace.yaml").read_text(encoding="utf-8"))
    assert trace["status"] == "failed"
    assert trace["summary"]["error_type"] == "RuntimeError"
    assert trace["summary"]["scan_error"] == "synthetic scan failure"
    events = [
        json.loads(line)
        for line in (run_dirs[0] / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert any(
        event["stage"] == "scan"
        and event["event_type"] == "failed"
        and event["details"]["error_type"] == "RuntimeError"
        and event["details"]["error"] == "synthetic scan failure"
        for event in events
    )
    assert not any(event["stage"] == "init" and event["event_type"] == "failed" for event in events)
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
                "risk_areas": [
                    {"path": "src/main/resources/application.yml", "reason": "配置变更影响运行环境"},
                    {"path": "docs/a.json", "reason": "可能包含明文 API key"},
                ],
                "needs_human_confirmation": True,
                "scan_warnings": [
                    {
                        "code": "source_sampling_truncated",
                        "message": "source:.py skipped 73 files",
                        "severity": "warning",
                        "evidence": ["source:.py"],
                    },
                    {
                        "code": "test_evidence_not_found",
                        "message": "No dedicated test evidence bucket was found; test strategy needs human confirmation.",
                        "severity": "warning",
                        "evidence": [],
                    }
                ],
                "scan_metadata": {
                    "coverage": {
                        "bucket_coverage": [
                            {
                                "bucket": "source:.py",
                                "total_count": 93,
                                "selected_count": 20,
                                "skipped_count": 73,
                                "selected_paths": ["app/main.py"],
                            }
                        ]
                    }
                },
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
    assert "高风险，需人工确认" in result.output
    assert "docs/a.json" in result.output
    assert "standard workflow" in result.output
    assert "不确定性" in result.output
    assert "需要人工确认" in result.output
    assert "LLM 扫描置信度为 low" in result.output
    assert "`.py` 源码文件较多" in result.output
    assert "本次已抽样 20/93 个文件" in result.output
    assert "还有 73 个未进入初始摘要" in result.output
    assert "source:.py skipped 73 files" not in result.output
    assert "当前扫描未找到明确测试证据" in result.output
    assert "No dedicated test evidence bucket was found" not in result.output
    assert "mvn -Pintegration test" in result.output
    assert "验证缺口" in result.output
    assert "暂未确认 hard gate" in result.output
    assert "低置信度验证命令" in result.output
    assert "建议补充" in result.output
    assert "真实可执行的 hard gate 命令" in result.output
    assert "确认高风险线索是否确认为风险边界" in result.output
    assert result.output.index("\n风险区域") < result.output.index("\n团队规则")
    assert result.output.index("高风险，需人工确认") < result.output.index("\n团队规则")


def test_guided_init_shows_llm_evidence_expansion_summary_and_confirmation(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)

    def scan_with_evidence_expansion(repo_path: Path):
        inventory = ProjectInventory(
            repo_name=repo_path.name,
            root_path=str(repo_path),
            primary_stack="java-spring",
            stacks=["java", "spring-boot"],
            modules=[{"name": "app", "path": ".", "kind": "backend"}],
            evidence=[{"path": "pom.xml", "reason": "build config"}],
            stack_extensions={
                "scan_metadata": {
                    "evidence_expansion": {
                        "schema_version": "1.0",
                        "planner_prompt_version": "llm-evidence-plan-v1",
                        "requested_paths": ["src/main/java/com/example/AuthService.java"],
                        "risk_focus": ["auth flow"],
                        "rationale": "认证逻辑未进入初始源码摘要。",
                        "confidence": "low",
                        "read_paths": ["src/main/java/com/example/AuthService.java"],
                        "read_file_count": 1,
                    }
                }
            },
        )
        commands = CommandCatalog(commands=[])
        return inventory, commands

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", scan_with_evidence_expansion)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="\n\n\n\n\n\n\nconfirm\n",
    )

    assert result.exit_code == 0, result.output
    assert "LLM 深度补充" in result.output
    assert "src/main/java/com/example/AuthService.java" in result.output
    assert "auth flow" in result.output
    assert "认证逻辑未进入初始源码摘要" in result.output
    assert "置信度：low" in result.output

    questionnaire = yaml.safe_load((repo / ".ai" / "questionnaire.yaml").read_text(encoding="utf-8"))
    Questionnaire.model_validate(questionnaire)
    ids = {item["interaction_id"] for item in questionnaire["questions"]}
    assert "confirm:evidence-expansion" in ids
    human_input = (repo / ".ai" / "human-input-needed.md").read_text(encoding="utf-8")
    assert "confirm:evidence-expansion" in human_input
    assert "src/main/java/com/example/AuthService.java" in human_input


def test_guided_init_shows_scan_followup_questions(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)

    def scan_with_followups(repo_path: Path):
        followups = [
            {
                "schema_version": "1.0",
                "interaction_id": "confirm:scan-followup:coverage-source-java",
                "trigger": "coverage_gap",
                "question": "哪些 Java 目录、入口文件或高风险路径需要补充扫描？",
                "reason": "source:.java 抽样不足，可能影响模块和风险判断。",
                "evidence": ["source:.java"],
                "confidence": "low",
                "affects": ["maturity", "guides", "sensors"],
            },
            {
                "schema_version": "1.0",
                "interaction_id": "confirm:scan-followup:stack-node",
                "trigger": "stack_claim_without_evidence",
                "question": "这个仓库是否存在 Node 子模块？",
                "reason": "LLM 提到了 node，但当前 evidence 未支持。",
                "evidence": ["node"],
                "confidence": "low",
                "affects": ["workflow"],
            },
            {
                "schema_version": "1.0",
                "interaction_id": "confirm:scan-followup:unknown-stack",
                "trigger": "unknown_stack",
                "question": "这个仓库真实主技术栈是什么？",
                "reason": "primary stack unknown。",
                "evidence": ["primary_stack:unknown"],
                "confidence": "low",
                "affects": ["maturity"],
            },
            {
                "schema_version": "1.0",
                "interaction_id": "confirm:scan-followup:module-boundary",
                "trigger": "module_boundary_unclear",
                "question": "主要模块路径和职责是什么？",
                "reason": "模块边界不清。",
                "evidence": ["modules:empty"],
                "confidence": "low",
                "affects": ["guides"],
            },
            {
                "schema_version": "1.0",
                "interaction_id": "confirm:scan-followup:test-evidence",
                "trigger": "test_evidence_missing",
                "question": "真实测试入口是什么？",
                "reason": "缺少测试 evidence。",
                "evidence": ["test_evidence_not_found"],
                "confidence": "low",
                "affects": ["sensors"],
            },
            {
                "schema_version": "1.0",
                "interaction_id": "confirm:scan-followup:release-constraint",
                "trigger": "module_boundary_unclear",
                "question": "发布约束或高风险变更入口是什么？",
                "reason": "需要补充发布风险边界。",
                "evidence": ["release"],
                "confidence": "low",
                "affects": ["workflow"],
            },
        ]
        inventory = ProjectInventory(
            repo_name=repo_path.name,
            root_path=str(repo_path),
            primary_stack="unknown",
            stacks=["node"],
            modules=[],
            evidence=[{"path": "README.md", "reason": "project document"}],
            stack_extensions={
                "needs_human_confirmation": True,
                "scan_metadata": {
                    "followup_questions": followups,
                    "self_check": {
                        "prompt_version": "llm-scan-self-check-v1",
                        "review_status": "pending_harness_maintainer_review",
                        "overall_risk": "high",
                        "summary": "多个深度追问仍需要 Maintainer 复核。",
                        "resolutions": [
                            {
                                "interaction_id": "confirm:scan-followup:coverage-source-java",
                                "trigger": "coverage_gap",
                                "status": "needs_targeted_scan",
                                "rationale": "当前 evidence 仍不足以确认 Java 核心模块覆盖。",
                                "evidence_sources": ["source:.java"],
                                "suggested_action_type": "provide_module",
                                "suggested_next_action": "请补充核心 Java 模块路径。",
                                "confidence": "medium",
                            }
                        ],
                    },
                },
            },
        )
        commands = CommandCatalog(commands=[])
        return inventory, commands

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", scan_with_followups)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="\n\n\n\n\n\n\nconfirm\n",
    )

    assert result.exit_code == 0, result.output
    assert "深度追问" in result.output
    assert "哪些 Java 目录、入口文件或高风险路径需要补充扫描？" in result.output
    assert "source:.java 抽样不足" in result.output
    assert "成熟度、Guides、Sensors" in result.output
    assert "还有 1 个深度追问" in result.output
    assert "LLM 二次自检" in result.output
    assert "pending_harness_maintainer_review" in result.output
    assert "needs_targeted_scan" in result.output
    assert "动作=provide_module" in result.output
    assert "module=路径|类型|名称" in result.output
    assert "请补充核心 Java 模块路径" in result.output
    assert "深度追问回答建议" in result.output
    assert "`confirm:scan-followup:coverage-source-java`" in result.output
    assert "module=src/main/java|backend|核心模块" in result.output
    assert "risk=src/main/java/payments|支付或权限高风险" in result.output
    assert "`confirm:scan-followup:stack-node`" in result.output
    assert "stack=java-spring" in result.output
    assert "`confirm:scan-followup:test-evidence`" in result.output
    assert "command=unit_test|mvn test|test|hard|pom.xml|high" in result.output
    assert "不会自动关闭追问" in result.output
    prewrite_preview = result.output[result.output.index("写入前 Harness 设计预览") : result.output.index("\n最终确认\n")]
    assert "待确认与低置信度边界" in prewrite_preview
    assert "深度追问：6 个待复核" in prewrite_preview
    assert "`confirm:scan-followup:coverage-source-java`" in prewrite_preview
    assert "trigger=coverage_gap" in prewrite_preview
    assert "LLM 二次自检：1 条 review-only 结论" in prewrite_preview
    assert "action=provide_module" in prewrite_preview
    assert "确认写入不会自动关闭追问" in prewrite_preview

    questionnaire = yaml.safe_load((repo / ".ai" / "questionnaire.yaml").read_text(encoding="utf-8"))
    Questionnaire.model_validate(questionnaire)
    question = next(
        item for item in questionnaire["questions"] if item["interaction_id"] == "confirm:scan-followup:coverage-source-java"
    )
    assert question["interaction_type"] == "scan_followup_confirmation"
    assert "LLM 二次自检" in question["reason"]
    assert "action_type=provide_module" in question["reason"]
    human_input = (repo / ".ai" / "human-input-needed.md").read_text(encoding="utf-8")
    assert "confirm:scan-followup:coverage-source-java" in human_input
    assert "哪些 Java 目录" in human_input
    assert "module=src/main/java|backend|核心模块" in human_input
    assert "risk=src/main/java/payments|支付或权限高风险" in human_input
    assert "stack=java-spring" in human_input
    assert "command=unit_test|mvn test|test|hard|pom.xml|high" in human_input
    assert "不会自动关闭追问" in human_input


def test_guided_init_marks_scan_followup_partially_addressed_by_current_supplement(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)

    def scan_with_followups(repo_path: Path):
        followups = [
            {
                "schema_version": "1.0",
                "interaction_id": "confirm:scan-followup:test-evidence",
                "trigger": "test_evidence_missing",
                "question": "真实测试入口是什么？",
                "reason": "缺少测试 evidence。",
                "evidence": ["test_evidence_not_found"],
                "confidence": "low",
                "affects": ["sensors"],
            },
            {
                "schema_version": "1.0",
                "interaction_id": "confirm:scan-followup:module-boundary",
                "trigger": "module_boundary_unclear",
                "question": "主要模块路径和职责是什么？",
                "reason": "模块边界不清。",
                "evidence": ["modules:empty"],
                "confidence": "low",
                "affects": ["guides", "workflow"],
            },
        ]
        inventory = ProjectInventory(
            repo_name=repo_path.name,
            root_path=str(repo_path),
            primary_stack="unknown",
            stacks=[],
            modules=[],
            evidence=[{"path": "README.md", "reason": "project document"}],
            stack_extensions={
                "needs_human_confirmation": True,
                "scan_metadata": {"followup_questions": followups},
            },
        )
        commands = CommandCatalog(commands=[])
        return inventory, commands

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", scan_with_followups)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n"
            "module=src/main/java|backend|core; command=unit_test|mvn test|test|hard|pom.xml|high; risk=src/main/java/com/example/AuthService.java|认证逻辑高风险\n"
            "\n\n\n\n"
            "\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    questionnaire = yaml.safe_load((repo / ".ai" / "questionnaire.yaml").read_text(encoding="utf-8"))
    Questionnaire.model_validate(questionnaire)
    test_question = next(
        item for item in questionnaire["questions"] if item["interaction_id"] == "confirm:scan-followup:test-evidence"
    )
    assert "本轮 scan 补充可能已部分回应该追问" in test_question["reason"]
    assert "command=unit_test:mvn test" in test_question["reason"]
    assert "review_status=pending_harness_maintainer_review" in test_question["reason"]
    assert test_question["response_status"] == "partially_addressed_by_current_scan_supplement"
    assert test_question["response_sources"] == ["command=unit_test:mvn test"]
    module_question = next(
        item for item in questionnaire["questions"] if item["interaction_id"] == "confirm:scan-followup:module-boundary"
    )
    assert "module=src/main/java" in module_question["reason"]
    assert "risk=src/main/java/com/example/AuthService.java" in module_question["reason"]
    assert module_question["response_status"] == "partially_addressed_by_current_scan_supplement"
    assert module_question["response_sources"] == [
        "module=src/main/java",
        "risk=src/main/java/com/example/AuthService.java",
    ]

    human_input = (repo / ".ai" / "human-input-needed.md").read_text(encoding="utf-8")
    assert "本轮 scan 补充可能已部分回应该追问" in human_input
    assert "command=unit_test:mvn test" in human_input
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["scan_confirmation"]["commands"][0]["id"] == "unit_test"
    assert decisions["scan_confirmation"]["modules"] == [{"path": "src/main/java", "kind": "backend", "name": "core"}]
    assert decisions["scan_confirmation"]["risk_areas"] == [
        {"path": "src/main/java/com/example/AuthService.java", "reason": "认证逻辑高风险"}
    ]
    assert decisions["scan_confirmation"]["review_status"] == "pending_harness_maintainer_review"
    assert decisions["scan_confirmation"]["fact_effect"] == "user_supplied_correction_review_required"

    existing_result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="exit\n")
    assert existing_result.exit_code == 0, existing_result.output
    assert "human_input_scan_followups_partially_addressed=2" in existing_result.output
    assert "human_input_scan_followups_unaddressed=0" in existing_result.output
    assert "top_action_2=review-human-input" in existing_result.output
    assert "reason=human_input_scan_followups_pending" in existing_result.output
    assert "source=.ai/questionnaire.yaml" in existing_result.output
    assert "count=2" in existing_result.output
    assert "detail=confirm:scan-followup:test-evidence" in existing_result.output
    assert "运行 `review-human-input`" in existing_result.output
    assert "resolved / reopened" in existing_result.output


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
    team_guidance_index = result.output.index("建议优先补充这些隐性约束")
    team_prompt_index = result.output.index("可以输入一段规则说明")
    team_understanding_index = result.output.index("团队规则理解")
    team_impact_index = result.output.index("团队规则影响")
    candidate_review_index = result.output.index("建议生成的规则")
    assert team_guidance_index < team_prompt_index < team_understanding_index < team_impact_index < candidate_review_index
    team_prompt = result.output[team_guidance_index:team_prompt_index]
    assert "架构边界 / 模块分层" in team_prompt
    assert "测试策略 / 必跑验证" in team_prompt
    assert "安全合规 / 数据权限" in team_prompt
    assert "发布回滚 / 环境限制" in team_prompt
    assert "禁止修改 / 只读区域" in team_prompt
    team_summary = result.output[team_understanding_index:candidate_review_index]
    assert "Controller 只能调用 Service" in team_summary
    assert "配置变更必须说明回滚方式" in team_summary
    assert "interaction-decisions.yaml" in team_summary
    assert "project-context.md" in team_summary
    assert "human-input-needed.md" in team_summary
    assert "不会被当作扫描事实" in team_summary
    preview = result.output[result.output.index("写入前 Harness 设计预览") : result.output.index("\n最终确认\n")]
    assert "团队规则约束" in preview
    assert "Controller 只能调用 Service" in preview
    assert "配置变更必须说明回滚方式" in preview
    assert "Guides" in preview
    assert "human-input-needed" in preview
    assert "不直接修改正式 workflow routing policy" in preview
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["scan_confirmation"]["status"] == "amended"
    assert "批处理入口" in decisions["scan_confirmation"]["notes"][0]
    assert "Controller 只能调用 Service" in decisions["context_confirmation"]["inline_contexts"][0]
    assert decisions["context_confirmation"]["impact_scopes"] == [
        "interaction_decisions",
        "project_context",
        "human_input_needed",
        "guide_context",
        "review_only_team_context",
    ]
    assert decisions["context_confirmation"]["review_status"] == "pending_harness_maintainer_review"
    assert decisions["context_confirmation"]["policy_effect"] == "context_only_no_direct_policy_change"
    config = yaml.safe_load((repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8"))
    routing_text = yaml.safe_dump(config["workflow_routing"], allow_unicode=True)
    assert "Controller 只能调用 Service" not in routing_text
    assert "配置变更必须说明回滚方式" not in routing_text
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
    workflow_prompt_index = result.output.index("如果工作流还有补充说明")
    workflow_understanding_index = result.output.index("Workflow 补充理解")
    workflow_impact_index = result.output.index("Workflow 补充影响")
    maturity_preview_index = result.output.index("当前 Harness 成熟度初评")
    assert workflow_prompt_index < workflow_understanding_index < workflow_impact_index < maturity_preview_index
    workflow_summary = result.output[workflow_understanding_index:maturity_preview_index]
    assert "bugfix 工作流适合缺陷修复" in workflow_summary
    assert "interaction-decisions.yaml" in workflow_summary
    assert "project-context.md" in workflow_summary
    assert "human-input-needed.md" in workflow_summary
    assert "review-only" in workflow_summary
    assert "不直接修改正式 workflow routing policy" in workflow_summary
    preview = result.output[result.output.index("写入前 Harness 设计预览") : result.output.index("\n最终确认\n")]
    assert "Workflow 补充约束" in preview
    assert "bugfix 工作流适合缺陷修复" in preview
    assert "review-only" in preview
    assert "不直接修改正式 workflow routing policy" in preview
    final_summary = result.output[result.output.index("最终确认"):]
    assert "已吸收的用户补充" in final_summary
    assert "补充影响" in final_summary
    assert "批处理入口" in final_summary
    assert "Controller 只能调用 Service" in final_summary
    assert "bugfix 工作流适合缺陷修复" in final_summary
    assert "影响 Guides 与写入前成熟度预览" in final_summary
    assert "影响团队上下文 Guide 与 human-input-needed" in final_summary
    assert "影响 Workflow 说明与后续人工确认记录" in final_summary
    completion_summary = result.output[result.output.index("== 初始化完成 ==") :]
    completion_next_steps = completion_summary[completion_summary.index("建议下一步：") : completion_summary.index("\n\nBenchmark 健康度：")]
    assert "1. 先运行 `harness-builder-agent benchmark --repo" in completion_next_steps
    assert "2. 处理 `.ai/human-input-needed.md#处理方式` 中的待确认问题" in completion_next_steps
    assert "本次吸收的用户补充" in completion_summary
    assert "批处理入口" in completion_summary
    assert "Controller 只能调用 Service" in completion_summary
    assert "bugfix 工作流适合缺陷修复" in completion_summary
    assert ".ai/interaction-decisions.yaml" in completion_summary
    assert "团队规则和 Workflow 补充不会被伪装成扫描事实或正式 routing policy" in completion_summary

    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert "批处理入口" in decisions["scan_confirmation"]["notes"][0]
    assert "Controller 只能调用 Service" in decisions["context_confirmation"]["inline_contexts"][0]
    assert decisions["context_confirmation"]["impact_scopes"] == [
        "interaction_decisions",
        "project_context",
        "human_input_needed",
        "guide_context",
        "review_only_team_context",
    ]
    assert decisions["context_confirmation"]["review_status"] == "pending_harness_maintainer_review"
    assert decisions["context_confirmation"]["policy_effect"] == "context_only_no_direct_policy_change"
    assert "bugfix 工作流适合缺陷修复" in decisions["workflow_confirmation"]["notes"][0]
    assert decisions["workflow_confirmation"]["impact_scopes"] == [
        "interaction_decisions",
        "project_context",
        "human_input_needed",
        "review_only_workflow_note",
    ]
    assert decisions["workflow_confirmation"]["review_status"] == "pending_harness_maintainer_review"
    assert decisions["workflow_confirmation"]["routing_policy_effect"] == "review_only_no_direct_policy_change"
    config = yaml.safe_load((repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8"))
    routing_text = yaml.safe_dump(config["workflow_routing"], allow_unicode=True)
    assert "bugfix 工作流适合缺陷修复" not in routing_text
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    human_input = (repo / ".ai" / "human-input-needed.md").read_text(encoding="utf-8")
    assert "批处理入口" in project_context
    assert "Controller 只能调用 Service" in project_context
    assert "bugfix 工作流适合缺陷修复" in project_context
    assert "批处理入口" in human_input
    assert "Controller 只能调用 Service" in human_input
    assert "bugfix 工作流适合缺陷修复" in human_input


def test_guided_init_existing_harness_improve_creates_review_only_workflow_note_candidate(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    runner = CliRunner()

    init_result = runner.invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n"
            "\n"
            "\n\n\n\n"
            "支付权限变更应升级到 standard workflow。\n"
            "confirm\n"
        ),
    )
    assert init_result.exit_code == 0, init_result.output
    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness improve must not rescan while creating workflow note candidate")

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.assess_maturity.scan_repository", fail_scan)

    improve_result = runner.invoke(app, ["init", "--repo", str(repo)], input="improve\n")

    assert improve_result.exit_code == 0, improve_result.output
    _assert_formal_assets_unchanged(repo, formal_before)
    candidates = ImprovementCandidateReport.model_validate(
        yaml.safe_load((repo / ".ai" / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    )
    workflow_candidate = next(item for item in candidates.candidates if item.id == "interaction-workflow-note-review")
    assert workflow_candidate.candidate_type == "workflow_policy_update"
    assert workflow_candidate.suggested_target == ".ai/harness-config.yaml"
    assert workflow_candidate.human_confirmation_required is True
    assert workflow_candidate.target_dimension == "workflow"
    assert workflow_candidate.source_next_step == "workflow-note-review"
    assert ".ai/interaction-decisions.yaml" in workflow_candidate.evidence_sources
    assert ".ai/human-input-needed.md" in workflow_candidate.evidence_sources
    assert any("支付权限变更应升级到 standard workflow" in item for item in workflow_candidate.evidence)

    config = yaml.safe_load((repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8"))
    routing_text = yaml.safe_dump(config["workflow_routing"], allow_unicode=True)
    assert "支付权限变更应升级到 standard workflow" not in routing_text
    pending = (repo / ".ai" / "experience" / "pending-improvements.md").read_text(encoding="utf-8")
    assert "interaction-workflow-note-review" in pending


def test_guided_init_workflow_note_self_improve_creates_review_only_workflow_policy_candidate(
    tmp_path: Path, monkeypatch
):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    runner = CliRunner()

    init_result = runner.invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n"
            "\n"
            "\n\n\n\n"
            "支付权限变更应升级到 standard workflow。\n"
            "confirm\n"
        ),
    )
    assert init_result.exit_code == 0, init_result.output
    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness self-improve must not rescan while reviewing workflow notes")

    def fake_review(score, evidence_pack, candidates, experience_summary=None):
        assert any(candidate.id == "interaction-workflow-note-review" for candidate in candidates.candidates)
        assert ".ai/interaction-decisions.yaml" in evidence_pack.maturity_inputs
        return MaturityReviewReport(
            summary="Workflow note should become a review-only routing policy draft.",
            candidate_reviews=[
                {
                    "candidate_id": "interaction-workflow-note-review",
                    "decision": "support",
                    "rationale": "The note is grounded in guided init interaction evidence.",
                    "risks": ["Routing policy changes require maintainer review."],
                    "suggested_acceptance_checks": ["Benchmark content:workflow-routing-policy passes."],
                    "evidence_sources": [".ai/interaction-decisions.yaml"],
                }
            ],
            missing_candidates=[],
            global_risks=[],
        )

    def fake_assets(score, evidence_pack, improvement_candidates, maturity_review, experience_summary=None):
        assert any(candidate.id == "interaction-workflow-note-review" for candidate in improvement_candidates.candidates)
        review = next(item for item in maturity_review.candidate_reviews if item.candidate_id == "interaction-workflow-note-review")
        assert review.decision == "support"
        return AssetCandidateReport(
            candidates=[
                {
                    "id": "workflow-standard-payment-permission",
                    "kind": "workflow_policy",
                    "source_candidate_id": "interaction-workflow-note-review",
                    "source_review_decision": "support",
                    "suggested_path": ".ai/harness-config.yaml",
                    "title": "Escalate payment permission changes",
                    "rationale": "The reviewed Workflow note supports a routing policy candidate.",
                    "draft_content": "Review-only routing policy update for payment permission changes.",
                    "workflow_policy_patch": {
                        "schema_version": "1.0",
                        "operation": "upsert_routing_rule",
                        "target": "workflow_routing.rules",
                        "rule": {
                            "id": "standard-escalation",
                            "selected_workflow": "standard",
                            "rationale": "Escalate high-risk, cross-module, security, low-coverage, and payment permission changes.",
                            "task_type_hints": ["feature", "permission"],
                            "triggers": [
                                "unclear_impact_scope",
                                "high_risk_module",
                                "cross_module_design",
                                "security_or_permission",
                                "insufficient_sensor_coverage",
                                "payment_permission_change",
                            ],
                            "required_guides": [".ai/guides/project-context.md", ".ai/guides/architecture.md"],
                            "required_sensors": [".ai/sensors/verification.md"],
                            "human_confirmation_required": True,
                        },
                    },
                    "evidence_sources": [".ai/interaction-decisions.yaml", ".ai/human-input-needed.md"],
                    "acceptance_checks": ["Benchmark content:workflow-routing-policy passes."],
                    "risk_level": "high",
                    "review_status": "pending_harness_maintainer_review",
                }
            ]
        )

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.assess_maturity.scan_repository", fail_scan)
    monkeypatch.setattr("harness_builder_agent.tools.review_maturity.review_maturity_with_llm", fake_review)
    monkeypatch.setattr(
        "harness_builder_agent.tools.generate_asset_candidates.generate_asset_candidates_with_llm",
        fake_assets,
    )

    result = runner.invoke(app, ["init", "--repo", str(repo)], input="self-improve\n")

    assert result.exit_code == 0, result.output
    _assert_formal_assets_unchanged(repo, formal_before)
    assert not (repo / ".ai" / "task-runs").exists()
    asset_report = AssetCandidateReport.model_validate(
        yaml.safe_load((repo / ".ai" / "review" / "asset-candidates.yaml").read_text(encoding="utf-8"))
    )
    workflow_candidate = next(item for item in asset_report.candidates if item.id == "workflow-standard-payment-permission")
    assert workflow_candidate.kind == "workflow_policy"
    assert workflow_candidate.source_candidate_id == "interaction-workflow-note-review"
    assert workflow_candidate.source_review_decision == "support"
    assert workflow_candidate.suggested_path == ".ai/harness-config.yaml"
    assert workflow_candidate.workflow_policy_patch is not None
    assert "payment_permission_change" in workflow_candidate.workflow_policy_patch.rule.triggers
    assert ".ai/interaction-decisions.yaml" in workflow_candidate.evidence_sources
    package = SelfImprovePackageManifest.model_validate(
        yaml.safe_load((repo / ".ai" / "review" / "self-improve-package.yaml").read_text(encoding="utf-8"))
    )
    assert package.candidate_counts.workflow_policy_candidates == 1
    assert package.review_status == "pending_harness_maintainer_review"


def test_review_human_input_command_marks_scan_followup_resolved_without_overwriting_formal_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    runner = CliRunner()

    init_result = runner.invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n"
            "command=unit_test|mvn test|test|hard|pom.xml|high\n"
            "\n\n\n\n"
            "\n"
            "confirm\n"
        ),
    )
    assert init_result.exit_code == 0, init_result.output
    formal_before = _formal_asset_snapshot(repo)

    result = runner.invoke(
        app,
        [
            "review-human-input",
            "--repo",
            str(repo),
            "--interaction-id",
            "confirm:scan-followup:test-evidence",
            "--decision",
            "resolved",
            "--rationale",
            "Maintainer confirmed mvn test is the stable test gate.",
        ],
    )

    assert result.exit_code == 0, result.output
    _assert_formal_assets_unchanged(repo, formal_before)
    questionnaire = Questionnaire.model_validate(
        yaml.safe_load((repo / ".ai" / "questionnaire.yaml").read_text(encoding="utf-8"))
    )
    question = next(item for item in questionnaire.questions if item.interaction_id == "confirm:scan-followup:test-evidence")
    assert question.response_status == "reviewed_resolved_by_harness_maintainer"
    governance = yaml.safe_load((repo / ".ai" / "review" / "human-input-governance.yaml").read_text(encoding="utf-8"))
    assert governance["decisions"][0]["interaction_id"] == "confirm:scan-followup:test-evidence"
    assert governance["decisions"][0]["decision"] == "resolved"
    human_input = (repo / ".ai" / "human-input-needed.md").read_text(encoding="utf-8")
    assert "response_status=reviewed_resolved_by_harness_maintainer" in human_input

    existing_result = runner.invoke(app, ["init", "--repo", str(repo)], input="exit\n")
    assert existing_result.exit_code == 0, existing_result.output
    assert "human_input_scan_followups_resolved=1" in existing_result.output


def test_guided_init_existing_harness_can_review_human_input_without_overwriting_formal_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    runner = CliRunner()

    init_result = runner.invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n"
            "command=unit_test|mvn test|test|hard|pom.xml|high\n"
            "\n\n\n\n"
            "\n"
            "confirm\n"
        ),
    )
    assert init_result.exit_code == 0, init_result.output
    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness human-input review must reuse existing Harness state, not rescan")

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = runner.invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "review-human-input\n"
            "\n"
            "resolved\n"
            "Maintainer confirmed mvn test is the stable test gate.\n"
            "lead-reviewer\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "已存在 Harness" in result.output
    assert "review-human-input" in result.output
    assert "human-input 治理决策已记录" in result.output
    assert "confirm:scan-followup:test-evidence" in result.output
    assert "resolved" in result.output
    _assert_formal_assets_unchanged(repo, formal_before)
    assert not (repo / ".ai" / "task-runs").exists()

    questionnaire = Questionnaire.model_validate(
        yaml.safe_load((repo / ".ai" / "questionnaire.yaml").read_text(encoding="utf-8"))
    )
    question = next(item for item in questionnaire.questions if item.interaction_id == "confirm:scan-followup:test-evidence")
    assert question.response_status == "reviewed_resolved_by_harness_maintainer"
    governance = yaml.safe_load((repo / ".ai" / "review" / "human-input-governance.yaml").read_text(encoding="utf-8"))
    assert governance["decisions"][0]["interaction_id"] == "confirm:scan-followup:test-evidence"
    assert governance["decisions"][0]["decision"] == "resolved"
    assert governance["decisions"][0]["reviewer"] == "lead-reviewer"
    human_input = (repo / ".ai" / "human-input-needed.md").read_text(encoding="utf-8")
    assert "response_status=reviewed_resolved_by_harness_maintainer" in human_input
    governance_md = (repo / ".ai" / "review" / "human-input-governance.md").read_text(encoding="utf-8")
    assert "## Review Boundary" in governance_md

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert "scan" not in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "review-human-input"
    assert trace["summary"]["interaction_id"] == "confirm:scan-followup:test-evidence"
    assert trace["summary"]["decision"] == "resolved"
    assert trace["summary"]["reviewer"] == "lead-reviewer"
    artifacts = _latest_init_artifacts(repo)
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/questionnaire.yaml" in artifact_paths
    assert ".ai/human-input-needed.md" in artifact_paths
    assert ".ai/review/human-input-governance.yaml" in artifact_paths
    assert ".ai/review/human-input-governance.md" in artifact_paths


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
            "frontend 还包含批处理入口; module=frontend|frontend|frontend; command=frontend_test|npm test|test|hard|frontend/package.json|high; risk=frontend/package.json|前端依赖需要单独确认\n"
            "\n\n\n\n"
            "\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    prompt_index = result.output.index("你的补充或修正")
    immediate_summary_index = result.output.index("扫描补充理解")
    impact_index = result.output.index("扫描补充影响")
    team_rules_index = result.output.index("\n团队规则")
    assert prompt_index < immediate_summary_index < impact_index < team_rules_index
    immediate_summary = result.output[immediate_summary_index:team_rules_index]
    assert "frontend 还包含批处理入口" in immediate_summary
    assert "frontend" in immediate_summary
    assert "npm test" in immediate_summary
    assert "frontend/package.json" in immediate_summary
    assert "前端依赖需要单独确认" in immediate_summary
    assert "成熟度缺口判断" in immediate_summary
    assert "Guides" in immediate_summary
    assert "Sensors" in immediate_summary
    assert "Workflow 升级" in immediate_summary
    assert "human-input-needed" in immediate_summary
    prewrite_preview = result.output[result.output.index("写入前 Harness 设计预览") : result.output.index("\n最终确认\n")]
    assert "扫描补充约束" in prewrite_preview
    assert "frontend 还包含批处理入口" in prewrite_preview
    assert "`frontend`（frontend，frontend）" in prewrite_preview
    assert "`npm test`，gate=hard，source=`frontend/package.json`" in prewrite_preview
    assert "`frontend/package.json`，前端依赖需要单独确认" in prewrite_preview
    assert "影响 project inventory、command catalog、risk hints、Guides、Sensors、Workflow 升级和人工确认" in prewrite_preview
    assert "不会被伪装成已验证扫描事实" in prewrite_preview
    assert "risk_area:frontend/package.json" in prewrite_preview
    assert "风险路径 `frontend/package.json` 会升级到 standard 工作流" in prewrite_preview
    assert "将生成的 Workflow Skills" in prewrite_preview
    assert "`lightweight`：`.ai/skills/lightweight/SKILL.md`" in prewrite_preview
    assert "`bugfix`：`.ai/skills/bugfix/SKILL.md`" in prewrite_preview
    assert "`standard`：`.ai/skills/standard/SKILL.md`" in prewrite_preview
    assert "路由规则：`standard-escalation`" in prewrite_preview
    assert "引用 Sensors：`.ai/sensors/verification.md`, `.ai/sensors/test-strategy.md`" in prewrite_preview
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text(encoding="utf-8"))
    assert {"name": "frontend", "path": "frontend", "kind": "frontend"} in inventory["modules"]
    assert {"path": "frontend/package.json", "reason": "前端依赖需要单独确认"} in inventory["stack_extensions"]["risk_areas"]
    assert inventory["stack_extensions"]["human_overrides"]["modules"][0]["path"] == "frontend"
    assert inventory["stack_extensions"]["human_overrides"]["risk_areas"][0]["path"] == "frontend/package.json"
    assert any("frontend 还包含批处理入口" in note for note in inventory["stack_extensions"]["human_overrides"]["scan_notes"])
    catalog = yaml.safe_load((repo / ".ai" / "command-catalog.yaml").read_text(encoding="utf-8"))
    assert any(command["id"] == "frontend_test" and command["command"] == "npm test" for command in catalog["commands"])
    config = yaml.safe_load((repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8"))
    standard = next(rule for rule in config["workflow_routing"]["rules"] if rule["id"] == "standard-escalation")
    assert "risk_area:frontend/package.json" in standard["triggers"]
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["scan_confirmation"]["status"] == "amended"
    assert decisions["scan_confirmation"]["modules"] == [{"path": "frontend", "kind": "frontend", "name": "frontend"}]
    assert decisions["scan_confirmation"]["commands"][0]["id"] == "frontend_test"
    assert decisions["scan_confirmation"]["commands"][0]["source"] == "frontend/package.json"
    assert decisions["scan_confirmation"]["risk_areas"] == [
        {"path": "frontend/package.json", "reason": "前端依赖需要单独确认"}
    ]
    assert decisions["scan_confirmation"]["impact_scopes"] == [
        "interaction_decisions",
        "project_context",
        "human_input_needed",
        "maturity_preview",
        "project_inventory",
        "command_catalog",
        "sensors",
        "workflow_routing_review",
    ]
    assert decisions["scan_confirmation"]["review_status"] == "pending_harness_maintainer_review"
    assert decisions["scan_confirmation"]["fact_effect"] == "user_supplied_correction_review_required"
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "frontend" in project_context
    assert "frontend/package.json" in project_context
    assert "前端依赖需要单独确认" in project_context
    assert "npm test" in project_context
    verification = (repo / ".ai" / "sensors" / "verification.md").read_text(encoding="utf-8")
    assert "frontend/package.json" in verification
    assert "前端依赖需要单独确认" in verification
    assert "npm test" in verification
    init_summary = (repo / ".ai" / "init-summary.md").read_text(encoding="utf-8")
    assert "frontend" in init_summary
    assert "frontend/package.json" in init_summary
    assert "前端依赖需要单独确认" in init_summary
    assert "npm test" in init_summary


def test_guided_init_explains_invalid_structured_scan_correction_does_not_update_catalog(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n"
            "command=bad_test|npm test|test|hard\n"
            "\n\n\n\n"
            "\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    immediate_summary = result.output[result.output.index("扫描补充理解") : result.output.index("\n团队规则")]
    assert "结构化 command 片段未解析：command=bad_test|npm test|test|hard" in immediate_summary
    assert "未进入 command catalog，只作为自然语言补充保留" in immediate_summary
    assert (
        "可用格式：command=ID|命令|类型(build/test/lint/typecheck/other)|gate(hard/soft)|来源|置信度(low/medium/high)"
        in immediate_summary
    )
    catalog = yaml.safe_load((repo / ".ai" / "command-catalog.yaml").read_text(encoding="utf-8"))
    assert all(command["id"] != "bad_test" for command in catalog["commands"])
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["scan_confirmation"]["commands"] == []
    assert any("未进入 command catalog" in note for note in decisions["scan_confirmation"]["notes"])
    assert any("可用格式：command=ID|命令|类型(build/test/lint/typecheck/other)" in note for note in decisions["scan_confirmation"]["notes"])


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
    assert "成熟度影响：补齐 Guides 上下文" in result.output
    assert "成熟度影响：补齐 Guides 上下文、Risk Control 风险控制" in result.output
    assert "成熟度影响：补齐 Sensors 验证、Verification 验证成熟度" in result.output
    assert "审查边界：保持 review-only；接受只记录确认，不会自动写入正式 Guide 或 Sensor。" in result.output
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    by_id = {item["candidate_id"]: item for item in decisions["candidate_decisions"]}
    assert by_id["llm-guide-architecture-001"]["decision"] == "accepted"
    assert by_id["llm-guide-risk-001"]["decision"] == "rejected"
    assert by_id["llm-sensor-command-001"]["decision"] == "edited"
    candidate_report = yaml.safe_load((repo / ".ai" / "experience" / "weapon-library-candidates.yaml").read_text(encoding="utf-8"))
    candidate_by_id = {item["id"]: item for item in candidate_report["candidates"]}
    assert candidate_by_id["llm-guide-architecture-001"]["status"] == "confirmed"
    assert candidate_by_id["llm-guide-architecture-001"]["maturity_dimensions"] == ["guides"]
    assert candidate_by_id["llm-guide-risk-001"]["status"] == "rejected"
    assert candidate_by_id["llm-guide-risk-001"]["maturity_dimensions"] == ["guides", "risk_control"]
    assert candidate_by_id["llm-guide-risk-001"]["maturity_impact_summary"] == "补齐 Guides 上下文、Risk Control 风险控制。"
    assert candidate_by_id["llm-sensor-command-001"]["decision_notes"] == "测试命令需要先确认 CI 稳定性。"
    assert candidate_by_id["llm-sensor-command-001"]["maturity_dimensions"] == ["sensors", "verification_sophistication"]
    assert candidate_by_id["llm-sensor-command-001"]["review_boundary"] == "review_only_no_formal_asset_change"


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
    assert "团队规则返回修改" in result.output
    rules_revision = result.output[
        result.output.index("团队规则返回修改") : result.output.index("\n团队规则理解", result.output.index("团队规则返回修改"))
    ]
    assert "新输入会替换上一版团队规则" in rules_revision
    assert "直接回车会清空上一版团队规则" in rules_revision
    assert "初始规则需要修改" in rules_revision
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["context_confirmation"]["inline_contexts"] == ["最终团队规则：配置变更必须说明影响环境。"]
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    assert "最终团队规则" in project_context
    assert "初始规则需要修改" not in project_context


def test_guided_init_final_summary_back_to_team_rules_can_clear_previous_rules(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n\n"
            "初始规则需要清空。\n"
            "\n\n\n"
            "\n"
            "back\n"
            "rules\n"
            "\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "团队规则返回修改" in result.output
    assert "直接回车会清空上一版团队规则" in result.output
    assert "团队规则已清空" in result.output
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["context_confirmation"]["inline_contexts"] == []
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    human_input = (repo / ".ai" / "human-input-needed.md").read_text(encoding="utf-8")
    assert "初始规则需要清空" not in project_context
    assert "初始规则需要清空" not in human_input


def test_guided_init_final_summary_can_go_back_to_workflow_note(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n\n\n"
            "\n\n\n"
            "初始 Workflow 说明需要修改。\n"
            "back\n"
            "workflow\n"
            "最终 Workflow 说明：bugfix 只用于缺陷修复。\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "返回修改" in result.output
    assert "workflow/工作流=Workflow补充" in result.output
    assert "Workflow 补充返回修改" in result.output
    workflow_revision = result.output[
        result.output.index("Workflow 补充返回修改") : result.output.index("\n推荐工作流", result.output.index("Workflow 补充返回修改"))
    ]
    assert "新输入会替换上一版 Workflow 补充" in workflow_revision
    assert "直接回车会清空上一版 Workflow 补充" in workflow_revision
    assert "初始 Workflow 说明需要修改" in workflow_revision
    assert result.output.count("Workflow 补充理解") == 2
    final_preview = result.output[result.output.rindex("写入前 Harness 设计预览") : result.output.rindex("\n最终确认\n")]
    assert "最终 Workflow 说明：bugfix 只用于缺陷修复" in final_preview
    assert "初始 Workflow 说明需要修改" not in final_preview
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["workflow_confirmation"]["notes"] == ["最终 Workflow 说明：bugfix 只用于缺陷修复。"]
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    human_input = (repo / ".ai" / "human-input-needed.md").read_text(encoding="utf-8")
    assert "最终 Workflow 说明：bugfix 只用于缺陷修复" in project_context
    assert "最终 Workflow 说明：bugfix 只用于缺陷修复" in human_input
    assert "初始 Workflow 说明需要修改" not in project_context
    assert "初始 Workflow 说明需要修改" not in human_input


def test_guided_init_final_summary_back_to_workflow_can_clear_previous_note(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n\n\n"
            "\n\n\n"
            "初始 Workflow 说明需要清空。\n"
            "back\n"
            "workflow\n"
            "\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "Workflow 补充返回修改" in result.output
    assert "直接回车会清空上一版 Workflow 补充" in result.output
    assert "Workflow 补充已清空" in result.output
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert decisions["workflow_confirmation"]["notes"] == []
    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    human_input = (repo / ".ai" / "human-input-needed.md").read_text(encoding="utf-8")
    config = yaml.safe_load((repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8"))
    routing_text = yaml.safe_dump(config["workflow_routing"], allow_unicode=True)
    assert "初始 Workflow 说明需要清空" not in project_context
    assert "初始 Workflow 说明需要清空" not in human_input
    assert "初始 Workflow 说明需要清空" not in routing_text


def test_guided_init_final_summary_back_to_scan_replaces_previous_corrections(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n"
            "module=legacy|backend|legacy; command=legacy_test|make legacy-test|test|hard|legacy/Makefile|high; risk=legacy|旧风险\n"
            "\n"
            "\n\n\n"
            "\n"
            "back\n"
            "scan\n"
            "module=final|backend|final; command=final_test|make final-test|test|hard|Makefile|high; risk=final|最终风险\n"
            "\n\n\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "扫描补充替换结果" in result.output
    replacement_preview = result.output[
        result.output.index("扫描补充替换结果") : result.output.index("\n当前 Harness 成熟度初评", result.output.index("扫描补充替换结果"))
    ]
    assert "上一版补充" in replacement_preview
    assert "legacy" in replacement_preview
    assert "legacy_test" in replacement_preview
    assert "旧风险" in replacement_preview
    assert "当前生效补充" in replacement_preview
    assert "final" in replacement_preview
    assert "final_test" in replacement_preview
    assert "最终风险" in replacement_preview
    assert "最终写入只会使用当前生效补充" in replacement_preview
    assert "上一版补充不会进入 project inventory、command catalog、Guides、Sensors 或 init summary" in replacement_preview
    final_preview = result.output[result.output.rindex("写入前 Harness 设计预览") : result.output.rindex("\n最终确认\n")]
    assert "扫描补充约束" in final_preview
    assert "`final`（backend，final）" in final_preview
    assert "`make final-test`，gate=hard，source=`Makefile`" in final_preview
    assert "`final`，最终风险" in final_preview
    assert "legacy" not in final_preview
    assert "旧风险" not in final_preview
    assert "make legacy-test" not in final_preview
    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text(encoding="utf-8"))
    assert {"name": "final", "path": "final", "kind": "backend"} in inventory["modules"]
    assert {"name": "legacy", "path": "legacy", "kind": "backend"} not in inventory["modules"]
    assert {"path": "final", "reason": "最终风险"} in inventory["stack_extensions"]["risk_areas"]
    assert {"path": "legacy", "reason": "旧风险"} not in inventory["stack_extensions"]["risk_areas"]
    assert inventory["stack_extensions"]["human_overrides"]["modules"] == [
        {"path": "final", "kind": "backend", "name": "final"}
    ]
    assert inventory["stack_extensions"]["human_overrides"]["risk_areas"] == [{"path": "final", "reason": "最终风险"}]

    catalog = yaml.safe_load((repo / ".ai" / "command-catalog.yaml").read_text(encoding="utf-8"))
    command_ids = {command["id"] for command in catalog["commands"]}
    assert "final_test" in command_ids
    assert "legacy_test" not in command_ids
    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert any("final" in note for note in decisions["scan_confirmation"]["notes"])
    assert all("legacy" not in note for note in decisions["scan_confirmation"]["notes"])

    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    verification = (repo / ".ai" / "sensors" / "verification.md").read_text(encoding="utf-8")
    init_summary = (repo / ".ai" / "init-summary.md").read_text(encoding="utf-8")
    for content in (project_context, verification, init_summary):
        assert "final" in content
        assert "最终风险" in content
        assert "legacy" not in content
        assert "旧风险" not in content
        assert "make legacy-test" not in content
    assert "make final-test" in verification


def test_guided_init_back_to_scan_reenters_candidate_review_for_refreshed_candidates(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n"
            "\n"
            "\n"
            "a\n"
            "r\n"
            "e\n"
            "旧候选备注不应进入最终产物。\n"
            "\n"
            "back\n"
            "scan\n"
            "risk=src/main/resources/application.yml|最终风险\n"
            "a\n"
            "r\n"
            "e\n"
            "新候选备注应该进入最终产物。\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "候选项已根据新的扫描状态刷新" in result.output
    assert "上一轮候选审查决策已清空" in result.output
    assert "接下来将按当前扫描状态重新审查候选" in result.output
    assert result.output.count("逐项审查模型候选") == 2
    final_summary = result.output[result.output.rindex("\n最终确认\n") : result.output.index("输入 confirm/确认", result.output.rindex("\n最终确认\n"))]
    assert "候选决策：确认 1 条，拒绝 1 条，备注 1 条，保持候选 0 条" in final_summary

    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    by_id = {item["candidate_id"]: item for item in decisions["candidate_decisions"]}
    assert by_id["llm-guide-architecture-001"]["decision"] == "accepted"
    assert by_id["llm-guide-risk-001"]["decision"] == "rejected"
    assert by_id["llm-sensor-command-001"]["decision"] == "edited"
    assert by_id["llm-sensor-command-001"]["notes"] == "新候选备注应该进入最终产物。"
    assert all("旧候选备注" not in item.get("notes", "") for item in decisions["candidate_decisions"])

    candidate_report = yaml.safe_load((repo / ".ai" / "experience" / "weapon-library-candidates.yaml").read_text(encoding="utf-8"))
    statuses = {item["id"]: item["status"] for item in candidate_report["candidates"]}
    assert statuses["llm-guide-architecture-001"] == "confirmed"
    assert statuses["llm-guide-risk-001"] == "rejected"
    assert statuses["llm-sensor-command-001"] == "candidate"
    assert all("旧候选备注" not in item.get("decision_notes", "") for item in candidate_report["candidates"])


def test_guided_init_final_summary_back_to_scan_can_clear_previous_corrections(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "\n"
            "module=legacy|backend|legacy; command=legacy_test|make legacy-test|test|hard|legacy/Makefile|high; risk=legacy|旧风险\n"
            "\n"
            "\n\n\n"
            "\n"
            "back\n"
            "scan\n"
            "\n"
            "\n\n\n"
            "confirm\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "扫描补充返回修改" in result.output
    assert "新输入会替换上一版扫描补充" in result.output
    assert "直接回车会清空上一版补充" in result.output
    assert "扫描补充已清空" in result.output

    inventory = json.loads((repo / ".ai" / "project-inventory.json").read_text(encoding="utf-8"))
    assert {"name": "legacy", "path": "legacy", "kind": "backend"} not in inventory["modules"]
    assert {"path": "legacy", "reason": "旧风险"} not in inventory["stack_extensions"].get("risk_areas", [])
    assert "human_overrides" not in inventory["stack_extensions"]

    catalog = yaml.safe_load((repo / ".ai" / "command-catalog.yaml").read_text(encoding="utf-8"))
    command_ids = {command["id"] for command in catalog["commands"]}
    assert "legacy_test" not in command_ids

    decisions = yaml.safe_load((repo / ".ai" / "interaction-decisions.yaml").read_text(encoding="utf-8"))
    assert all("legacy" not in note for note in decisions["scan_confirmation"]["notes"])

    project_context = (repo / ".ai" / "guides" / "project-context.md").read_text(encoding="utf-8")
    verification = (repo / ".ai" / "sensors" / "verification.md").read_text(encoding="utf-8")
    init_summary = (repo / ".ai" / "init-summary.md").read_text(encoding="utf-8")
    for content in (project_context, verification, init_summary):
        assert "legacy" not in content
        assert "旧风险" not in content
        assert "make legacy-test" not in content


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
    assert "维护状态摘要（Maintenance overview）" in result.output
    assert "质量门禁：尚未运行 benchmark；建议先运行菜单 `4` 的 `benchmark` 建立质量基线。" in result.output
    assert "Workflow 路由：default=`lightweight`，standard escalation 已启用" in result.output
    assert "优先动作：输入 `4` 运行 `benchmark`（reason=benchmark_not_run，source=.ai/benchmark-report.yaml）。" in result.output
    assert "审计明细（Audit signals）" in result.output
    assert result.output.index("维护建议（Maintenance triage guidance）") < result.output.index("质量门禁信号（Benchmark signals）")
    assert result.output.index("推荐动作快捷选择（Maintenance action shortcuts）") < result.output.index("质量门禁信号（Benchmark signals）")
    assert result.output.index("审计明细（Audit signals）") < result.output.index("质量门禁信号（Benchmark signals）")
    assert result.output.count("维护建议（Maintenance triage guidance）") == 1
    assert result.output.count("推荐动作快捷选择（Maintenance action shortcuts）") == 1
    assert "质量门禁信号（Benchmark signals）" in result.output
    assert "benchmark_failed_checks=not_available" in result.output
    assert "Workflow 路由信号（Workflow routing signals）" in result.output
    assert "routing_default=lightweight" in result.output
    assert "routing_rule_count=3" in result.output
    assert "standard_escalation=present" in result.output
    assert "standard_human_confirmation=true" in result.output
    assert "missing_hard_gate_trigger=" in result.output
    assert "经验 / 审查信号（Experience / review signals）" in result.output
    assert "维护优先级（Maintenance triage）" in result.output
    assert "top_action_1=benchmark" in result.output
    assert "reason=benchmark_not_run" in result.output
    assert "source=.ai/benchmark-report.yaml" in result.output
    assert "next=benchmark" in result.output
    assert "pending_improvements=" in result.output
    assert "asset_candidates=" in result.output
    assert "weapon_library_candidates=" in result.output
    assert "weapon_library_candidates_pending=" in result.output
    assert "weapon_candidate_maturity_dimensions=" in result.output
    assert "weapon_candidate_top=" in result.output
    assert "candidate_governance=" in result.output
    assert "maturity_reviews=" in result.output
    assert "workflow_recommendations=" in result.output
    assert "runtime_task_runs=" in result.output
    assert "self_improve_package=" in result.output
    assert "human_input_needed=" in result.output
    assert "human_input_questionnaire=present" in result.output
    assert "human_input_confirmations=" in result.output
    assert "human_input_scan_confirmations=" in result.output
    assert "human_input_first=confirm:" in result.output
    assert "human_input_action_entry=.ai/human-input-needed.md#处理方式" in result.output
    assert "schema_content_failed_checks=" in result.output
    assert "exit" in result.output
    assert "== 启动说明 ==" not in result.output
    assert "== 初始化完成 ==" not in result.output
    assert "本次已生成" not in result.output
    assert (repo / ".ai" / "project-inventory.json").read_text(encoding="utf-8") == inventory_before
    assert (repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8") == config_before
    assert (repo / ".ai" / "init-summary.md").read_text(encoding="utf-8") == summary_before

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert trace["summary"]["existing_harness_action"] == "exit"


def test_guided_init_existing_harness_can_exit_with_numbered_action(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output

    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("numbered existing Harness exit must not scan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="1\n")

    assert result.exit_code == 0, result.output
    assert "维护状态摘要（Maintenance overview）" in result.output
    assert "质量门禁：尚未运行 benchmark；建议先运行菜单 `4` 的 `benchmark` 建立质量基线。" in result.output
    assert "优先动作：输入 `4` 运行 `benchmark`（reason=benchmark_not_run，source=.ai/benchmark-report.yaml）。" in result.output
    assert "维护建议（Maintenance triage guidance）" in result.output
    assert "建议处理 1：先运行 `benchmark`" in result.output
    assert "推荐动作快捷选择（Maintenance action shortcuts）" in result.output
    assert "建议优先选择 1：输入 `4` 运行 `benchmark`" in result.output
    assert "1. exit" in result.output
    assert "2. assess" in result.output
    assert "7. review-human-input" in result.output
    assert "9. reinit" in result.output
    assert "human_input_questionnaire=present" in result.output
    assert "human_input_action_entry=.ai/human-input-needed.md#处理方式" in result.output
    _assert_formal_assets_unchanged(repo, formal_before)

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
    assert "== 初始化完成 ==" not in result.output
    assert "本次已生成" not in result.output
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


def test_guided_init_existing_harness_recommend_workflow_empty_task_preserves_action_failure(
    tmp_path: Path, monkeypatch
):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr(
        "harness_builder_agent.tools.interactive_init.scan_repository",
        lambda repo_path: _fake_scan(repo_path, "java-spring"),
    )
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness recommend-workflow failure must not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="recommend-workflow\n\n")

    assert result.exit_code != 0
    assert "recommend-workflow" in result.output
    assert "empty_task_brief" in result.output
    trace = _latest_init_trace(repo)
    assert trace["status"] == "failed"
    assert "existing-harness" in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "recommend-workflow"
    assert trace["summary"]["error"] == "empty_task_brief"
    assert not (repo / ".ai" / "task-runs").exists()


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


def test_guided_init_existing_harness_review_candidate_missing_report_records_action_failure(
    tmp_path: Path, monkeypatch
):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr(
        "harness_builder_agent.tools.interactive_init.scan_repository",
        lambda repo_path: _fake_scan(repo_path, "java-spring"),
    )
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness review-candidate failure must not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="review-candidate\n")

    assert result.exit_code != 0
    assert "asset-candidates.yaml" in result.output
    trace = _latest_init_trace(repo)
    assert trace["status"] == "failed"
    assert "existing-harness" in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "review-candidate"
    assert trace["summary"]["error"]
    assert "asset-candidates.yaml" in trace["summary"]["error"]
    assert not (repo / ".ai" / "task-runs").exists()


def test_guided_init_existing_harness_review_candidate_unknown_id_records_action_failure(
    tmp_path: Path, monkeypatch
):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr(
        "harness_builder_agent.tools.interactive_init.scan_repository",
        lambda repo_path: _fake_scan(repo_path, "java-spring"),
    )
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

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness review-candidate failure must not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="review-candidate\nmissing-candidate\n")

    assert result.exit_code != 0
    assert "unknown asset candidate id: missing-candidate" in result.output
    trace = _latest_init_trace(repo)
    assert trace["status"] == "failed"
    assert "existing-harness" in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "review-candidate"
    assert trace["summary"]["candidate_id"] == "missing-candidate"
    assert trace["summary"]["error"] == "unknown asset candidate id: missing-candidate"
    assert not (repo / ".ai" / "task-runs").exists()


def test_guided_init_existing_harness_can_review_initial_candidate_without_overwriting_formal_assets(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    ai = repo / ".ai"
    formal_before = _formal_asset_snapshot(repo)

    def fail_scan(_repo_path):
        raise AssertionError("guided initial candidate governance must reuse existing Harness state, not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input=(
            "10\n"
            "llm-guide-architecture-001\n"
            "accepted\n"
            "Maintainer confirmed the architecture signal remains useful.\n"
            "lead-reviewer\n"
        ),
    )

    assert result.exit_code == 0, result.output
    assert "review-initial-candidate" in result.output
    assert "初始候选治理决策已记录" in result.output
    assert "accepted" in result.output
    assert "formal_asset_changes=0" in result.output
    _assert_formal_assets_unchanged(repo, formal_before)
    assert not (ai / "task-runs").exists()

    candidate_report = yaml.safe_load((ai / "experience" / "weapon-library-candidates.yaml").read_text(encoding="utf-8"))
    candidates_by_id = {item["id"]: item for item in candidate_report["candidates"]}
    assert candidates_by_id["llm-guide-architecture-001"]["status"] == "confirmed"
    assert candidates_by_id["llm-guide-architecture-001"]["human_confirmation_required"] is False
    assert candidates_by_id["llm-guide-architecture-001"]["decision_notes"] == "Maintainer confirmed the architecture signal remains useful."

    governance = WeaponCandidateGovernanceLog.model_validate(
        yaml.safe_load((ai / "review" / "weapon-candidate-governance.yaml").read_text(encoding="utf-8"))
    )
    latest = governance.decisions[-1]
    assert latest.candidate_id == "llm-guide-architecture-001"
    assert latest.candidate_type == "guide"
    assert latest.decision == "accepted"
    assert latest.new_status == "confirmed"
    assert latest.reviewer == "lead-reviewer"
    assert "## Review Boundary" in (ai / "review" / "weapon-candidate-governance.md").read_text(encoding="utf-8")
    assert "status=`confirmed`" in (ai / "review" / "llm-enhancement-candidates.md").read_text(encoding="utf-8")

    trace = _latest_init_trace(repo)
    assert trace["command"] == "init"
    assert trace["status"] == "completed"
    assert "scan" not in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "review-initial-candidate"
    assert trace["summary"]["candidate_id"] == "llm-guide-architecture-001"
    assert trace["summary"]["decision"] == "accepted"
    assert trace["summary"]["new_status"] == "confirmed"
    artifacts = _latest_init_artifacts(repo)
    artifact_paths = {item["path"] for item in artifacts["artifacts"]}
    assert ".ai/experience/weapon-library-candidates.yaml" in artifact_paths
    assert ".ai/review/weapon-candidate-governance.yaml" in artifact_paths
    assert ".ai/review/weapon-candidate-governance.md" in artifact_paths
    assert ".ai/review/llm-enhancement-candidates.md" in artifact_paths


def test_guided_init_existing_harness_review_initial_candidate_missing_report_preserves_action_failure(
    tmp_path: Path, monkeypatch
):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr(
        "harness_builder_agent.tools.interactive_init.scan_repository",
        lambda repo_path: _fake_scan(repo_path, "java-spring"),
    )
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output
    (repo / ".ai" / "experience" / "weapon-library-candidates.yaml").unlink()

    def fail_scan(_repo_path):
        raise AssertionError("guided initial candidate failure must reuse existing Harness state, not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="review-initial-candidate\n")

    assert result.exit_code != 0
    assert "review-initial-candidate" in result.output
    assert "weapon-library-candidates.yaml" in result.output
    trace = _latest_init_trace(repo)
    assert trace["status"] == "failed"
    assert "existing-harness" in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "review-initial-candidate"
    assert "weapon-library-candidates.yaml" in trace["summary"]["error"]
    assert not (repo / ".ai" / "task-runs").exists()


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
    trace = _latest_init_trace(repo)
    assert trace["status"] == "failed"
    assert "existing-harness" in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "review-candidate"
    assert trace["summary"]["candidate_id"] == "workflow-standard-domain-policy"
    assert trace["summary"]["error"] == "workflow_policy_applied_requires_expert_command"
    assert not (repo / ".ai" / "task-runs").exists()


def test_guided_init_existing_harness_review_human_input_unknown_id_preserves_action_failure(
    tmp_path: Path, monkeypatch
):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr(
        "harness_builder_agent.tools.interactive_init.scan_repository",
        lambda repo_path: _fake_scan(repo_path, "java-spring"),
    )
    first_result = CliRunner().invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert first_result.exit_code == 0, first_result.output

    def fail_scan(_repo_path):
        raise AssertionError("guided existing Harness review-human-input failure must not rescan")

    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", fail_scan)

    result = CliRunner().invoke(
        app,
        ["init", "--repo", str(repo)],
        input="review-human-input\nmissing-interaction\nresolved\nReviewed manually.\nlead-reviewer\n",
    )

    assert result.exit_code != 0
    assert "review-human-input" in result.output
    assert "missing-interaction" in result.output
    trace = _latest_init_trace(repo)
    assert trace["status"] == "failed"
    assert "existing-harness" in trace["stages"]
    assert trace["summary"]["existing_harness_action"] == "review-human-input"
    assert trace["summary"]["interaction_id"] == "missing-interaction"
    assert trace["summary"]["decision"] == "resolved"
    assert trace["summary"]["error"]
    assert not (repo / ".ai" / "task-runs").exists()


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
