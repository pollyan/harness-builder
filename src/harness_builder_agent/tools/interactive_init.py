from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import typer
import yaml

from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceLog
from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.interaction_decision import CandidateDecision, WorkflowConfirmation
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.schemas.workflow_recommendation_history import WorkflowRecommendationHistory
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.benchmark import run_benchmark
from harness_builder_agent.tools.candidate_governance import review_candidate
from harness_builder_agent.tools.experience_index import write_experience_index
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.interaction_decisions import accepted_interactive_decisions, default_non_interactive_decisions
from harness_builder_agent.tools.llm_enhancement_candidates import build_llm_enhancement_candidates
from harness_builder_agent.tools.maintenance_triage import build_maintenance_triage, render_maintenance_triage_lines
from harness_builder_agent.tools.maturity_model import build_maturity_report
from harness_builder_agent.tools.recommend_workflow import recommend_workflow
from harness_builder_agent.tools.scan_repo import scan_repository
from harness_builder_agent.tools.self_improve import run_self_improve
from harness_builder_agent.tools.weapon_library import select_weapon_library
from harness_builder_agent.tools.write_assets import write_initial_assets


@dataclass
class GuidedScanOverrides:
    primary_stack: str | None = None
    notes: list[str] = field(default_factory=list)
    modules: list[dict[str, str]] = field(default_factory=list)
    commands: list[CommandDefinition] = field(default_factory=list)
    risk_areas: list[dict[str, str]] = field(default_factory=list)


def run_non_interactive_init(repo: Path, context_paths: list[Path], trace: GenerationTrace) -> Path:
    trace.event("scan", "started", "Repository scan started.")
    inventory, commands = scan_repository(repo)
    trace.event(
        "scan",
        "completed",
        "Repository scan completed.",
        {"primary_stack": inventory.primary_stack, "stacks": inventory.stacks, "command_count": len(commands.commands)},
    )
    decisions = default_non_interactive_decisions(str(repo), context_paths=[str(path) for path in context_paths])
    output_dir = write_initial_assets(
        repo,
        inventory,
        commands,
        trace=trace,
        context_paths=context_paths,
        interaction_decisions=decisions,
    )
    trace.finish("completed", {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)})
    return output_dir


def run_guided_init(repo: Path, context_paths: list[Path], trace: GenerationTrace) -> Path:
    typer.echo("Harness Builder 将为这个仓库生成一套可审查、可继续修改的 `.ai` 资产。")
    typer.echo(f"目标仓库：{repo}")
    existing = _handle_existing_harness_entry(repo, trace)
    if existing is not None:
        return existing
    if not typer.confirm("继续生成 Harness?", default=True):
        trace.finish("failed", {"cancelled": True})
        raise typer.Abort()

    _show_scan_progress_start(repo)
    trace.event("scan", "started", "Repository scan started.")
    try:
        inventory, commands = scan_repository(repo)
    except Exception as exc:
        trace.event("scan", "failed", "Repository scan failed before writing formal Harness assets.")
        _show_scan_progress_failed(exc)
        raise
    trace.event(
        "scan",
        "completed",
        "Repository scan completed.",
        {"primary_stack": inventory.primary_stack, "stacks": inventory.stacks, "command_count": len(commands.commands)},
    )
    _show_scan_progress_completed(inventory, commands)

    scan_overrides = GuidedScanOverrides()
    _show_scan_findings(inventory, commands)
    scan_overrides = _collect_scan_supplement(inventory)
    _apply_scan_overrides(inventory, commands, scan_overrides)

    inline_contexts: list[str] = _collect_team_rules()
    weapon_selection = select_weapon_library(inventory, commands)
    candidate_report = build_llm_enhancement_candidates(inventory, commands)
    candidate_decisions = _review_candidates(candidate_report, weapon_selection, commands)
    workflow_confirmation = _show_workflows()
    candidate_ids = [item.id for item in candidate_report.candidates]

    while True:
        _show_prewrite_maturity_preview(repo, inventory, commands, weapon_selection)
        action = _confirm_summary(
            inventory,
            commands,
            scan_overrides,
            inline_contexts,
            candidate_decisions,
            workflow_confirmation,
        )
        if action == "confirm":
            break
        if action == "cancel":
            trace.finish("failed", {"cancelled": True})
            raise typer.Abort()
        if action == "scan":
            _show_scan_findings(inventory, commands)
            scan_overrides = _collect_scan_supplement(inventory)
            _apply_scan_overrides(inventory, commands, scan_overrides)
            weapon_selection = select_weapon_library(inventory, commands)
            candidate_report = build_llm_enhancement_candidates(inventory, commands)
            candidate_ids = [item.id for item in candidate_report.candidates]
            continue
        if action == "rules":
            inline_contexts = _collect_team_rules()
            continue
        if action == "candidates":
            candidate_decisions = _review_candidates(candidate_report, weapon_selection, commands)
            continue

    decisions = accepted_interactive_decisions(
        str(repo),
        context_paths=[str(path) for path in context_paths],
        inline_contexts=inline_contexts,
        candidate_ids=candidate_ids,
        scan_notes=scan_overrides.notes,
        primary_stack_override=scan_overrides.primary_stack,
        candidate_decisions=candidate_decisions,
        workflow_confirmation=workflow_confirmation,
    )
    output_dir = write_initial_assets(
        repo,
        inventory,
        commands,
        trace=trace,
        context_paths=context_paths,
        interaction_decisions=decisions,
    )
    trace.finish("completed", {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)})
    return output_dir


def _show_scan_progress_start(repo: Path) -> None:
    typer.echo("\n扫描仓库")
    typer.echo(f"- 目标仓库：{repo}")
    typer.echo("- 正在收集仓库文件、构建配置、CI、测试和文档证据。")
    typer.echo("- 正在识别构建、测试、验证命令、源码入口、模块线索和风险区域。")
    typer.echo("- 正在请求 LLM 做结构化扫描，并校验返回 schema。")
    typer.echo("- 正在调和 LLM 判断与 evidence；这个阶段可能需要一些时间。")


def _show_scan_progress_completed(inventory: ProjectInventory, commands: CommandCatalog) -> None:
    typer.echo("\n扫描完成")
    typer.echo("- 已完成 evidence 收集、LLM 结构化分析和扫描调和。")
    typer.echo(f"- 初步识别技术栈：{_stack_label(inventory.primary_stack)}。")
    typer.echo(f"- 初步识别验证命令数量：{len(commands.commands)}。")


