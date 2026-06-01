from __future__ import annotations

import inspect
from pathlib import Path

from pydantic import ValidationError
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
    is_existing_harness_action,
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
from harness_builder_agent.tools.existing_harness_action_runner import run_existing_harness_action
from harness_builder_agent.tools.existing_harness_review_actions import (
    find_asset_candidate,
    review_human_input_default_interaction_id,
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
from harness_builder_agent.tools.guided_team_rules import collect_team_rules as _collect_team_rules
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


class ExistingHarnessStateLoadError(Exception):
    def __init__(self, source: str, error_type: str, message: str) -> None:
        super().__init__(message)
        self.source = source
        self.error_type = error_type
        self.message = message


def run_non_interactive_init(repo: Path, context_paths: list[Path], trace: GenerationTrace) -> Path:
    trace.event("scan", "started", "Repository scan started.")
    try:
        inventory, commands = scan_repository(repo)
    except Exception as exc:
        error_message = _short_error_message(exc)
        trace.event(
            "scan",
            "failed",
            "Repository scan failed before writing formal Harness assets.",
            {"error_type": type(exc).__name__, "error": error_message},
        )
        _show_non_interactive_scan_failed(exc, error_message)
        trace.finish("failed", {"error_type": type(exc).__name__, "scan_error": error_message})
        raise typer.Exit(code=1) from None
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


def _show_non_interactive_scan_failed(exc: Exception, error_message: str) -> None:
    typer.echo("\ninit --non-interactive 扫描失败。")
    typer.echo("- 阶段：scan")
    typer.echo(f"- 原因：{type(exc).__name__}: {error_message}")
    typer.echo("- 未写入正式 Harness 资产。")
    typer.echo("- 请检查 DeepSeek / LLM 配置、网络或扫描错误后重试。")


def run_guided_init(repo: Path, context_paths: list[Path], trace: GenerationTrace) -> Path:
    typer.echo("Harness Builder 将为这个仓库生成一套可审查、可继续修改的 `.ai` 资产。")
    typer.echo(f"目标仓库：{repo}")
    existing = _handle_existing_harness_entry(repo, trace)
    if existing is not None:
        return existing
    reinit_requested = _is_existing_harness_reinit_requested(trace)
    _show_guided_init_startup_boundary(repo, reinit_requested=reinit_requested)
    if not typer.confirm("继续生成 Harness?", default=True):
        _cancel_guided_init(
            trace,
            reinit_requested=reinit_requested,
            before_scan=True,
            cancel_stage="startup_confirmation",
        )

    _show_scan_progress_start(repo)
    trace.event("scan", "started", "Repository scan started.")
    try:
        inventory, commands = _scan_repository_for_guided_init(repo)
    except Exception as exc:
        error_message = _short_error_message(exc)
        trace.event(
            "scan",
            "failed",
            "Repository scan failed before writing formal Harness assets.",
            {"error_type": type(exc).__name__, "error": error_message},
        )
        _show_scan_progress_failed(exc)
        summary = {
            "error_type": type(exc).__name__,
            "scan_error": error_message,
            "scan_completed": False,
            "formal_assets_written": False,
        }
        if reinit_requested:
            summary["existing_harness_action"] = "reinit"
        trace.finish("failed", summary)
        raise typer.Exit(code=1) from None
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
            candidate_count=len(candidate_ids),
            workflow_confirmation=workflow_confirmation,
        )
        if action == "confirm":
            break
        if action == "cancel":
            _cancel_guided_init(
                trace,
                reinit_requested=reinit_requested,
                before_scan=False,
                cancel_stage="prewrite_confirmation",
                inventory=inventory,
                commands=commands,
            )
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
            candidate_decisions = []
            _show_candidate_review_reset_after_scan_back()
            if candidate_ids:
                candidate_decisions = _review_candidates(candidate_report, weapon_selection, commands)
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
    summary = {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)}
    if reinit_requested:
        summary["existing_harness_action"] = "reinit"
    trace.finish("completed", summary)
    return output_dir


