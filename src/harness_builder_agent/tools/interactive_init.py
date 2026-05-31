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
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.benchmark import run_benchmark
from harness_builder_agent.tools.candidate_governance import review_candidate
from harness_builder_agent.tools.experience_index import write_experience_index
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.interaction_decisions import accepted_interactive_decisions, default_non_interactive_decisions
from harness_builder_agent.tools.llm_enhancement_candidates import build_llm_enhancement_candidates
from harness_builder_agent.tools.recommend_workflow import recommend_workflow
from harness_builder_agent.tools.scan_repo import scan_repository
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

    trace.event("scan", "started", "Repository scan started.")
    inventory, commands = scan_repository(repo)
    trace.event(
        "scan",
        "completed",
        "Repository scan completed.",
        {"primary_stack": inventory.primary_stack, "stacks": inventory.stacks, "command_count": len(commands.commands)},
    )

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
        action = _confirm_summary(
            inventory,
            commands,
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
    experience = _read_experience_status(ai)

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
    typer.echo(f"- 待处理 Experience / 候选信号：{experience}")
    typer.echo("\n可选动作")
    typer.echo("- exit：退出，不覆盖现有 Harness。")
    typer.echo("- assess：重新评估成熟度，只刷新 maturity 和 init summary 产物。")
    typer.echo("- improve：基于成熟度缺口生成 review-only 改进候选，不覆盖正式 Harness 资产。")
    typer.echo("- benchmark：运行 Harness 质量门禁，刷新 benchmark / maturity / improvement 派生产物，不覆盖正式 Harness 资产。")
    typer.echo("- recommend-workflow：输入任务说明，生成 review-only Workflow 推荐，不执行任务或修改正式 routing policy。")
    typer.echo("- review-candidate：记录候选 accepted / deferred / rejected 决策，不应用正式资产。")
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
        _show_asset_candidate_summary(ai / "review" / "asset-candidates.yaml")
        candidate_id = typer.prompt("候选 ID", default="", show_default=False).strip()
        decision = typer.prompt("决策 accepted/deferred/rejected", default="deferred").strip().lower()
        if decision == "applied":
            trace.event(
                "existing-harness",
                "failed",
                "Guided candidate governance does not apply formal assets.",
                {"primary_stack": inventory.primary_stack, "action": "review-candidate", "candidate_id": candidate_id},
            )
            trace.finish(
                "failed",
                {
                    "primary_stack": inventory.primary_stack,
                    "existing_harness_action": "review-candidate",
                    "candidate_id": candidate_id,
                    "error": "applied_not_supported_in_guided_init",
                },
            )
            raise typer.BadParameter("guided review-candidate supports accepted/deferred/rejected only; use the expert command for applied.")
        if decision not in {"accepted", "deferred", "rejected"}:
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
            raise typer.BadParameter("decision must be accepted, deferred, or rejected.")
        rationale = typer.prompt("决策理由", default="", show_default=False).strip()
        reviewer = typer.prompt("Reviewer", default="harness-maintainer").strip() or "harness-maintainer"
        typer.echo("正在记录候选治理决策...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose candidate governance.",
            {"primary_stack": inventory.primary_stack, "action": "review-candidate", "candidate_id": candidate_id, "decision": decision},
        )
        output_dir = review_candidate(repo, candidate_id, decision, rationale, reviewer)
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
        typer.echo(_candidate_governance_summary(latest.candidate_id, latest.decision, latest.reviewer))
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
        ]
    )


def _candidate_governance_summary(candidate_id: str, decision: str, reviewer: str) -> str:
    return "\n".join(
        [
            "候选治理决策已记录。",
            f"- candidate_id={candidate_id}",
            f"- decision={decision}",
            f"- reviewer={reviewer}",
            "- applied_paths=0",
            "- `.ai/review/candidate-governance.yaml`",
            "- `.ai/review/candidate-governance.md`",
            "- `.ai/experience/experience-index.yaml`",
        ]
    )


def _show_asset_candidate_summary(path: Path) -> None:
    report = AssetCandidateReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    typer.echo("\n待治理候选")
    for candidate in report.candidates[:10]:
        typer.echo(
            f"- `{candidate.id}`：{candidate.title}，kind={candidate.kind}，"
            f"target=`{candidate.suggested_path}`，risk={candidate.risk_level}"
        )
    if len(report.candidates) > 10:
        typer.echo(f"- 还有 {len(report.candidates) - 10} 个候选，请查看 `.ai/review/asset-candidates.yaml`。")
    typer.echo("guided review-candidate 只记录 accepted/deferred/rejected，不应用正式资产。")


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
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    status = payload.get("status", "unknown")
    quality = payload.get("quality_status", "unknown")
    return f"{status}，quality={quality}"


def _read_experience_status(ai: Path) -> str:
    path = ai / "experience" / "experience-index.yaml"
    if not path.exists():
        return "未发现 experience-index.yaml"
    index = ExperienceIndex.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    total = (
        index.pending_improvement_count
        + index.asset_candidate_count
        + index.candidate_governance_decision_count
        + index.maturity_review_count
        + index.workflow_recommendation_count
    )
    return str(total)


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


def _confirm_summary(
    inventory: ProjectInventory,
    commands: CommandCatalog,
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