def _show_scan_progress_failed(exc: Exception) -> None:
    typer.echo("\n扫描阶段失败")
    typer.echo(f"- 原因：{type(exc).__name__}: {exc}")
    typer.echo("- 未写入正式 Harness 资产。")
    typer.echo("- 请检查 LLM 配置、网络或扫描错误后重试。")


def _show_scan_findings(inventory: ProjectInventory, commands: CommandCatalog) -> None:
    typer.echo("\n扫描发现")
    typer.echo("我先根据仓库文件、构建配置、源码样本和 LLM 结构化分析做了一个初步判断。")
    typer.echo(f"- 主要技术栈：{_stack_label(inventory.primary_stack)}")
    if inventory.stacks:
        typer.echo(f"- 技术线索：{', '.join(inventory.stacks)}")

    evidence = inventory.evidence or inventory.configs or inventory.documents
    typer.echo("\n判断依据")
    for item in evidence[:6]:
        typer.echo(f"- `{item.get('path', 'unknown')}`：{item.get('reason') or item.get('kind') or '扫描证据'}")
    if not evidence:
        typer.echo("- 暂时没有足够直接证据，建议人工补充。")

    typer.echo("\n识别到的模块")
    if inventory.modules:
        for module in inventory.modules:
            typer.echo(f"- {module.get('kind', '模块')}：`{module.get('path', '.')}`（{module.get('name', '未命名')}）")
    else:
        typer.echo("- 暂未识别出稳定模块边界，建议人工补充。")

    typer.echo("\n识别到的验证命令")
    if commands.commands:
        for command in commands.commands:
            gate = "阻断式 hard gate" if command.gate == "hard" else "提示式 soft gate"
            typer.echo(f"- `{command.command}`：{gate}，来源 `{command.source}`，置信度 {command.confidence}")
    else:
        typer.echo("- 暂未发现稳定验证命令，后续会作为待补齐 Sensor。")