def _show_guided_init_startup_boundary(repo: Path, *, reinit_requested: bool = False) -> None:
    typer.echo("\n== 启动说明 ==")
    if reinit_requested:
        typer.echo("- 已选择重新生成现有 Harness。")
        typer.echo("- 接下来会重新扫描这个仓库，并重新生成 Harness 候选与正式资产预览。")
        typer.echo("- 最终输入 `confirm`/`确认` 前，不会覆盖现有正式 Harness 资产。")
        typer.echo("- 如需保留现有 Harness，请在继续前或最终确认前取消并备份 `.ai/`。")
    typer.echo("- 将扫描仓库文件、构建配置、CI、测试、文档和源码样本证据。")
    typer.echo("- 需要你确认或补充技术栈、模块边界、风险区域、验证命令、团队规则和 Workflow 说明。")
    typer.echo(
        "- 最终确认写入后将生成 project inventory、command catalog、Guides、Sensors、Workflow Skills、成熟度报告和待确认项；"
        "Workflow Skills 包括 `lightweight`、`bugfix` 和 `standard`。"
    )
    typer.echo("- 本次会话会记录 generation trace，用于审计取消、失败和完成结果。")
    typer.echo("- 不会执行 Runtime，不会创建 `.ai/task-runs`，不会默认运行 benchmark。")
    for line in _partial_harness_startup_boundary_lines(repo):
        typer.echo(line)
    typer.echo("- 在最终输入 `confirm`/`确认` 前，不会写入或覆盖正式 Harness 资产；trace 只记录本次会话过程。")


def _is_existing_harness_reinit_requested(trace: GenerationTrace) -> bool:
    return any(
        event.get("stage") == "existing-harness"
        and event.get("details", {}).get("action") == "reinit"
        for event in trace.events
    )


def _cancel_guided_init(
    trace: GenerationTrace,
    *,
    reinit_requested: bool,
    before_scan: bool,
    cancel_stage: str,
    inventory: ProjectInventory | None = None,
    commands: CommandCatalog | None = None,
) -> None:
    summary = {
        "cancelled": True,
        "cancel_stage": cancel_stage,
        "scan_completed": inventory is not None and commands is not None,
    }
    if inventory is not None:
        summary["primary_stack"] = inventory.primary_stack
    if commands is not None:
        summary["command_count"] = len(commands.commands)
    if reinit_requested:
        summary["existing_harness_action"] = "reinit"
    trace.finish("failed", summary)
    _show_guided_init_cancelled(reinit_requested=reinit_requested, before_scan=before_scan)
    raise typer.Exit(code=1)


def _show_guided_init_cancelled(*, reinit_requested: bool, before_scan: bool) -> None:
    typer.echo("\n已取消 init。")
    if reinit_requested and before_scan:
        typer.echo("- 未重新扫描，未覆盖正式 Harness 资产，未创建 Runtime 产物。")
    elif before_scan:
        typer.echo("- 未开始扫描，未写入正式 Harness 资产，未创建 Runtime 产物。")
    else:
        typer.echo("- 未确认写入，未覆盖正式 Harness 资产，未创建 Runtime 产物。")


def _partial_harness_startup_boundary_lines(repo: Path) -> list[str]:
    if not _has_existing_partial_harness(repo):
        return []
    present, missing = _partial_harness_core_state(repo)
    if not present or not missing:
        return []
    return [
        "- 不完整 Harness 状态：发现部分 `.ai` core 文件，但还不足以进入已有 Harness 维护入口。",
        f"- 已存在：{_format_inline_paths(present)}；缺失：{_format_inline_paths(missing)}。",
        "- 因核心文件不完整，本次不会进入已有 Harness 维护入口；继续后会按首次 init 重新扫描。",
        "- 如需保留当前 `.ai` 内容，请先取消并备份；最终输入 `confirm`/`确认` 前，不会写入或覆盖正式 Harness 资产。",
    ]


def _partial_harness_core_state(repo: Path) -> tuple[list[str], list[str]]:
    ai = repo / ".ai"
    core_files = [".ai/project-inventory.json", ".ai/harness-config.yaml"]
    present: list[str] = []
    missing: list[str] = []
    for rel_path in core_files:
        target = repo / rel_path
        if target.exists():
            present.append(rel_path)
        else:
            missing.append(rel_path)
    if not ai.exists():
        return [], core_files
    return present, missing


def _format_inline_paths(paths: list[str]) -> str:
    return "、".join(f"`{path}`" for path in paths) if paths else "无"


