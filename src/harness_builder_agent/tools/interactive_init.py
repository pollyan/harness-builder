from __future__ import annotations

import inspect
from pathlib import Path

import typer
import yaml

from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.interaction_decision import CandidateDecision, WorkflowConfirmation
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools.existing_harness_actions import (
    existing_harness_action_menu_lines,
    normalize_existing_harness_action,
)
from harness_builder_agent.tools.existing_harness_action_summaries import (
    asset_candidate_apply_preview,
    asset_candidate_detail,
    benchmark_summary,
    candidate_append_diff_lines,
    candidate_governance_summary,
    human_input_governance_summary,
    self_improve_summary,
    top_improvement_candidate,
    workflow_recommendation_summary,
)
from harness_builder_agent.tools.existing_harness_action_runner import (
    find_asset_candidate,
    review_human_input_default_interaction_id,
    run_existing_harness_action,
    show_asset_candidate_summary,
)
from harness_builder_agent.tools.existing_harness_signals import (
    benchmark_signal_lines,
    experience_status_lines,
    human_input_needed_status_lines,
    read_benchmark_status,
    workflow_routing_status_lines,
)
from harness_builder_agent.tools.existing_harness_status import render_existing_harness_status_overview_lines
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.guided_candidate_review import review_candidates as _review_candidates
from harness_builder_agent.tools.guided_scan_presentation import (
    SCAN_PROGRESS_LABELS as _SCAN_PROGRESS_LABELS,
    evidence_expansion as _evidence_expansion,
    format_affect_labels as _format_affect_labels,
    format_cli_items as _format_cli_items,
    format_plain_cli_items as _format_plain_cli_items,
    format_scan_warning_for_cli as _format_scan_warning_for_cli,
    guided_scan_progress as _guided_scan_progress,
    human_followup_lines as _human_followup_lines,
    list_items as _list_items,
    risk_attention_lines as _risk_attention_lines,
    scan_followup_questions as _scan_followup_questions,
    scan_maturity_followup_lines as _scan_maturity_followup_lines,
    scan_self_check as _scan_self_check,
    show_llm_evidence_expansion as _show_llm_evidence_expansion,
    show_scan_attention_summary as _show_scan_attention_summary,
    show_scan_findings as _show_scan_findings,
    show_scan_followup_questions as _show_scan_followup_questions,
    show_scan_maturity_snapshot as _show_scan_maturity_snapshot,
    show_scan_progress_completed as _show_scan_progress_completed,
    show_scan_progress_failed as _show_scan_progress_failed,
    show_scan_progress_start as _show_scan_progress_start,
    show_scan_self_check as _show_scan_self_check,
    source_bucket_label as _source_bucket_label,
    stack_extensions_list as _stack_extensions_list,
    stack_label as _stack_label,
    stack_summary_label as _stack_summary_label,
    uncertainty_attention_lines as _uncertainty_attention_lines,
    verification_gap_lines as _verification_gap_lines,
    warning_bucket as _warning_bucket,
)
from harness_builder_agent.tools.guided_scan_supplements import parse_guided_scan_supplement
from harness_builder_agent.tools.guided_supplement_presentation import (
    brief_text_items as _brief_text_items,
    scan_override_brief as _scan_override_brief,
    show_scan_back_revision_notice as _show_scan_back_revision_notice,
    show_scan_supplement_cleared_summary as _show_scan_supplement_cleared_summary,
    show_scan_supplement_immediate_summary as _show_scan_supplement_immediate_summary,
    show_scan_supplement_replacement_summary as _show_scan_supplement_replacement_summary,
    show_supplement_impact_summary as _show_supplement_impact_summary,
    show_team_rules_back_revision_notice as _show_team_rules_back_revision_notice,
    show_team_rules_cleared_summary as _show_team_rules_cleared_summary,
    show_team_rules_immediate_summary as _show_team_rules_immediate_summary,
    show_workflow_back_revision_notice as _show_workflow_back_revision_notice,
    show_workflow_note_cleared_summary as _show_workflow_note_cleared_summary,
    show_workflow_note_immediate_summary as _show_workflow_note_immediate_summary,
)
from harness_builder_agent.tools.interaction_decisions import accepted_interactive_decisions, default_non_interactive_decisions
from harness_builder_agent.tools.llm_enhancement_candidates import build_llm_enhancement_candidates
from harness_builder_agent.tools.maintenance_triage import (
    build_maintenance_triage,
    render_maintenance_triage_guidance_lines,
    render_maintenance_triage_lines,
    render_maintenance_triage_menu_hint_lines,
)
from harness_builder_agent.tools.prewrite_preview import (
    GuidedScanOverrides,
    has_existing_partial_harness as _has_existing_partial_harness,
    has_scan_overrides as _has_scan_overrides,
    show_prewrite_maturity_preview as _show_prewrite_maturity_preview,
    weapon_blocker_summary as _weapon_blocker_summary,
    weapon_maturity_dimension_keys as _weapon_maturity_dimension_keys,
    weapon_next_lift_summary as _weapon_next_lift_summary,
)
from harness_builder_agent.tools.scan_repo import scan_repository
from harness_builder_agent.tools.weapon_library import select_weapon_library
from harness_builder_agent.tools.write_assets import write_initial_assets

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
    _show_guided_init_startup_boundary()
    if not typer.confirm("继续生成 Harness?", default=True):
        trace.finish("failed", {"cancelled": True})
        raise typer.Abort()

    _show_scan_progress_start(repo)
    trace.event("scan", "started", "Repository scan started.")
    try:
        inventory, commands = _scan_repository_for_guided_init(repo)
    except Exception as exc:
        trace.event(
            "scan",
            "failed",
            "Repository scan failed before writing formal Harness assets.",
            {"error_type": type(exc).__name__, "error": str(exc)},
        )
        _show_scan_progress_failed(exc)
        trace.finish("failed", {"error_type": type(exc).__name__, "scan_error": str(exc)})
        raise typer.Exit(code=1) from exc
    trace.event(
        "scan",
        "completed",
        "Repository scan completed.",
        {"primary_stack": inventory.primary_stack, "stacks": inventory.stacks, "command_count": len(commands.commands)},
    )
    _show_scan_progress_completed(inventory, commands)
    base_inventory = inventory.model_copy(deep=True)
    base_commands = commands.model_copy(deep=True)

    scan_overrides = GuidedScanOverrides()
    _show_scan_findings(inventory, commands)
    _show_scan_maturity_snapshot(repo, inventory, commands)
    scan_overrides = _collect_scan_supplement(inventory)
    inventory, commands = _scan_state_with_overrides(base_inventory, base_commands, scan_overrides)
    _show_scan_supplement_immediate_summary(scan_overrides)

    inline_contexts: list[str] = _collect_team_rules()
    _show_team_rules_immediate_summary(inline_contexts)
    weapon_selection = select_weapon_library(inventory, commands)
    candidate_report = build_llm_enhancement_candidates(inventory, commands)
    candidate_decisions = _review_candidates(candidate_report, weapon_selection, commands)
    workflow_confirmation = _show_workflows()
    _show_workflow_note_immediate_summary(workflow_confirmation)
    candidate_ids = [item.id for item in candidate_report.candidates]

    while True:
        _show_prewrite_maturity_preview(
            repo,
            inventory,
            commands,
            weapon_selection,
            scan_overrides,
            inline_contexts,
            workflow_confirmation,
        )
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
            previous_scan_overrides = scan_overrides
            _show_scan_back_revision_notice(previous_scan_overrides)
            _show_scan_findings(base_inventory, base_commands)
            _show_scan_maturity_snapshot(repo, base_inventory, base_commands)
            scan_overrides = _collect_scan_supplement(base_inventory)
            inventory, commands = _scan_state_with_overrides(base_inventory, base_commands, scan_overrides)
            if _has_scan_overrides(scan_overrides):
                _show_scan_supplement_immediate_summary(scan_overrides)
                _show_scan_supplement_replacement_summary(previous_scan_overrides, scan_overrides)
            elif _has_scan_overrides(previous_scan_overrides):
                _show_scan_supplement_cleared_summary()
            weapon_selection = select_weapon_library(inventory, commands)
            candidate_report = build_llm_enhancement_candidates(inventory, commands)
            candidate_ids = [item.id for item in candidate_report.candidates]
            continue
        if action == "rules":
            previous_inline_contexts = inline_contexts
            _show_team_rules_back_revision_notice(previous_inline_contexts)
            inline_contexts = _collect_team_rules()
            if inline_contexts:
                _show_team_rules_immediate_summary(inline_contexts)
            elif previous_inline_contexts:
                _show_team_rules_cleared_summary()
            continue
        if action == "candidates":
            candidate_decisions = _review_candidates(candidate_report, weapon_selection, commands)
            continue
        if action == "workflow":
            previous_workflow_confirmation = workflow_confirmation
            _show_workflow_back_revision_notice(previous_workflow_confirmation)
            workflow_confirmation = _show_workflows()
            if workflow_confirmation.notes:
                _show_workflow_note_immediate_summary(workflow_confirmation)
            elif previous_workflow_confirmation.notes:
                _show_workflow_note_cleared_summary()
            continue

    decisions = accepted_interactive_decisions(
        str(repo),
        context_paths=[str(path) for path in context_paths],
        inline_contexts=inline_contexts,
        candidate_ids=candidate_ids,
        scan_notes=scan_overrides.notes,
        primary_stack_override=scan_overrides.primary_stack,
        scan_modules=scan_overrides.modules,
        scan_commands=scan_overrides.commands,
        scan_risk_areas=scan_overrides.risk_areas,
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


def _show_guided_init_startup_boundary() -> None:
    typer.echo("\n== 启动说明 ==")
    typer.echo("- 将扫描仓库文件、构建配置、CI、测试、文档和源码样本证据。")
    typer.echo("- 需要你确认或补充技术栈、模块边界、风险区域、验证命令、团队规则和 Workflow 说明。")
    typer.echo("- 最终确认写入后将生成 project inventory、command catalog、Guides、Sensors、Workflow Skills、成熟度报告和待确认项。")
    typer.echo("- 本次会话会记录 generation trace，用于审计取消、失败和完成结果。")
    typer.echo("- 不会执行 Runtime，不会创建 `.ai/task-runs`，不会默认运行 benchmark。")
    typer.echo("- 在最终输入 `confirm` 前，不会写入或覆盖正式 Harness 资产；trace 只记录本次会话过程。")


def _scan_repository_for_guided_init(repo: Path) -> tuple[ProjectInventory, CommandCatalog]:
    if _scan_repository_accepts_progress(scan_repository):
        return scan_repository(repo, progress=_guided_scan_progress)
    return scan_repository(repo)


def _scan_repository_accepts_progress(scan_callable) -> bool:
    try:
        signature = inspect.signature(scan_callable)
    except (TypeError, ValueError):
        return False
    return any(
        parameter.name == "progress" or parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )


def _handle_existing_harness_entry(repo: Path, trace: GenerationTrace) -> Path | None:
    ai = repo / ".ai"
    if not (ai / "project-inventory.json").exists() or not (ai / "harness-config.yaml").exists():
        return None

    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))
    config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
    score = None
    if (ai / "maturity-score.yaml").exists():
        score = MaturityReport.model_validate(yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8")))
    benchmark = read_benchmark_status(ai)
    experience_lines = experience_status_lines(ai)
    maintenance_actions = build_maintenance_triage(ai, score)

    typer.echo("\n我发现这个仓库已存在 Harness。")
    typer.echo(f"- 仓库：`{inventory.repo_name}`")
    typer.echo(f"- 技术栈：{_stack_summary_label(inventory)}")
    if score:
        typer.echo(f"- 当前成熟度：{score.overall_level}，下一目标：{score.target_next_level or score.overall_level}")
        if score.blocking_reasons:
            typer.echo(f"- 主要阻断项：{score.blocking_reasons[0]}")
    else:
        typer.echo("- 当前成熟度：未发现 `.ai/maturity-score.yaml`，建议先运行 assess。")
    typer.echo(f"- 最近 benchmark：{benchmark}")
    typer.echo("- 维护状态摘要（Maintenance overview）:")
    for line in render_existing_harness_status_overview_lines(ai, config, score, maintenance_actions):
        typer.echo(f"  - {line}")
    typer.echo("- 质量门禁信号（Benchmark signals）:")
    for line in benchmark_signal_lines(ai):
        typer.echo(f"  - {line}")
    typer.echo("- Workflow 路由信号（Workflow routing signals）:")
    for line in workflow_routing_status_lines(config):
        typer.echo(f"  - {line}")
    typer.echo("- 经验 / 审查信号（Experience / review signals）:")
    for line in experience_lines:
        typer.echo(f"  - {line}")
    typer.echo("- 维护优先级（Maintenance triage）:")
    for line in render_maintenance_triage_lines(maintenance_actions):
        typer.echo(f"  - {line}")
    typer.echo("- 维护建议（Maintenance triage guidance）:")
    for line in render_maintenance_triage_guidance_lines(maintenance_actions):
        typer.echo(f"  - {line}")
    typer.echo("- 推荐动作快捷选择（Maintenance action shortcuts）:")
    for line in render_maintenance_triage_menu_hint_lines(maintenance_actions):
        typer.echo(f"  - {line}")
    typer.echo("\n可选动作")
    for line in _existing_harness_action_menu_lines():
        typer.echo(line)

    action = _normalize_existing_harness_action(typer.prompt("你的选择", default="1").strip())
    return run_existing_harness_action(repo, ai, inventory, action, trace, maintenance_actions)


def _existing_harness_action_menu_lines() -> list[str]:
    return existing_harness_action_menu_lines()


def _normalize_existing_harness_action(value: str) -> str:
    return normalize_existing_harness_action(value)


def _benchmark_signal_lines(ai: Path) -> list[str]:
    return benchmark_signal_lines(ai)


def _workflow_routing_status_lines(config: HarnessConfig) -> list[str]:
    return workflow_routing_status_lines(config)


def _human_input_needed_status_lines(ai: Path) -> list[str]:
    return human_input_needed_status_lines(ai)


def _review_human_input_default_interaction_id(maintenance_actions) -> str | None:
    return review_human_input_default_interaction_id(maintenance_actions)


def _benchmark_summary(report: BenchmarkReport) -> str:
    return benchmark_summary(report)


def _workflow_recommendation_summary(recommendation: WorkflowRecommendationReport) -> str:
    return workflow_recommendation_summary(recommendation)


def _candidate_governance_summary(candidate_id: str, decision: str, reviewer: str, applied_path_count: int) -> str:
    return candidate_governance_summary(candidate_id, decision, reviewer, applied_path_count)


def _human_input_governance_summary(interaction_id: str, decision: str, reviewer: str, new_response_status: str) -> str:
    return human_input_governance_summary(interaction_id, decision, reviewer, new_response_status)


def _show_asset_candidate_summary(path: Path) -> AssetCandidateReport:
    return show_asset_candidate_summary(path)


def _find_asset_candidate(report: AssetCandidateReport, candidate_id: str):
    return find_asset_candidate(report, candidate_id)


def _asset_candidate_detail(candidate) -> str:
    return asset_candidate_detail(candidate)


def _asset_candidate_apply_preview(repo: Path, candidate) -> str:
    return asset_candidate_apply_preview(repo, candidate)


def _candidate_append_diff_lines(candidate, marker: str, heading: str) -> list[str]:
    return candidate_append_diff_lines(candidate, marker, heading)


def _self_improve_summary(manifest: SelfImprovePackageManifest) -> str:
    return self_improve_summary(manifest)


def _top_improvement_candidate(path: Path) -> str:
    return top_improvement_candidate(path)


def _collect_scan_supplement(inventory: ProjectInventory) -> GuidedScanOverrides:
    typer.echo("\n需要你补充或修正的地方")
    typer.echo("如果这些判断符合你的理解，直接回车继续。")
    typer.echo(
        "如果需要修正，可以直接输入说明；如果主要技术栈不对，可以输入 `stack=java-spring`、"
        "`stack=dotnet-aspnet`、`stack=node`、`stack=python-flask` 或 `stack=unknown`。"
    )
    typer.echo("可以直接用自然语言说明多栈、噪声目录或真实主模块；这些说明会进入后续 Harness 上下文。")
    typer.echo("也可以用结构化片段补充：`module=路径|类型|名称`、`command=ID|命令|类型|gate|来源|置信度`、`risk=路径|原因`，多个片段用分号分隔。")
    answer = typer.prompt("你的补充或修正", default="", show_default=False).strip()
    if not answer:
        return GuidedScanOverrides()

    def resolve_stack(_value: str) -> str:
        return typer.prompt(
            "请输入允许的技术栈：java-spring / dotnet-aspnet / node / python-flask / unknown",
            default=inventory.primary_stack,
        ).strip()

    return parse_guided_scan_supplement(answer, current_stack=inventory.primary_stack, stack_resolver=resolve_stack)


def _collect_team_rules() -> list[str]:
    typer.echo("\n团队规则")
    typer.echo("除了仓库本身能扫描出来的信息，你们团队是否还有需要 AI 遵守的规则？")
    typer.echo("例如：团队代码规范、组织级架构约束、测试策略、安全合规要求、发布流程、禁止随意修改的目录。")
    answer = typer.prompt("可以输入一段规则说明；暂时没有则直接回车", default="", show_default=False).strip()
    return [answer] if answer else []


def _show_workflows() -> WorkflowConfirmation:
    typer.echo("\n推荐工作流")
    typer.echo("- lightweight：适合低风险文案、配置或小功能调整，步骤包括理解需求、映射 Guide、实现或建议、执行 Sensor、交接摘要。")
    typer.echo("- bugfix：适合缺陷修复，步骤包括观察现象、定位原因、映射 Harness、最小修复、执行相关 Sensor、交接摘要。")
    note = typer.prompt("如果工作流还有补充说明，可以输入；没有则直接回车", default="", show_default=False).strip()
    if note:
        return WorkflowConfirmation(
            shown_workflows=["lightweight", "bugfix"],
            confirmed=True,
            notes=[note],
            impact_scopes=[
                "interaction_decisions",
                "project_context",
                "human_input_needed",
                "review_only_workflow_note",
            ],
            review_status="pending_harness_maintainer_review",
            routing_policy_effect="review_only_no_direct_policy_change",
        )
    return WorkflowConfirmation(
        shown_workflows=["lightweight", "bugfix"],
        confirmed=True,
    )


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
    typer.echo(f"- 技术栈：{_stack_summary_label(inventory)}")
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
        stage = typer.prompt(
            "返回哪一部分？scan=扫描修正，rules=团队规则，candidates=候选项，workflow=Workflow补充",
            default="rules",
        ).strip().lower()
        if stage in {"scan", "rules", "candidates", "workflow"}:
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


def _scan_state_with_overrides(
    base_inventory: ProjectInventory,
    base_commands: CommandCatalog,
    scan_overrides: GuidedScanOverrides,
) -> tuple[ProjectInventory, CommandCatalog]:
    inventory = base_inventory.model_copy(deep=True)
    commands = base_commands.model_copy(deep=True)
    _apply_scan_overrides(inventory, commands, scan_overrides)
    return inventory, commands