def _handle_existing_harness_entry(repo: Path, trace: GenerationTrace) -> Path | None:
    ai = repo / ".ai"
    if not (ai / "project-inventory.json").exists() or not (ai / "harness-config.yaml").exists():
        return None

    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))
    HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
    score = None
    if (ai / "maturity-score.yaml").exists():
        score = MaturityReport.model_validate(yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8")))
    benchmark = _read_benchmark_status(ai)
    experience_lines = _experience_status_lines(ai)

    typer.echo("\n我发现这个仓库已存在 Harness。")
    typer.echo(f"- 仓库：`{inventory.repo_name}`")
    typer.echo(f"- 技术栈：{_stack_label(inventory.primary_stack)}")
    if score:
        typer.echo(f"- 当前成熟度：{score.overall_level}，下一目标：{score.target_next_level or score.overall_level}")
        if score.blocking_reasons:
            typer.echo(f"- 主要阻断项：{score.blocking_reasons[0]}")
    else:
        typer.echo("- 当前成熟度：未发现 `.ai/maturity-score.yaml`，建议先运行 assess。")
    typer.echo(f"- 最近 benchmark：{benchmark}")
    typer.echo("- Experience / review signals:")
    for line in experience_lines:
        typer.echo(f"  - {line}")
    typer.echo("- Maintenance triage:")
    for line in render_maintenance_triage_lines(build_maintenance_triage(ai, score)):
        typer.echo(f"  - {line}")
    typer.echo("\n可选动作")
    typer.echo("- exit：退出，不覆盖现有 Harness。")
    typer.echo("- assess：重新评估成熟度，只刷新 maturity 和 init summary 产物。")
    typer.echo("- improve：基于成熟度缺口生成 review-only 改进候选，不覆盖正式 Harness 资产。")
    typer.echo("- benchmark：运行 Harness 质量门禁，刷新 benchmark / maturity / improvement 派生产物，不覆盖正式 Harness 资产。")
    typer.echo("- recommend-workflow：输入任务说明，生成 review-only Workflow 推荐，不执行任务或修改正式 routing policy。")
    typer.echo("- review-candidate：记录候选 accepted / deferred / rejected；Guide/Sensor 可显式 applied，workflow_policy 仍需专家命令。")
    typer.echo("- self-improve：生成 review-only 自改进审查包，不应用正式资产或执行 Runtime。")
    typer.echo("- reinit：继续重新扫描并进入当前生成向导。")

    action = typer.prompt("你的选择", default="exit").strip().lower()
    if action in {"exit", "quit", "q"}:
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness detected; user exited without rewriting formal assets.",
            {"primary_stack": inventory.primary_stack, "action": "exit"},
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "exit",
            },
        )
        return ai
    if action in {"assess", "reassess", "复评", "重新评估"}:
        typer.echo("正在重新评估现有 Harness 成熟度...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose maturity reassessment.",
            {"primary_stack": inventory.primary_stack, "action": "assess"},
        )
        output_dir = assess_maturity(repo)
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-report.md", "maturity_report")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.artifact(output_dir / "init-summary.md", "init_summary")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness maturity assessment refreshed.",
            {"primary_stack": inventory.primary_stack, "action": "assess", "artifact_count": 4},
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "assess",
                "artifact_count": 4,
            },
        )
        typer.echo("成熟度评估已刷新。")
        typer.echo("- `.ai/maturity-score.yaml`")
        typer.echo("- `.ai/maturity-report.md`")
        typer.echo("- `.ai/maturity-evidence.yaml`")
        typer.echo("- `.ai/init-summary.md`")
        return output_dir
    if action in {"improve", "recommendations", "建议", "改进"}:
        typer.echo("正在生成成熟度驱动的改进候选...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose improvement candidate generation.",
            {"primary_stack": inventory.primary_stack, "action": "improve"},
        )
        write_experience_index(ai)
        output_dir = assess_maturity(repo)
        output_dir = generate_improvements(repo)
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-report.md", "maturity_report")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.artifact(output_dir / "init-summary.md", "init_summary")
        trace.artifact(output_dir / "improvement-candidates.yaml", "improvement_candidates")
        trace.artifact(output_dir / "evolution-plan.md", "plan")
        trace.artifact(output_dir / "experience" / "pending-improvements.md", "experience")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness improvement candidates generated.",
            {"primary_stack": inventory.primary_stack, "action": "improve", "artifact_count": 8},
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "improve",
                "artifact_count": 8,
            },
        )
        typer.echo("改进候选已生成。")
        typer.echo(_top_improvement_candidate(output_dir / "improvement-candidates.yaml"))
        typer.echo("- `.ai/improvement-candidates.yaml`")
        typer.echo("- `.ai/evolution-plan.md`")
        typer.echo("- `.ai/experience/pending-improvements.md`")
        typer.echo("- `.ai/experience/experience-index.yaml`")
        return output_dir
    if action in {"benchmark", "bench", "质量", "验收"}:
        typer.echo("正在运行 Harness benchmark...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose benchmark validation.",
            {"primary_stack": inventory.primary_stack, "action": "benchmark"},
        )
        report = BenchmarkReport.model_validate(run_benchmark(repo, profile=inventory.primary_stack, trace=trace))
        failed_checks = [check for check in report.checks if not check.passed]
        output_dir = ai
        trace.artifact(output_dir / "benchmark-report.yaml", "benchmark_report")
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-report.md", "maturity_report")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.artifact(output_dir / "init-summary.md", "init_summary")
        trace.artifact(output_dir / "improvement-candidates.yaml", "improvement_candidates")
        trace.artifact(output_dir / "evolution-plan.md", "plan")
        trace.artifact(output_dir / "experience" / "pending-improvements.md", "experience")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.event(
            "existing-harness",
            "completed" if report.status == "passed" else "failed",
            "Existing Harness benchmark validation completed.",
            {
                "primary_stack": inventory.primary_stack,
                "action": "benchmark",
                "benchmark_status": report.status,
                "quality_status": report.quality_status,
                "failed_check_count": len(failed_checks),
            },
        )
        trace.finish(
            "completed" if report.status == "passed" else "failed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "benchmark",
                "benchmark_status": report.status,
                "quality_status": report.quality_status,
                "check_count": len(report.checks),
                "failed_check_count": len(failed_checks),
            },
        )
        typer.echo(_benchmark_summary(report))
        return output_dir
    if action in {"recommend-workflow", "recommend", "workflow", "工作流", "路由"}:
        task_brief = typer.prompt("任务说明", default="", show_default=False).strip()
        if not task_brief:
            trace.event(
                "existing-harness",
                "failed",
                "Workflow recommendation requires a task brief.",
                {"primary_stack": inventory.primary_stack, "action": "recommend-workflow"},
            )
            trace.finish(
                "failed",
                {
                    "primary_stack": inventory.primary_stack,
                    "existing_harness_action": "recommend-workflow",
                    "error": "empty_task_brief",
                },
            )
            raise typer.BadParameter("recommend-workflow requires a non-empty task brief.")
        task_id = typer.prompt("任务 ID", default="manual-task").strip() or "manual-task"
        typer.echo("正在生成 review-only Workflow 推荐...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose workflow recommendation.",
            {"primary_stack": inventory.primary_stack, "action": "recommend-workflow", "task_id": task_id},
        )
        output_dir = recommend_workflow(repo, task_brief=task_brief, task_id=task_id)
        recommendation = WorkflowRecommendationReport.model_validate(
            yaml.safe_load((output_dir / "review" / "workflow-routing-recommendation.yaml").read_text(encoding="utf-8"))
        )
        trace.artifact(output_dir / "review" / "workflow-routing-recommendation.yaml", "workflow_recommendation")
        trace.artifact(output_dir / "review" / "workflow-routing-recommendation.md", "review")
        trace.artifact(output_dir / "review" / "workflow-routing-recommendations" / "index.yaml", "workflow_recommendation_history")
        trace.artifact(output_dir / "review" / "workflow-routing-recommendations.md", "review")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness workflow recommendation generated.",
            {
                "primary_stack": inventory.primary_stack,
                "action": "recommend-workflow",
                "task_id": recommendation.task_id,
                "recommended_workflow": recommendation.recommended_workflow,
                "risk_level": recommendation.risk_level,
                "confidence": recommendation.confidence,
            },
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "recommend-workflow",
                "task_id": recommendation.task_id,
                "recommended_workflow": recommendation.recommended_workflow,
                "risk_level": recommendation.risk_level,
                "confidence": recommendation.confidence,
                "human_confirmation_required": recommendation.human_confirmation_required,
            },
        )
        typer.echo(_workflow_recommendation_summary(recommendation))
        return output_dir
    if action in {"review-candidate", "candidate", "governance", "候选", "治理"}:
        candidate_report = _show_asset_candidate_summary(ai / "review" / "asset-candidates.yaml")
        candidate_id = typer.prompt("候选 ID", default="", show_default=False).strip()
        candidate = _find_asset_candidate(candidate_report, candidate_id)
        typer.echo(_asset_candidate_detail(candidate))
        typer.echo(_asset_candidate_apply_preview(repo, candidate))
        decision = typer.prompt("决策 accepted/deferred/rejected/applied", default="deferred").strip().lower()
        if decision == "applied" and candidate.kind == "workflow_policy":
            trace.event(
                "existing-harness",
                "failed",
                "Guided candidate governance does not apply workflow policy candidates.",
                {"primary_stack": inventory.primary_stack, "action": "review-candidate", "candidate_id": candidate_id},
            )
            trace.finish(
                "failed",
                {
                    "primary_stack": inventory.primary_stack,
                    "existing_harness_action": "review-candidate",
                    "candidate_id": candidate_id,
                    "error": "workflow_policy_applied_requires_expert_command",
                },
            )
            raise typer.BadParameter("guided workflow_policy applied requires the expert command with structured patch review.")
        if decision not in {"accepted", "deferred", "rejected", "applied"}:
            trace.event(
                "existing-harness",
                "failed",
                "Unsupported guided candidate governance decision.",
                {"primary_stack": inventory.primary_stack, "action": "review-candidate", "candidate_id": candidate_id, "decision": decision},
            )
            trace.finish(
                "failed",
                {
                    "primary_stack": inventory.primary_stack,
                    "existing_harness_action": "review-candidate",
                    "candidate_id": candidate_id,
                    "decision": decision,
                    "error": "unsupported_decision",
                },
            )
            raise typer.BadParameter("decision must be accepted, deferred, rejected, or applied.")
        rationale = typer.prompt("决策理由", default="", show_default=False).strip()
        reviewer = typer.prompt("Reviewer", default="harness-maintainer").strip() or "harness-maintainer"
        typer.echo("正在记录候选治理决策...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose candidate governance.",
            {"primary_stack": inventory.primary_stack, "action": "review-candidate", "candidate_id": candidate_id, "decision": decision},
        )
        try:
            output_dir = review_candidate(repo, candidate_id, decision, rationale, reviewer)
        except (FileNotFoundError, ValueError) as exc:
            trace.event(
                "existing-harness",
                "failed",
                "Existing Harness candidate governance failed.",
                {
                    "primary_stack": inventory.primary_stack,
                    "action": "review-candidate",
                    "candidate_id": candidate_id,
                    "decision": decision,
                    "error": str(exc),
                },
            )
            trace.finish(
                "failed",
                {
                    "primary_stack": inventory.primary_stack,
                    "existing_harness_action": "review-candidate",
                    "candidate_id": candidate_id,
                    "decision": decision,
                    "error": str(exc),
                },
            )
            raise typer.BadParameter(str(exc)) from exc
        governance = CandidateGovernanceLog.model_validate(
            yaml.safe_load((output_dir / "review" / "candidate-governance.yaml").read_text(encoding="utf-8"))
        )
        latest = governance.decisions[-1]
        trace.artifact(output_dir / "review" / "candidate-governance.yaml", "candidate_governance")
        trace.artifact(output_dir / "review" / "candidate-governance.md", "review")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness candidate governance decision recorded.",
            {
                "primary_stack": inventory.primary_stack,
                "action": "review-candidate",
                "candidate_id": latest.candidate_id,
                "decision": latest.decision,
                "reviewer": latest.reviewer,
            },
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "review-candidate",
                "candidate_id": latest.candidate_id,
                "decision": latest.decision,
                "reviewer": latest.reviewer,
                "applied_path_count": len(latest.applied_paths),
            },
        )
        typer.echo(_candidate_governance_summary(latest.candidate_id, latest.decision, latest.reviewer, len(latest.applied_paths)))
        return output_dir
    if action in {"self-improve", "self", "自改进", "智能改进"}:
        typer.echo("正在生成 review-only 自改进审查包...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose self-improve package generation.",
            {"primary_stack": inventory.primary_stack, "action": "self-improve"},
        )
        output_dir = run_self_improve(repo)
        manifest = SelfImprovePackageManifest.model_validate(
            yaml.safe_load((output_dir / "review" / "self-improve-package.yaml").read_text(encoding="utf-8"))
        )
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.artifact(output_dir / "improvement-candidates.yaml", "improvement_candidates")
        trace.artifact(output_dir / "evolution-plan.md", "plan")
        trace.artifact(output_dir / "experience" / "pending-improvements.md", "experience")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.artifact(output_dir / "review" / "maturity-review.yaml", "maturity_review")
        trace.artifact(output_dir / "review" / "maturity-review.md", "review")
        trace.artifact(output_dir / "review" / "asset-candidates.yaml", "asset_candidates")
        trace.artifact(output_dir / "review" / "asset-candidate-guides.md", "review")
        trace.artifact(output_dir / "review" / "asset-candidate-sensors.md", "review")
        trace.artifact(output_dir / "review" / "asset-candidate-workflows.md", "review")
        trace.artifact(output_dir / "review" / "self-improve-package.yaml", "self_improve_package")
        trace.artifact(output_dir / "review" / "self-improve-package.md", "review")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness self-improve package generated.",
            {
                "primary_stack": inventory.primary_stack,
                "action": "self-improve",
                "improvement_candidate_count": manifest.candidate_counts.improvement_candidates,
                "asset_candidate_count": manifest.candidate_counts.asset_candidates,
            },
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "self-improve",
                "overall_level": manifest.maturity.overall_level,
                "target_next_level": manifest.maturity.target_next_level,
                "improvement_candidate_count": manifest.candidate_counts.improvement_candidates,
                "maturity_review_count": manifest.candidate_counts.maturity_reviews,
                "asset_candidate_count": manifest.candidate_counts.asset_candidates,
            },
        )
        typer.echo(_self_improve_summary(manifest))
        return output_dir
    if action in {"reinit", "重新生成", "regenerate"}:
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness detected; user chose to continue guided regeneration.",
            {"primary_stack": inventory.primary_stack, "action": "reinit"},
        )
        return None
    typer.echo("未识别的选择，默认退出且不覆盖现有 Harness。")
    trace.event(
        "existing-harness",
        "warning",
        "Unknown existing Harness action; defaulted to exit.",
        {"primary_stack": inventory.primary_stack, "action": action},
    )
    trace.finish(
        "completed",
        {
            "primary_stack": inventory.primary_stack,
            "existing_harness_action": "exit",
        },
    )
    return ai