def _show_candidate_review_reset_after_scan_back() -> None:
    typer.echo("\n候选审查已刷新")
    typer.echo("- 候选项已根据新的扫描状态刷新。")
    typer.echo("- 上一轮候选审查决策已清空，避免旧 accept / reject / edit 套用到当前扫描理解。")
    typer.echo("- 接下来将按当前扫描状态重新审查候选。")


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

    try:
        inventory, config, score = _load_existing_harness_state(ai)
    except ExistingHarnessStateLoadError as exc:
        _show_existing_harness_state_load_failed(exc)
        trace.event(
            "existing-harness",
            "failed",
            "Existing Harness state could not be loaded.",
            {
                "action": "load-state",
                "error": "existing_harness_state_invalid",
                "source": exc.source,
                "error_type": exc.error_type,
                "message": exc.message,
            },
        )
        trace.finish(
            "failed",
            {
                "existing_harness_action": "load-state",
                "error": "existing_harness_state_invalid",
                "source": exc.source,
                "error_type": exc.error_type,
                "message": exc.message,
            },
        )
        raise typer.Exit(code=1)
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
    typer.echo("- 维护建议（Maintenance triage guidance）:")
    for line in render_maintenance_triage_guidance_lines(maintenance_actions):
        typer.echo(f"  - {line}")
    typer.echo("- 推荐动作快捷选择（Maintenance action shortcuts）:")
    for line in render_maintenance_triage_menu_hint_lines(maintenance_actions):
        typer.echo(f"  - {line}")
    typer.echo("- 审计明细（Audit signals）: 以下字段保留给排查、测试定位和报告溯源；优先按上方维护建议行动。")
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
    typer.echo("\n可选动作")
    for line in _existing_harness_action_menu_lines():
        typer.echo(line)

    while True:
        raw_action = typer.prompt("你的选择", default="1").strip()
        action = _normalize_existing_harness_action(raw_action)
        if _is_existing_harness_action(action):
            break
        typer.echo(f"未识别的维护动作：{raw_action}")
        typer.echo("请输入菜单编号、英文命令或中文别名；直接回车等同于 `1` 只读退出。")
    return run_existing_harness_action(repo, ai, inventory, action, trace, maintenance_actions)


def _load_existing_harness_state(ai: Path) -> tuple[ProjectInventory, HarnessConfig, MaturityReport | None]:
    inventory = _read_existing_harness_json(
        ai,
        "project-inventory.json",
        lambda content: ProjectInventory.model_validate_json(content),
    )
    config = _read_existing_harness_yaml(
        ai,
        "harness-config.yaml",
        lambda payload: HarnessConfig.model_validate(payload),
    )
    score = None
    if (ai / "maturity-score.yaml").exists():
        score = _read_existing_harness_yaml(
            ai,
            "maturity-score.yaml",
            lambda payload: MaturityReport.model_validate(payload),
        )
    return inventory, config, score


def _read_existing_harness_json(ai: Path, filename: str, validator):
    path = ai / filename
    source = f".ai/{filename}"
    try:
        return validator(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, ValidationError) as exc:
        raise ExistingHarnessStateLoadError(source, type(exc).__name__, _short_error_message(exc)) from exc