def _benchmark_summary(report: BenchmarkReport) -> str:
    failed_checks = [check for check in report.checks if not check.passed]
    passed_count = len(report.checks) - len(failed_checks)
    status_label = "已通过" if report.status == "passed" else "未通过"
    lines = [
        f"Benchmark {status_label}。",
        f"- status={report.status}",
        f"- quality={report.quality_status}",
        f"- checks={passed_count}/{len(report.checks)}",
        f"- failed_checks={len(failed_checks)}",
    ]
    if failed_checks:
        lines.append("- 失败项：")
        for check in failed_checks[:5]:
            lines.append(f"  - `{check.id}`")
        if len(failed_checks) > 5:
            lines.append(f"  - 还有 {len(failed_checks) - 5} 项，查看 `.ai/benchmark-report.yaml`。")
    lines.append("- `.ai/benchmark-report.yaml`")
    return "\n".join(lines)


def _workflow_recommendation_summary(recommendation: WorkflowRecommendationReport) -> str:
    return "\n".join(
        [
            "工作流推荐已生成。",
            f"- recommended_workflow={recommendation.recommended_workflow}",
            f"- risk={recommendation.risk_level}",
            f"- confidence={recommendation.confidence}",
            f"- human_confirmation_required={recommendation.human_confirmation_required}",
            "- review_status=pending_harness_maintainer_review",
            "- `.ai/review/workflow-routing-recommendation.yaml`",
            "- `.ai/review/workflow-routing-recommendation.md`",
            "- `.ai/review/workflow-routing-recommendations/index.yaml`",
            "- `.ai/review/workflow-routing-recommendations.md`",
        ]
    )


def _candidate_governance_summary(candidate_id: str, decision: str, reviewer: str, applied_path_count: int) -> str:
    return "\n".join(
        [
            "候选治理决策已记录。",
            f"- candidate_id={candidate_id}",
            f"- decision={decision}",
            f"- reviewer={reviewer}",
            f"- applied_paths={applied_path_count}",
            "- `.ai/review/candidate-governance.yaml`",
            "- `.ai/review/candidate-governance.md`",
            "- `.ai/experience/experience-index.yaml`",
        ]
    )


def _show_asset_candidate_summary(path: Path) -> AssetCandidateReport:
    report = AssetCandidateReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    typer.echo("\n待治理候选")
    for candidate in report.candidates[:10]:
        typer.echo(
            f"- `{candidate.id}`：{candidate.title}，kind={candidate.kind}，"
            f"target=`{candidate.suggested_path}`，risk={candidate.risk_level}"
        )
    if len(report.candidates) > 10:
        typer.echo(f"- 还有 {len(report.candidates) - 10} 个候选，请查看 `.ai/review/asset-candidates.yaml`。")
    typer.echo("guided review-candidate 可记录 accepted/deferred/rejected；Guide/Sensor 候选可显式 applied。")
    typer.echo("workflow_policy 候选应用仍需使用专家命令。")
    return report


def _find_asset_candidate(report: AssetCandidateReport, candidate_id: str):
    for candidate in report.candidates:
        if candidate.id == candidate_id:
            return candidate
    raise typer.BadParameter(f"unknown asset candidate id: {candidate_id}")


def _asset_candidate_detail(candidate) -> str:
    evidence = ", ".join(f"`{source}`" for source in candidate.evidence_sources) or "None."
    checks = "\n".join(f"  - {item}" for item in candidate.acceptance_checks) or "  - None."
    return "\n".join(
        [
            "\n候选详情",
            f"- id={candidate.id}",
            f"- kind={candidate.kind}",
            f"- title={candidate.title}",
            f"- target={candidate.suggested_path}",
            f"- risk={candidate.risk_level}",
            f"- review_status={candidate.review_status}",
            f"- evidence_sources={evidence}",
            "- acceptance_checks:",
            checks,
            "- apply_boundary=single_candidate_only",
        ]
    )


def _asset_candidate_apply_preview(repo: Path, candidate) -> str:
    if candidate.kind == "workflow_policy":
        return "\n".join(
            [
                "\n应用预览",
                "- apply_preview=expert_command_required",
                f"- target={candidate.suggested_path}",
                "- guided_workflow_policy_apply=false",
                "- reason=workflow_policy candidates require the expert command with structured patch review.",
                "- source_report=.ai/review/asset-candidates.yaml",
            ]
        )

    if candidate.kind not in {"guide", "sensor"} or not candidate.suggested_path.startswith(".ai/"):
        return "\n".join(
            [
                "\n应用预览",
                "- apply_preview=unavailable",
                f"- target={candidate.suggested_path}",
                "- reason=guided apply only supports Guide / Sensor Markdown candidates under .ai/.",
                "- source_report=.ai/review/asset-candidates.yaml",
            ]
        )

    target = repo / candidate.suggested_path
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    marker = f"<!-- harness-builder:candidate-applied id={candidate.id} -->"
    heading = f"## Applied Candidate: {candidate.title}"
    diff_lines = _candidate_append_diff_lines(candidate, marker, heading)
    return "\n".join(
        [
            "\n应用预览",
            "- apply_preview=available",
            f"- target={candidate.suggested_path}",
            "- apply_mode=append_markdown_candidate_block",
            f"- target_exists={str(target.exists()).lower()}",
            f"- duplicate_marker={'present' if marker in existing else 'absent'}",
            f"- block_heading={heading}",
            "- source_report=.ai/review/asset-candidates.yaml",
            "- diff_preview=unified_append",
            *diff_lines,
        ]
    )


def _candidate_append_diff_lines(candidate, marker: str, heading: str) -> list[str]:
    block_lines = [
        marker,
        heading,
        "",
        f"Rationale: {candidate.rationale}",
        "",
        *candidate.draft_content.rstrip().splitlines(),
        "<!-- /harness-builder:candidate-applied -->",
    ]
    return [f"+{line}" if line else "+" for line in block_lines[:24]]


def _self_improve_summary(manifest: SelfImprovePackageManifest) -> str:
    return "\n".join(
        [
            "自改进审查包已生成。",
            f"- overall_level={manifest.maturity.overall_level}",
            f"- target_next_level={manifest.maturity.target_next_level or 'unknown'}",
            f"- improvement_candidates={manifest.candidate_counts.improvement_candidates}",
            f"- maturity_reviews={manifest.candidate_counts.maturity_reviews}",
            f"- asset_candidates={manifest.candidate_counts.asset_candidates}",
            "- review_status=pending_harness_maintainer_review",
            "- `.ai/review/self-improve-package.yaml`",
            "- `.ai/review/self-improve-package.md`",
        ]
    )


def _top_improvement_candidate(path: Path) -> str:
    report = ImprovementCandidateReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if not report.candidates:
        return "优先候选：暂无候选。"
    priority_order = {"high": 0, "medium": 1, "low": 2}
    candidate = sorted(report.candidates, key=lambda item: (priority_order.get(item.priority, 3), item.id))[0]
    return (
        f"优先候选：`{candidate.id}`"
        f"（priority={candidate.priority}，dimension={candidate.target_dimension or 'unknown'}，"
        f"target=`{candidate.suggested_target}`）"
    )


def _read_benchmark_status(ai: Path) -> str:
    path = ai / "benchmark-report.yaml"
    if not path.exists():
        return "未发现 benchmark-report.yaml"
    report = BenchmarkReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    return f"{report.status}，quality={report.quality_status}"


def _experience_status_lines(ai: Path) -> list[str]:
    path = ai / "experience" / "experience-index.yaml"
    if not path.exists():
        return [
            "experience_index=missing",
            *_workflow_recommendation_status_lines(ai),
            f"self_improve_package={_self_improve_package_status(ai)}",
            f"human_input_needed={_human_input_needed_status(ai)}",
            f"schema_content_failed_checks={_benchmark_schema_content_failed_count(ai)}",
        ]
    index = ExperienceIndex.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    return [
        "experience_index=present",
        f"pending_improvements={index.pending_improvement_count}",
        f"asset_candidates={index.asset_candidate_count}",
        f"candidate_governance={index.candidate_governance_decision_count}",
        f"maturity_reviews={index.maturity_review_count}",
        f"workflow_recommendations={index.workflow_recommendation_count}",
        *_workflow_recommendation_status_lines(ai),
        f"runtime_task_runs={index.runtime_task_run_count}",
        f"self_improve_package={_self_improve_package_status(ai)}",
        f"human_input_needed={_human_input_needed_status(ai)}",
        f"schema_content_failed_checks={_benchmark_schema_content_failed_count(ai)}",
    ]