def _read_existing_harness_yaml(ai: Path, filename: str, validator):
    path = ai / filename
    source = f".ai/{filename}"
    try:
        return validator(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (OSError, TypeError, ValueError, yaml.YAMLError, ValidationError) as exc:
        raise ExistingHarnessStateLoadError(source, type(exc).__name__, _short_error_message(exc)) from exc


def _short_error_message(exc: Exception, limit: int = 240) -> str:
    message = " ".join(str(exc).split())
    if len(message) <= limit:
        return message
    return f"{message[: limit - 1]}..."


def _show_existing_harness_state_load_failed(error: ExistingHarnessStateLoadError) -> None:
    typer.echo("\n已有 Harness 读取失败。")
    typer.echo(f"- 文件：`{error.source}`")
    typer.echo(f"- 原因：{error.error_type}: {error.message}")
    typer.echo("- 未重新扫描，未覆盖正式 Harness 资产，未创建 Runtime 产物。")
    typer.echo("- 请修复该文件后重试；如果需要重新初始化，请先备份 `.ai/` 后再显式选择重新生成。")


def _existing_harness_action_menu_lines() -> list[str]:
    return existing_harness_action_menu_lines()


def _normalize_existing_harness_action(value: str) -> str:
    return normalize_existing_harness_action(value)


def _is_existing_harness_action(value: str) -> bool:
    return is_existing_harness_action(value)


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


def _show_workflows() -> WorkflowConfirmation:
    typer.echo("\n推荐工作流")
    typer.echo("- lightweight：适合低风险文案、配置或小功能调整，步骤包括理解需求、映射 Guide、实现或建议、执行 Sensor、交接摘要。")
    typer.echo("- bugfix：适合缺陷修复，步骤包括观察现象、定位原因、映射 Harness、最小修复、执行相关 Sensor、交接摘要。")
    typer.echo("- standard：适合复杂、高风险、跨模块、安全 / 数据或影响不清任务，会升级到更完整的计划、验证、人工确认和交接流程。")
    note = typer.prompt("如果工作流还有补充说明，可以输入；没有则直接回车", default="", show_default=False).strip()
    if note:
        return WorkflowConfirmation(
            shown_workflows=["lightweight", "bugfix", "standard"],
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
        shown_workflows=["lightweight", "bugfix", "standard"],
        confirmed=True,
    )


_FINAL_CONFIRM_ALIASES = {
    "": "confirm",
    "confirm": "confirm",
    "确认": "confirm",
    "写入": "confirm",
    "yes": "confirm",
    "y": "confirm",
    "back": "back",
    "返回": "back",
    "返回修改": "back",
    "修改": "back",
    "cancel": "cancel",
    "取消": "cancel",
    "退出": "cancel",
    "放弃": "cancel",
    "no": "cancel",
    "n": "cancel",
}

_FINAL_BACK_STAGE_ALIASES = {
    "scan": "scan",
    "扫描": "scan",
    "扫描修正": "scan",
    "rules": "rules",
    "团队规则": "rules",
    "规则": "rules",
    "team": "rules",
    "candidates": "candidates",
    "candidate": "candidates",
    "候选": "candidates",
    "候选项": "candidates",
    "workflow": "workflow",
    "工作流": "workflow",
    "workflow补充": "workflow",
}


def _normalize_final_confirmation_choice(value: str) -> str | None:
    return _FINAL_CONFIRM_ALIASES.get(value.strip().lower())


def _normalize_final_back_stage(value: str) -> str | None:
    return _FINAL_BACK_STAGE_ALIASES.get(value.strip().lower())


def _confirm_summary(
    inventory: ProjectInventory,
    commands: CommandCatalog,
    scan_overrides: GuidedScanOverrides,
    inline_contexts: list[str],
    candidate_decisions: list[CandidateDecision],
    candidate_count: int,
    workflow_confirmation: WorkflowConfirmation,
) -> str:
    typer.echo("\n最终确认")
    typer.echo("即将写入 Harness 资产，请检查下面的摘要。")
    typer.echo(f"- 技术栈：{_stack_summary_label(inventory)}")
    typer.echo(f"- 模块数量：{len(inventory.modules)}")
    typer.echo(f"- 团队规则：{len(inline_contexts)} 条")
    typer.echo(_candidate_decision_summary_line(candidate_decisions, candidate_count))
    hard_gates = [command.command for command in commands.commands if command.gate == "hard"]
    typer.echo(f"- hard gate 命令：{', '.join(hard_gates) if hard_gates else '暂未确认'}")
    typer.echo(f"- Workflows：{', '.join(workflow_confirmation.shown_workflows) or '无'}")
    _show_supplement_impact_summary(scan_overrides, inline_contexts, workflow_confirmation)
    typer.echo("- 将写入：project inventory、command catalog、guides、sensors、workflow skills、review candidates、trace。")
    while True:
        raw_choice = typer.prompt(
            "输入 confirm/确认 写入，back/返回 修改，cancel/取消 取消；可直接输入 scan/扫描、rules/团队规则、candidates/候选、workflow/工作流 返回对应部分",
            default="confirm",
        )
        choice = _normalize_final_confirmation_choice(raw_choice)
        if choice == "confirm":
            return "confirm"
        if choice == "back":
            typer.echo("返回修改")
            stage = _normalize_final_back_stage(
                typer.prompt(
                    "返回哪一部分？scan/扫描=扫描修正，rules/团队规则=团队规则，candidates/候选=候选项，workflow/工作流=Workflow补充",
                    default="rules",
                )
            )
            if stage in {"scan", "rules", "candidates", "workflow"}:
                return stage
            typer.echo("未识别的返回目标，回到最终确认。")
            return "back"
        if choice == "cancel":
            return "cancel"
        direct_stage = _normalize_final_back_stage(raw_choice)
        if direct_stage in {"scan", "rules", "candidates", "workflow"}:
            typer.echo("返回修改")
            return direct_stage
        typer.echo(f"未识别的最终确认输入：{raw_choice.strip()}")
        typer.echo(
            "请输入 `confirm`/`确认`、`back`/`返回`、`cancel`/`取消`，"
            "或直接输入 `scan`/`扫描`、`rules`/`团队规则`、`candidates`/`候选`、`workflow`/`工作流`；"
            "直接回车等同于 `confirm`。"
        )


def _candidate_decision_summary_line(candidate_decisions: list[CandidateDecision], candidate_count: int) -> str:
    if candidate_decisions:
        accepted = sum(1 for item in candidate_decisions if item.decision == "accepted")
        rejected = sum(1 for item in candidate_decisions if item.decision == "rejected")
        edited = sum(1 for item in candidate_decisions if item.decision == "edited")
        kept = sum(1 for item in candidate_decisions if item.decision == "kept")
        return f"- 候选决策：确认 {accepted} 条，拒绝 {rejected} 条，备注 {edited} 条，保持候选 {kept} 条"
    if candidate_count:
        return f"- 候选决策：待重新审查 {candidate_count} 条；最终确认会默认保持候选，可输入 back/返回 -> candidates/候选 复核。"
    return "- 候选决策：暂无候选。"


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