def _workflow_recommendation_status_lines(ai: Path) -> list[str]:
    history_path = ai / "review" / "workflow-routing-recommendations" / "index.yaml"
    if history_path.exists():
        history = WorkflowRecommendationHistory.model_validate(yaml.safe_load(history_path.read_text(encoding="utf-8")) or {})
        latest = next(
            (
                item
                for item in history.recommendations
                if item.recommendation_id == history.latest_recommendation_id
            ),
            None,
        )
        if latest is None:
            return ["latest_workflow_recommendation=none source=.ai/review/workflow-routing-recommendations/index.yaml"]
        return [
            "latest_workflow_recommendation="
            f"{latest.recommendation_id} "
            f"task={latest.task_id} "
            f"workflow={latest.recommended_workflow} "
            f"risk={latest.risk_level} "
            f"status={latest.review_status} "
            "source=.ai/review/workflow-routing-recommendations/index.yaml"
        ]

    latest_path = ai / "review" / "workflow-routing-recommendation.yaml"
    if latest_path.exists():
        recommendation = WorkflowRecommendationReport.model_validate(
            yaml.safe_load(latest_path.read_text(encoding="utf-8")) or {}
        )
        return [
            "latest_workflow_recommendation=legacy_latest "
            f"task={recommendation.task_id} "
            f"workflow={recommendation.recommended_workflow} "
            f"risk={recommendation.risk_level} "
            f"status={recommendation.review_status} "
            "source=.ai/review/workflow-routing-recommendation.yaml"
        ]

    return []


def _self_improve_package_status(ai: Path) -> str:
    yaml_path = ai / "review" / "self-improve-package.yaml"
    markdown_path = ai / "review" / "self-improve-package.md"
    if not yaml_path.exists() and not markdown_path.exists():
        return "missing"
    if not yaml_path.exists() or not markdown_path.exists():
        return "incomplete"
    manifest = SelfImprovePackageManifest.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
    return (
        "present"
        f"(maturity_reviews={manifest.candidate_counts.maturity_reviews},"
        f"asset_candidates={manifest.candidate_counts.asset_candidates})"
    )


def _human_input_needed_status(ai: Path) -> str:
    return "present" if (ai / "human-input-needed.md").exists() else "missing"


def _benchmark_schema_content_failed_count(ai: Path) -> str:
    path = ai / "benchmark-report.yaml"
    if not path.exists():
        return "not_available"
    report = BenchmarkReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    failed = [
        check
        for check in report.checks
        if not check.passed and (check.id.startswith("schema:") or check.id.startswith("content:"))
    ]
    return str(len(failed))


def _collect_scan_supplement(inventory: ProjectInventory) -> GuidedScanOverrides:
    typer.echo("\n需要你补充或修正的地方")
    typer.echo("如果这些判断符合你的理解，直接回车继续。")
    typer.echo("如果需要修正，可以直接输入说明；如果主要技术栈不对，可以输入 `stack=java-spring`、`stack=dotnet-aspnet`、`stack=node` 或 `stack=unknown`。")
    typer.echo("也可以用结构化片段补充：`module=路径|类型|名称`、`command=ID|命令|类型|gate|来源|置信度`、`risk=路径|原因`，多个片段用分号分隔。")
    answer = typer.prompt("你的补充或修正", default="", show_default=False).strip()
    if not answer:
        return GuidedScanOverrides()
    overrides = GuidedScanOverrides()
    unparsed: list[str] = []
    for part in [item.strip() for item in answer.split(";") if item.strip()]:
        key, separator, value = part.partition("=")
        if not separator:
            unparsed.append(part)
            continue
        key = key.strip().lower()
        value = value.strip()
        if key == "stack":
            if value not in {"java-spring", "dotnet-aspnet", "node", "unknown"}:
                value = typer.prompt("请输入允许的技术栈：java-spring / dotnet-aspnet / node / unknown", default=inventory.primary_stack).strip()
            overrides.primary_stack = value
            overrides.notes.append(f"用户将主要技术栈修正为：{value}")
        elif key == "module":
            fields = [item.strip() for item in value.split("|")]
            if len(fields) >= 3:
                overrides.modules.append({"path": fields[0], "kind": fields[1], "name": fields[2]})
                overrides.notes.append(f"用户补充模块：{fields[0]}（{fields[1]}，{fields[2]}）")
            else:
                unparsed.append(part)
        elif key == "command":
            fields = [item.strip() for item in value.split("|")]
            if len(fields) >= 6 and fields[2] in {"build", "test", "lint", "typecheck", "other"} and fields[3] in {"hard", "soft"}:
                confidence = fields[5] if fields[5] in {"low", "medium", "high"} else "medium"
                overrides.commands.append(
                    CommandDefinition(
                        id=fields[0],
                        command=fields[1],
                        type=fields[2],
                        gate=fields[3],
                        source=fields[4],
                        confidence=confidence,
                    )
                )
                overrides.notes.append(f"用户补充验证命令：{fields[1]}，gate={fields[3]}")
            else:
                unparsed.append(part)
        elif key == "risk":
            fields = [item.strip() for item in value.split("|", 1)]
            if len(fields) == 2:
                overrides.risk_areas.append({"path": fields[0], "reason": fields[1]})
                overrides.notes.append(f"用户补充风险区域：{fields[0]}，{fields[1]}")
            else:
                unparsed.append(part)
        else:
            unparsed.append(part)
    overrides.notes.extend(unparsed)
    return overrides


def _collect_team_rules() -> list[str]:
    typer.echo("\n团队规则")
    typer.echo("除了仓库本身能扫描出来的信息，你们团队是否还有需要 AI 遵守的规则？")
    typer.echo("例如：团队代码规范、组织级架构约束、测试策略、安全合规要求、发布流程、禁止随意修改的目录。")
    answer = typer.prompt("可以输入一段规则说明；暂时没有则直接回车", default="", show_default=False).strip()
    return [answer] if answer else []


def _review_candidates(
    report,
    weapon_selection: WeaponLibrarySelection,
    commands: CommandCatalog,
) -> list[CandidateDecision]:
    typer.echo("\n建议生成的规则")
    typer.echo("这些规则会进入 Guide，影响后续 AI 如何理解项目边界和编码约束。")
    for weapon in weapon_selection.guide_weapons:
        typer.echo(f"- {weapon.title}：{weapon.guidance} 来源线索：{', '.join(weapon.evidence_hints) or '通用基线'}")

    typer.echo("\n建议生成的传感器")
    typer.echo("Sensor 用来描述验证活动。hard gate 失败时不应该声明任务完成，soft gate 则作为风险提示。")
    for weapon in weapon_selection.sensor_weapons:
        typer.echo(f"- {weapon.title}：{weapon.guidance} 建议 gate=`{weapon.gate}`")
    for command in commands.commands:
        typer.echo(f"- 现有命令 `{command.command}`：来自 `{command.source}`，当前 gate=`{command.gate}`")

    decisions: list[CandidateDecision] = []
    candidates = report.model_dump(mode="json")["candidates"]
    if not candidates:
        typer.echo("\n模型没有提出额外候选项。")
        return decisions

    typer.echo("\n逐项审查模型候选")
    typer.echo("选项：a=接受为确认项，r=拒绝，k=保持候选，e=补充备注后保持候选。直接回车等同于 k。")
    for item in candidates:
        typer.echo(f"\n- `{item['id']}`：{item['title']}")
        typer.echo(f"  类型：{'规则 Guide' if item['candidate_type'] == 'guide' else '传感器 Sensor'}")
        typer.echo(f"  作用：{item['rationale']}")
        typer.echo(f"  依据：{', '.join(str(value) for value in item.get('evidence', [])) or '暂无'}")
        choice = typer.prompt("你的选择", default="k").strip().lower()
        if choice == "a":
            decisions.append(CandidateDecision(candidate_id=item["id"], decision="accepted", notes="用户在 guided init 中接受。"))
        elif choice == "r":
            note = "用户在 guided init 中拒绝。"
            decisions.append(CandidateDecision(candidate_id=item["id"], decision="rejected", notes=note))
        elif choice == "e":
            note = typer.prompt("请输入备注", default="", show_default=False).strip()
            decisions.append(CandidateDecision(candidate_id=item["id"], decision="edited", notes=note))
        else:
            decisions.append(CandidateDecision(candidate_id=item["id"], decision="kept", notes="保持候选，等待后续确认。"))
    return decisions


def _show_workflows() -> WorkflowConfirmation:
    typer.echo("\n推荐工作流")
    typer.echo("- lightweight：适合低风险文案、配置或小功能调整，步骤包括理解需求、映射 Guide、实现或建议、执行 Sensor、交接摘要。")
    typer.echo("- bugfix：适合缺陷修复，步骤包括观察现象、定位原因、映射 Harness、最小修复、执行相关 Sensor、交接摘要。")
    note = typer.prompt("如果工作流还有补充说明，可以输入；没有则直接回车", default="", show_default=False).strip()
    return WorkflowConfirmation(
        shown_workflows=["lightweight", "bugfix"],
        confirmed=True,
        notes=[note] if note else [],
    )


def _show_prewrite_maturity_preview(
    repo: Path,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    weapon_selection: WeaponLibrarySelection,
) -> None:
    config = HarnessConfig.default()
    planned = build_maturity_report(
        ai=None,
        inventory=inventory,
        commands=commands,
        config=config,
        weapon_selection=weapon_selection,
    )
    current_level = "L1" if _has_existing_partial_harness(repo) else "L0"

    typer.echo("\n当前 Harness 成熟度初评")
    if current_level == "L0":
        typer.echo("- 当前从 L0 起步：尚未发现项目级 `.ai` Harness，仓库还没有可被 AI Coding Runtime 稳定消费的项目控制资产。")
    else:
        typer.echo("- 当前从 L1 起步：已发现部分 `.ai` 资产，但还不足以构成完整项目级 Harness。")
    typer.echo(f"- 确认写入后预计建立：{planned.overall_level} 基线，包含结构化 Guides、Sensors、Workflow Skills 和生成 trace。")
    typer.echo(f"- 下一目标：{planned.target_next_level or planned.overall_level}")
    typer.echo("- 写入边界：本次只生成 Harness 资产，不执行 Runtime task-run；写入后仍需显式运行 benchmark 完成质量验收。")

    typer.echo("\n主要阻断项")
    blockers = planned.blocking_reasons[:3] or ["暂无阻断项；仍建议通过 benchmark 和真实任务运行验证。"]
    for blocker in blockers:
        typer.echo(f"- {blocker}")

    typer.echo("\n推荐补齐动作")
    next_steps = planned.recommended_next_steps[:3] or ["运行 benchmark，并基于结果进入已有 Harness 维护入口。"]
    for step in next_steps:
        typer.echo(f"- {step}")

    typer.echo("\n写入前 Harness 设计预览")
    typer.echo("将生成的 Guides")
    for weapon in weapon_selection.guide_weapons[:3]:
        typer.echo(f"- {weapon.title}：{weapon.recommended_action}")
    if not weapon_selection.guide_weapons:
        typer.echo("- 暂未匹配到专门 Guide，保留通用项目上下文和人工确认点。")

    typer.echo("将生成的 Sensors")
    for weapon in weapon_selection.sensor_weapons[:3]:
        typer.echo(f"- {weapon.title}：{weapon.recommended_action}，建议 gate={weapon.gate}")
    if not weapon_selection.sensor_weapons:
        typer.echo("- 暂未匹配到专门 Sensor，后续需要补齐验证命令和失败处理策略。")

    typer.echo("Workflow routing")
    routing_notes = {
        "bugfix-intent": "缺陷修复、回归和故障任务进入 bugfix 工作流。",
        "low-risk-lightweight": "范围清晰、低风险、单模块或文档类任务进入 lightweight 工作流。",
        "standard-escalation": "高风险、跨模块、安全、数据、核心状态或影响不清的任务升级到 standard 工作流，并需要人工确认。",
    }
    for rule in config.workflow_routing.rules:
        note = routing_notes.get(rule.id, rule.rationale)
        typer.echo(f"- `{rule.id}` -> {rule.selected_workflow}：{note}")


def _has_existing_partial_harness(repo: Path) -> bool:
    ai = repo / ".ai"
    return (ai / "project-inventory.json").exists() or (ai / "harness-config.yaml").exists()


def _confirm_summary(
    inventory: ProjectInventory,
    commands: CommandCatalog,
    scan_overrides: GuidedScanOverrides,
    inline_contexts: list[str],
    candidate_decisions: list[CandidateDecision],
    workflow_confirmation: WorkflowConfirmation,
) -> str:
    typer.echo("\n最终确认")
    typer.echo("即将写入 Harness 资产，请检查下面的摘要。")
    typer.echo(f"- 技术栈：{_stack_label(inventory.primary_stack)}")
    typer.echo(f"- 模块数量：{len(inventory.modules)}")
    typer.echo(f"- 团队规则：{len(inline_contexts)} 条")
    accepted = sum(1 for item in candidate_decisions if item.decision == "accepted")
    rejected = sum(1 for item in candidate_decisions if item.decision == "rejected")
    edited = sum(1 for item in candidate_decisions if item.decision == "edited")
    kept = sum(1 for item in candidate_decisions if item.decision == "kept")
    typer.echo(f"- 候选决策：确认 {accepted} 条，拒绝 {rejected} 条，备注 {edited} 条，保持候选 {kept} 条")
    hard_gates = [command.command for command in commands.commands if command.gate == "hard"]
    typer.echo(f"- hard gate 命令：{', '.join(hard_gates) if hard_gates else '暂未确认'}")
    typer.echo(f"- Workflows：{', '.join(workflow_confirmation.shown_workflows) or '无'}")
    _show_supplement_impact_summary(scan_overrides, inline_contexts, workflow_confirmation)
    typer.echo("- 将写入：project inventory、command catalog、guides、sensors、workflow skills、review candidates、trace。")
    choice = typer.prompt("输入 confirm 写入，back 返回修改，cancel 取消", default="confirm").strip().lower()
    if choice == "back":
        typer.echo("返回修改")
        stage = typer.prompt("返回哪一部分？scan=扫描修正，rules=团队规则，candidates=候选项", default="rules").strip().lower()
        if stage in {"scan", "rules", "candidates"}:
            return stage
        typer.echo("未识别的返回目标，回到最终确认。")
        return "back"
    if choice == "cancel":
        return "cancel"
    return "confirm"


def _show_supplement_impact_summary(
    scan_overrides: GuidedScanOverrides,
    inline_contexts: list[str],
    workflow_confirmation: WorkflowConfirmation,
) -> None:
    supplement_lines: list[str] = []
    impact_lines: list[str] = []

    if scan_overrides.notes:
        supplement_lines.extend(f"- 扫描补充：{note}" for note in scan_overrides.notes)
        impact_lines.append("- 扫描补充会影响 Guides 与写入前成熟度预览，并进入 interaction-decisions / project-context。")
    if scan_overrides.modules:
        module_labels = ", ".join(f"`{item['path']}`" for item in scan_overrides.modules)
        impact_lines.append(f"- 补充模块 {module_labels} 会进入 project inventory，并影响后续 Guide 的项目事实。")
    if scan_overrides.commands:
        command_labels = ", ".join(f"`{item.command}`" for item in scan_overrides.commands)
        impact_lines.append(f"- 补充命令 {command_labels} 会进入 command catalog，并影响 Sensor 与 hard gate 摘要。")
    if scan_overrides.risk_areas:
        risk_labels = ", ".join(f"`{item['path']}`" for item in scan_overrides.risk_areas)
        impact_lines.append(f"- 补充风险 {risk_labels} 会进入项目风险线索，并影响后续人工确认。")
    if inline_contexts:
        supplement_lines.extend(f"- 团队规则：{item}" for item in inline_contexts)
        impact_lines.append("- 团队规则会影响团队上下文 Guide 与 human-input-needed。")
    if workflow_confirmation.notes:
        supplement_lines.extend(f"- Workflow 补充：{item}" for item in workflow_confirmation.notes)
        impact_lines.append("- Workflow 补充会影响 Workflow 说明与后续人工确认记录。")

    typer.echo("\n已吸收的用户补充")
    if supplement_lines:
        for line in supplement_lines[:8]:
            typer.echo(line)
        if len(supplement_lines) > 8:
            typer.echo(f"- 还有 {len(supplement_lines) - 8} 条补充会写入交互决策。")
    else:
        typer.echo("- 暂无用户补充。")

    typer.echo("\n补充影响")
    if impact_lines:
        for line in impact_lines:
            typer.echo(line)
    else:
        typer.echo("- 当前将按扫描结果和内置 Harness 基线生成。")


def _apply_scan_overrides(
    inventory: ProjectInventory,
    commands: CommandCatalog,
    scan_overrides: GuidedScanOverrides,
) -> None:
    if scan_overrides.primary_stack:
        inventory.primary_stack = scan_overrides.primary_stack
        if scan_overrides.primary_stack != "unknown" and scan_overrides.primary_stack not in inventory.stacks:
            inventory.stacks.append(scan_overrides.primary_stack)
    for module in scan_overrides.modules:
        if module not in inventory.modules:
            inventory.modules.append(module)
    existing_command_ids = {command.id for command in commands.commands}
    for command in scan_overrides.commands:
        if command.id not in existing_command_ids:
            commands.commands.append(command)
            existing_command_ids.add(command.id)
    risk_areas = list(inventory.stack_extensions.get("risk_areas", []))
    for risk in scan_overrides.risk_areas:
        if risk not in risk_areas:
            risk_areas.append(risk)
    if risk_areas:
        inventory.stack_extensions["risk_areas"] = risk_areas
    human_overrides = dict(inventory.stack_extensions.get("human_overrides", {}))
    if scan_overrides.primary_stack:
        human_overrides["primary_stack"] = scan_overrides.primary_stack
    if scan_overrides.notes:
        human_overrides["scan_notes"] = scan_overrides.notes
    if scan_overrides.modules:
        human_overrides["modules"] = scan_overrides.modules
    if scan_overrides.commands:
        human_overrides["commands"] = [command.model_dump(mode="json") for command in scan_overrides.commands]
    if scan_overrides.risk_areas:
        human_overrides["risk_areas"] = scan_overrides.risk_areas
    if human_overrides:
        inventory.stack_extensions["human_overrides"] = human_overrides


def _stack_label(stack: str) -> str:
    labels = {
        "java-spring": "Java 后端项目，使用 Spring / Spring Boot 相关框架",
        "dotnet-aspnet": ".NET 后端项目，使用 ASP.NET Core 相关框架",
        "node": "Node.js / 前端或服务端 JavaScript 项目",
        "unknown": "暂时无法可靠判断，需要人工确认",
    }
    return labels.get(stack, stack)
