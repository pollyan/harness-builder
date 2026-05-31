from __future__ import annotations

import inspect
from pathlib import Path

import typer
import yaml

from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceLog
from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.human_confirmation import Questionnaire
from harness_builder_agent.schemas.human_input_governance import HumanInputGovernanceLog
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
from harness_builder_agent.tools.existing_harness_actions import (
    existing_harness_action_menu_lines,
    normalize_existing_harness_action,
)
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.human_input_governance import review_human_input
from harness_builder_agent.tools.interaction_decisions import accepted_interactive_decisions, default_non_interactive_decisions
from harness_builder_agent.tools.llm_enhancement_candidates import build_llm_enhancement_candidates
from harness_builder_agent.tools.maintenance_triage import (
    build_maintenance_triage,
    render_maintenance_triage_guidance_lines,
    render_maintenance_triage_lines,
    render_maintenance_triage_menu_hint_lines,
)
from harness_builder_agent.tools.maturity_model import build_maturity_report
from harness_builder_agent.tools.prewrite_preview import (
    GuidedScanOverrides,
    has_existing_partial_harness as _has_existing_partial_harness,
    has_scan_overrides as _has_scan_overrides,
    show_prewrite_maturity_preview as _show_prewrite_maturity_preview,
    weapon_blocker_summary as _weapon_blocker_summary,
    weapon_maturity_dimension_keys as _weapon_maturity_dimension_keys,
    weapon_next_lift_summary as _weapon_next_lift_summary,
)
from harness_builder_agent.tools.recommend_workflow import recommend_workflow
from harness_builder_agent.tools.risk_signals import classify_risk_area, high_impact_risk_areas
from harness_builder_agent.tools.scan_repo import ScanProgressEvent, scan_repository
from harness_builder_agent.tools.self_improve import run_self_improve
from harness_builder_agent.tools.weapon_library import select_weapon_library
from harness_builder_agent.tools.write_assets import write_initial_assets

SCAN_CONFIRMATION_TYPES = {
    "scan_warning_confirmation",
    "risk_area_confirmation",
    "evidence_expansion_confirmation",
    "scan_followup_confirmation",
}


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


def _show_scan_progress_start(repo: Path) -> None:
    typer.echo("\n扫描仓库")
    typer.echo(f"- 目标仓库：{repo}")
    typer.echo("- 正在收集仓库文件、构建配置、CI、测试和文档证据。")
    typer.echo("- 正在识别构建、测试、验证命令、源码入口、模块线索和风险区域。")
    typer.echo("- 正在请求 LLM 做结构化扫描，并校验返回 schema。")
    typer.echo("- 正在调和 LLM 判断与 evidence；这个阶段可能需要一些时间。")


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


def _guided_scan_progress(event: ScanProgressEvent) -> None:
    label = _SCAN_PROGRESS_LABELS.get(event.phase, event.message)
    if event.status == "started":
        typer.echo(f"- 当前阶段：{label}")
        return
    typer.echo(f"  已完成：{label}")


_SCAN_PROGRESS_LABELS = {
    "collect-evidence": "收集仓库 evidence",
    "plan-evidence-expansion": "请求 LLM 规划补充 evidence",
    "expand-evidence": "读取 LLM 请求的补充 evidence",
    "llm-scan": "请求 LLM 做最终结构化扫描",
    "reconcile-scan": "调和扫描结果",
    "scan-self-check": "请求 LLM 二次自检深度追问",
}


def _show_scan_progress_completed(inventory: ProjectInventory, commands: CommandCatalog) -> None:
    typer.echo("\n扫描完成")
    typer.echo("- 已完成 evidence 收集、LLM 结构化分析和扫描调和。")
    typer.echo(f"- 初步识别技术栈：{_stack_summary_label(inventory)}。")
    typer.echo(f"- 初步识别验证命令数量：{len(commands.commands)}。")


def _show_scan_progress_failed(exc: Exception) -> None:
    typer.echo("\n扫描阶段失败")
    typer.echo(f"- 原因：{type(exc).__name__}: {exc}")
    typer.echo("- 未写入正式 Harness 资产。")
    typer.echo("- 请检查 LLM 配置、网络或扫描错误后重试。")


def _show_scan_findings(inventory: ProjectInventory, commands: CommandCatalog) -> None:
    typer.echo("\n扫描发现")
    typer.echo("我先根据仓库文件、构建配置、源码样本和 LLM 结构化分析做了一个初步判断。")
    typer.echo(f"- 主要技术栈：{_stack_summary_label(inventory)}")
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

    _show_scan_attention_summary(inventory, commands)


def _show_scan_attention_summary(inventory: ProjectInventory, commands: CommandCatalog) -> None:
    _show_llm_evidence_expansion(inventory)
    _show_scan_followup_questions(inventory)
    _show_scan_self_check(inventory)

    typer.echo("\n风险区域")
    for line in _risk_attention_lines(inventory):
        typer.echo(f"- {line}")

    typer.echo("\n不确定性")
    for line in _uncertainty_attention_lines(inventory, commands):
        typer.echo(f"- {line}")

    typer.echo("\n验证缺口")
    for line in _verification_gap_lines(commands):
        typer.echo(f"- {line}")

    typer.echo("\n建议补充")
    for line in _human_followup_lines(inventory, commands):
        typer.echo(f"- {line}")


def _show_llm_evidence_expansion(inventory: ProjectInventory) -> None:
    expansion = _evidence_expansion(inventory)
    if expansion is None:
        return

    typer.echo("\nLLM 深度补充")
    requested = _format_cli_items(expansion.get("requested_paths"))
    focus = _format_cli_items(expansion.get("risk_focus"))
    read_paths = _format_cli_items(expansion.get("read_paths"))
    rationale = str(expansion.get("rationale") or "未提供规划说明。")
    confidence = str(expansion.get("confidence") or "unknown")

    typer.echo(f"- LLM 规划补读：{requested}")
    typer.echo(f"- 关注原因：{focus}")
    typer.echo(f"- 规划说明：{rationale}")
    if _list_items(expansion.get("read_paths")):
        typer.echo(f"- 实际读取：{read_paths}")
    else:
        typer.echo("- 实际读取：未读取到补充文件；请确认关键路径是否被遗漏或需要人工补充。")
    if confidence == "low":
        typer.echo(f"- 置信度：{confidence}，需要人工确认这些文件是否代表真实关键路径或风险边界。")
    else:
        typer.echo(f"- 置信度：{confidence}")


def _show_scan_followup_questions(inventory: ProjectInventory) -> None:
    questions = _scan_followup_questions(inventory)
    if not questions:
        return

    typer.echo("\n深度追问")
    for question in questions[:5]:
        text = str(question.get("question") or "是否需要补充扫描不确定性？")
        reason = str(question.get("reason") or "扫描阶段存在需要补救的不确定性。")
        affects = _format_affect_labels(question.get("affects"))
        typer.echo(f"- {text}（原因：{reason}；影响：{affects}）")
    remaining = len(questions) - 5
    if remaining > 0:
        typer.echo(f"- 还有 {remaining} 个深度追问，详见 `.ai/questionnaire.yaml` 和 `.ai/human-input-needed.md`。")


def _scan_followup_questions(inventory: ProjectInventory) -> list[dict[str, object]]:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    scan_metadata = extensions.get("scan_metadata")
    if not isinstance(scan_metadata, dict):
        return []
    questions = scan_metadata.get("followup_questions")
    return [item for item in questions if isinstance(item, dict)] if isinstance(questions, list) else []


def _show_scan_self_check(inventory: ProjectInventory) -> None:
    self_check = _scan_self_check(inventory)
    if self_check is None:
        return

    typer.echo("\nLLM 二次自检")
    typer.echo("- 结论边界：pending_harness_maintainer_review；这只是 review-only 结论，不会自动修正正式扫描结果。")
    typer.echo(f"- 整体风险：{self_check.get('overall_risk', 'medium')}")
    typer.echo(f"- 摘要：{self_check.get('summary') or 'LLM 已对深度追问进行二次审查。'}")
    resolutions = self_check.get("resolutions")
    items = [item for item in resolutions if isinstance(item, dict)] if isinstance(resolutions, list) else []
    for item in items[:5]:
        status = str(item.get("status") or "needs_human_confirmation")
        action = str(item.get("suggested_next_action") or "请人工确认该追问。")
        rationale = str(item.get("rationale") or "当前 evidence 不足以完成确认。")
        interaction_id = str(item.get("interaction_id") or "unknown")
        typer.echo(f"- `{interaction_id}`：{status}；建议：{action}；理由：{rationale}")
    remaining = len(items) - 5
    if remaining > 0:
        typer.echo(f"- 还有 {remaining} 条二次自检结论，详见 `.ai/scan-metadata.yaml`。")


def _scan_self_check(inventory: ProjectInventory) -> dict[str, object] | None:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    scan_metadata = extensions.get("scan_metadata")
    if not isinstance(scan_metadata, dict):
        return None
    self_check = scan_metadata.get("self_check")
    return self_check if isinstance(self_check, dict) else None


def _evidence_expansion(inventory: ProjectInventory) -> dict[str, object] | None:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    scan_metadata = extensions.get("scan_metadata")
    if not isinstance(scan_metadata, dict):
        return None
    expansion = scan_metadata.get("evidence_expansion")
    return expansion if isinstance(expansion, dict) else None


def _format_cli_items(value: object) -> str:
    items = _list_items(value)
    if not items:
        return "无"
    return "、".join(f"`{item}`" for item in items[:5])


def _format_plain_cli_items(value: object) -> str:
    items = _list_items(value)
    if not items:
        return "无"
    return ", ".join(items[:5])


def _format_affect_labels(value: object) -> str:
    labels = {
        "maturity": "成熟度",
        "guides": "Guides",
        "sensors": "Sensors",
        "workflow": "Workflow",
        "config": "配置",
    }
    items = _list_items(value)
    if not items:
        return "无"
    return "、".join(labels.get(item, item) for item in items[:5])


def _list_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item]


def _show_scan_maturity_snapshot(repo: Path, inventory: ProjectInventory, commands: CommandCatalog) -> None:
    planned = build_maturity_report(
        ai=None,
        inventory=inventory,
        commands=commands,
        config=HarnessConfig.default(),
        weapon_selection=select_weapon_library(inventory, commands),
    )

    typer.echo("\n扫描后的成熟度初评")
    if _has_existing_partial_harness(repo):
        typer.echo("- 当前从 L1 起步：已发现部分 `.ai` 资产，但还不足以构成完整项目级 Harness。")
    else:
        typer.echo("- 当前从 L0 起步：尚未发现项目级 `.ai` Harness，后续 AI Coding 仍主要依赖临时 prompt 和个人经验。")
    typer.echo(f"- 按当前扫描写入后预计建立：{planned.overall_level} 基线。")
    typer.echo(f"- 下一目标：{planned.target_next_level or planned.overall_level}。")
    typer.echo("- 说明：这是基于当前扫描结果的写入前预测，不代表正式 Harness 已经写入或 benchmark 已经通过。")

    typer.echo("\n主要差距")
    blockers = planned.blocking_reasons[:3] or ["暂无明确阻断项；仍建议通过 benchmark 和真实任务运行验证。"]
    for blocker in blockers:
        typer.echo(f"- {blocker}")

    typer.echo("\n建议优先补充")
    for line in _scan_maturity_followup_lines(planned):
        typer.echo(f"- {line}")


def _scan_maturity_followup_lines(planned: MaturityReport) -> list[str]:
    return [
        "真实可执行的 hard gate 命令，以及哪些命令只能作为 soft signal。",
        "主要模块边界、入口目录和职责，避免 Guides 过于泛化。",
        "高风险区域，例如权限、数据迁移、配置、支付或核心状态变更路径。",
        "团队规则、架构边界或测试策略，这些会影响成熟度判断和后续 Harness 推荐。",
    ]


def _risk_attention_lines(inventory: ProjectInventory) -> list[str]:
    risk_areas = _stack_extensions_list(inventory, "risk_areas")
    if not risk_areas:
        return ["当前扫描暂未识别明确高风险区域；如存在支付、权限、数据迁移或配置目录，请在下一步补充。"]
    lines: list[str] = []
    for risk in risk_areas[:5]:
        signal = classify_risk_area(risk)
        if signal.is_high_impact:
            lines.append(
                f"【高风险，需人工确认】`{signal.path}`：{signal.reason}；"
                f"{signal.confirmation_reason} 命中后建议进入 standard workflow / Workflow 升级或人工确认。"
            )
        else:
            lines.append(f"`{signal.path}`：{signal.reason}")
    return lines


def _uncertainty_attention_lines(inventory: ProjectInventory, commands: CommandCatalog) -> list[str]:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    lines: list[str] = []
    if extensions.get("needs_human_confirmation"):
        lines.append("LLM 扫描标记需要人工确认，请检查技术栈、模块边界、风险区域和验证命令是否符合真实项目。")
    llm_proposal = extensions.get("llm_scan_proposal")
    if isinstance(llm_proposal, dict):
        confidence = llm_proposal.get("confidence")
        if confidence and confidence != "high":
            lines.append(f"LLM 扫描置信度为 {confidence}，建议补充关键目录、测试入口或团队规则。")
    if inventory.primary_stack == "unknown":
        lines.append("主要技术栈仍不明确，需要人工补充真实技术栈或入口目录。")
    if not inventory.modules:
        lines.append("暂未识别稳定模块边界，需要人工确认主要模块、入口文件或职责分工。")
    for warning in _stack_extensions_list(inventory, "scan_warnings")[:5]:
        lines.append(_format_scan_warning_for_cli(inventory, warning))
    low_confidence_commands = [command for command in commands.commands if command.confidence == "low"]
    if low_confidence_commands:
        labels = ", ".join(f"`{command.command}`" for command in low_confidence_commands[:3])
        lines.append(f"低置信度验证命令：{labels}，需要确认是否稳定可执行。")
    return lines or ["当前扫描没有发现必须立即处理的不确定性；仍建议确认关键模块和验证命令。"]


def _format_scan_warning_for_cli(inventory: ProjectInventory, warning: dict[str, object]) -> str:
    code = str(warning.get("code") or "unknown")
    if code == "source_sampling_truncated":
        bucket = _warning_bucket(warning)
        stats = _coverage_bucket_stats(inventory, bucket)
        label = _source_bucket_label(bucket)
        if stats:
            selected = stats.get("selected_count", 0)
            total = stats.get("total_count", 0)
            skipped = stats.get("skipped_count", 0)
            return (
                f"{label} 源码文件较多，本次已抽样 {selected}/{total} 个文件，"
                f"还有 {skipped} 个未进入初始摘要；这可能影响技术栈、模块边界或风险判断，"
                "建议补充关键目录、入口文件或高风险路径。"
            )
        return (
            f"{label} 源码文件较多，本次只抽样读取了部分文件；"
            "可能遗漏核心模块或风险路径，建议补充关键目录、入口文件或高风险路径。"
        )
    if code == "test_evidence_not_found":
        return "当前扫描未找到明确测试证据；建议补充真实 test / integration / lint / typecheck 入口或说明只能先使用 soft gate。"
    message = str(warning.get("message") or code or "扫描存在未分类 warning")
    return f"扫描 warning（{code}）：{message}"


def _warning_bucket(warning: dict[str, object]) -> str:
    bucket = warning.get("bucket")
    if bucket:
        return str(bucket)
    evidence = warning.get("evidence")
    if isinstance(evidence, list) and evidence:
        return str(evidence[0])
    return ""


def _coverage_bucket_stats(inventory: ProjectInventory, bucket: str) -> dict[str, object] | None:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    scan_metadata = extensions.get("scan_metadata")
    if not isinstance(scan_metadata, dict):
        return None
    coverage = scan_metadata.get("coverage")
    if not isinstance(coverage, dict):
        return None
    bucket_coverage = coverage.get("bucket_coverage")
    if not isinstance(bucket_coverage, list):
        return None
    for item in bucket_coverage:
        if isinstance(item, dict) and item.get("bucket") == bucket:
            return item
    return None


def _source_bucket_label(bucket: str) -> str:
    if bucket.startswith("source:") and len(bucket) > len("source:"):
        return f"`{bucket.removeprefix('source:')}`"
    return "源码"


def _verification_gap_lines(commands: CommandCatalog) -> list[str]:
    if not commands.commands:
        return ["暂未发现验证命令；后续 Sensors 需要人工补充 build / test / lint / typecheck 入口。"]
    lines: list[str] = []
    hard_commands = [command for command in commands.commands if command.gate == "hard"]
    if not hard_commands:
        lines.append("暂未确认 hard gate；当前命令都不能直接作为阻断式完成门禁。")
    weak_hard_commands = [command for command in hard_commands if not command.source or command.confidence == "low"]
    if weak_hard_commands:
        labels = ", ".join(f"`{command.command}`" for command in weak_hard_commands[:3])
        lines.append(f"hard gate 证据不足或置信度低：{labels}，需要补充来源或降级为 soft gate。")
    soft_commands = [command for command in commands.commands if command.gate == "soft"]
    if soft_commands:
        labels = ", ".join(f"`{command.command}`" for command in soft_commands[:3])
        lines.append(f"soft gate 只能作为风险提示：{labels}，不能单独证明任务完成。")
    present_types = {command.type for command in commands.commands}
    missing_types = [label for label in ["build", "test", "lint", "typecheck"] if label not in present_types]
    if missing_types:
        lines.append(f"当前扫描未确认这些验证类型：{', '.join(missing_types)}。")
    return lines or ["已发现 hard gate 候选；仍建议确认其在本地和 CI 中稳定可重复。"]


def _human_followup_lines(inventory: ProjectInventory, commands: CommandCatalog) -> list[str]:
    lines: list[str] = []
    risk_areas = _stack_extensions_list(inventory, "risk_areas")
    if high_impact_risk_areas(risk_areas):
        lines.append("请确认高风险线索是否确认为风险边界，命中后是否需要 standard workflow / Workflow 升级或人工确认。")
    elif risk_areas:
        lines.append("请确认上述风险路径是否需要进入 Guides、Workflow 升级条件或人工确认项。")
    else:
        lines.append("如存在高风险目录、权限逻辑、配置变更或数据迁移，请在下一步补充。")
    if not any(command.gate == "hard" for command in commands.commands):
        lines.append("请补充真实可执行的 hard gate 命令，或确认当前项目只能先使用 soft gate。")
    if any(command.confidence == "low" for command in commands.commands):
        lines.append("请确认低置信度命令是否可在开发机或 CI 中稳定运行。")
    if not inventory.modules:
        lines.append("请补充主要模块路径、职责和入口文件，避免后续 Guide 过于泛化。")
    return lines


def _stack_extensions_list(inventory: ProjectInventory, key: str) -> list[dict[str, object]]:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    value = extensions.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _handle_existing_harness_entry(repo: Path, trace: GenerationTrace) -> Path | None:
    ai = repo / ".ai"
    if not (ai / "project-inventory.json").exists() or not (ai / "harness-config.yaml").exists():
        return None

    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))
    config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
    score = None
    if (ai / "maturity-score.yaml").exists():
        score = MaturityReport.model_validate(yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8")))
    benchmark = _read_benchmark_status(ai)
    experience_lines = _experience_status_lines(ai)

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
    typer.echo("- 质量门禁信号（Benchmark signals）:")
    for line in _benchmark_signal_lines(ai):
        typer.echo(f"  - {line}")
    typer.echo("- Workflow 路由信号（Workflow routing signals）:")
    for line in _workflow_routing_status_lines(config):
        typer.echo(f"  - {line}")
    typer.echo("- 经验 / 审查信号（Experience / review signals）:")
    for line in experience_lines:
        typer.echo(f"  - {line}")
    maintenance_actions = build_maintenance_triage(ai, score)
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
    if action == "exit":
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
    if action == "assess":
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
    if action == "improve":
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
    if action == "benchmark":
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
    if action == "recommend-workflow":
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
    if action == "review-candidate":
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
    if action == "review-human-input":
        interaction_id = typer.prompt("Human input interaction ID", default="", show_default=False).strip()
        decision = typer.prompt("决策 resolved/reopened", default="resolved").strip().lower()
        rationale = typer.prompt("决策理由", default="", show_default=False).strip()
        reviewer = typer.prompt("Reviewer", default="harness-maintainer").strip() or "harness-maintainer"
        typer.echo("正在记录 human-input 治理决策...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose human input governance.",
            {"primary_stack": inventory.primary_stack, "action": "review-human-input", "interaction_id": interaction_id, "decision": decision},
        )
        try:
            output_dir = review_human_input(repo, interaction_id, decision, rationale, reviewer)
        except (FileNotFoundError, ValueError) as exc:
            trace.event(
                "existing-harness",
                "failed",
                "Existing Harness human input governance failed.",
                {
                    "primary_stack": inventory.primary_stack,
                    "action": "review-human-input",
                    "interaction_id": interaction_id,
                    "decision": decision,
                    "error": str(exc),
                },
            )
            trace.finish(
                "failed",
                {
                    "primary_stack": inventory.primary_stack,
                    "existing_harness_action": "review-human-input",
                    "interaction_id": interaction_id,
                    "decision": decision,
                    "error": str(exc),
                },
            )
            raise typer.BadParameter(str(exc)) from exc
        governance = HumanInputGovernanceLog.model_validate(
            yaml.safe_load((output_dir / "review" / "human-input-governance.yaml").read_text(encoding="utf-8"))
        )
        latest = governance.decisions[-1]
        trace.artifact(output_dir / "questionnaire.yaml", "questionnaire")
        trace.artifact(output_dir / "human-input-needed.md", "human_confirmation")
        trace.artifact(output_dir / "review" / "human-input-governance.yaml", "human_input_governance")
        trace.artifact(output_dir / "review" / "human-input-governance.md", "review")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness human input governance decision recorded.",
            {
                "primary_stack": inventory.primary_stack,
                "action": "review-human-input",
                "interaction_id": latest.interaction_id,
                "decision": latest.decision,
                "reviewer": latest.reviewer,
            },
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "review-human-input",
                "interaction_id": latest.interaction_id,
                "decision": latest.decision,
                "reviewer": latest.reviewer,
                "new_response_status": latest.new_response_status,
            },
        )
        typer.echo(_human_input_governance_summary(latest.interaction_id, latest.decision, latest.reviewer, latest.new_response_status))
        return output_dir
    if action == "self-improve":
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
    if action == "reinit":
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


def _existing_harness_action_menu_lines() -> list[str]:
    return existing_harness_action_menu_lines()


def _normalize_existing_harness_action(value: str) -> str:
    return normalize_existing_harness_action(value)


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


def _human_input_governance_summary(interaction_id: str, decision: str, reviewer: str, new_response_status: str) -> str:
    return "\n".join(
        [
            "human-input 治理决策已记录。",
            f"- interaction_id={interaction_id}",
            f"- decision={decision}",
            f"- reviewer={reviewer}",
            f"- new_response_status={new_response_status}",
            "- `.ai/questionnaire.yaml`",
            "- `.ai/human-input-needed.md`",
            "- `.ai/review/human-input-governance.yaml`",
            "- `.ai/review/human-input-governance.md`",
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


def _benchmark_signal_lines(ai: Path) -> list[str]:
    path = ai / "benchmark-report.yaml"
    if not path.exists():
        return ["benchmark_failed_checks=not_available"]
    report = BenchmarkReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    failed_checks = [check for check in report.checks if not check.passed]
    lines = [f"benchmark_failed_checks={len(failed_checks)}"]
    lines.extend(f"benchmark_failed_check={check.id}" for check in failed_checks[:3])
    lines.extend(
        f"benchmark_failed_check_detail={check.id}|{_benchmark_failed_check_label(check.id)}"
        for check in failed_checks[:3]
    )
    lines.extend(
        f"benchmark_failed_check_error={check.id}|{detail}"
        for check in failed_checks[:3]
        if (detail := _benchmark_check_detail(check))
    )
    return lines


def _benchmark_failed_check_label(check_id: str) -> str:
    labels = {
        "content:risk-context-consistency": "风险上下文在 Guide / Sensor / Routing 之间不一致",
        "content:init-summary-workflow-routing": "init-summary 的 Workflow 与路由摘要缺失或与 harness-config 漂移",
        "content:hard-gate-command-evidence": "hard gate 命令证据不足",
        "content:workflow-routing-policy": "workflow routing policy 缺少必要升级规则",
        "content:guides-quality": "project-context Guide 缺少必需章节或仓库特异性",
        "content:scan-report": "scan-report 缺少扫描证据审计细节",
        "content:init-summary": "init-summary 缺少扫描证据审计摘要",
        "content:project-context-evidence-context": "project-context Guide 缺少 inventory evidence 或 LLM 证据扩展摘要",
        "content:sensors-quality": "verification Sensor 缺少必需章节或验证风险说明",
    }
    if check_id in labels:
        return labels[check_id]
    if check_id.startswith("schema:"):
        return "机器消费产物 schema 校验失败"
    return "查看 benchmark-report.yaml 获取完整失败详情"


def _benchmark_check_detail(check) -> str:
    details: list[str] = []
    if check.error:
        details.append(check.error)
    details.extend(str(error) for error in check.errors[:3])
    details.extend(str(item) for item in check.missing[:3])
    details.extend(_weak_command_details(check.weak_commands[:3]))
    if len(check.errors) > 3:
        details.append(f"还有 {len(check.errors) - 3} 项错误")
    if len(check.missing) > 3:
        details.append(f"还有 {len(check.missing) - 3} 项缺失")
    if len(check.weak_commands) > 3:
        details.append(f"还有 {len(check.weak_commands) - 3} 个弱命令")
    return "；".join(details)


def _weak_command_details(weak_commands) -> list[str]:
    details: list[str] = []
    for item in weak_commands:
        command_id = str(item.id or "unknown")
        reason = _weak_command_reason(item)
        source = str(item.source or "missing_source")
        details.append(f"{command_id}:{reason}:{source}")
    return details


def _weak_command_reason(item) -> str:
    if item.reason:
        return str(item.reason)
    if not item.source:
        return "missing_source"
    if item.confidence == "low":
        return "low_confidence"
    return "weak_command"


def _workflow_routing_status_lines(config: HarnessConfig) -> list[str]:
    rules = config.workflow_routing.rules
    lines = [
        f"routing_default={config.workflow_routing.default_workflow}",
        f"routing_rule_count={len(rules)}",
    ]
    standard_rules = [rule for rule in rules if rule.id == "standard-escalation"]
    if not standard_rules:
        return [*lines, "standard_escalation=missing"]

    standard = standard_rules[0]
    risk_triggers = [trigger for trigger in standard.triggers if trigger.startswith("risk_area:")]
    lines.extend(
        [
            "standard_escalation=present",
            f"standard_human_confirmation={str(standard.human_confirmation_required).lower()}",
            f"standard_risk_triggers={len(risk_triggers)}",
        ]
    )
    lines.extend(f"risk_trigger={trigger}" for trigger in risk_triggers[:3])
    lines.append(f"missing_hard_gate_trigger={'present' if 'missing_hard_gate' in standard.triggers else 'absent'}")
    return lines


def _experience_status_lines(ai: Path) -> list[str]:
    path = ai / "experience" / "experience-index.yaml"
    if not path.exists():
        return [
            "experience_index=missing",
            *_workflow_recommendation_status_lines(ai),
            f"self_improve_package={_self_improve_package_status(ai)}",
            *_human_input_needed_status_lines(ai),
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
        *_human_input_needed_status_lines(ai),
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


def _human_input_needed_status_lines(ai: Path) -> list[str]:
    if not (ai / "human-input-needed.md").exists():
        return ["human_input_needed=missing"]
    questionnaire_path = ai / "questionnaire.yaml"
    if not questionnaire_path.exists():
        return [
            "human_input_needed=present",
            "human_input_questionnaire=missing",
            "human_input_action_entry=.ai/human-input-needed.md#处理方式",
        ]
    questionnaire = Questionnaire.model_validate(yaml.safe_load(questionnaire_path.read_text(encoding="utf-8")) or {})
    questions = questionnaire.questions
    scan_confirmation_count = sum(1 for question in questions if question.interaction_type in SCAN_CONFIRMATION_TYPES)
    scan_followups = [question for question in questions if question.interaction_type == "scan_followup_confirmation"]
    scan_followup_partial_count = sum(
        1
        for question in scan_followups
        if question.response_status == "partially_addressed_by_current_scan_supplement"
    )
    scan_followup_resolved_count = sum(
        1
        for question in scan_followups
        if question.response_status == "reviewed_resolved_by_harness_maintainer"
    )
    scan_followup_unaddressed_count = sum(1 for question in scan_followups if question.response_status == "unaddressed")
    lines = [
        "human_input_needed=present",
        "human_input_questionnaire=present",
        f"human_input_confirmations={len(questions)}",
        f"human_input_scan_confirmations={scan_confirmation_count}",
    ]
    if scan_followups:
        lines.extend(
            [
                f"human_input_scan_followups_resolved={scan_followup_resolved_count}",
                f"human_input_scan_followups_partially_addressed={scan_followup_partial_count}",
                f"human_input_scan_followups_unaddressed={scan_followup_unaddressed_count}",
            ]
        )
    for question in questions[:3]:
        lines.append(f"human_input_first={question.interaction_id}")
    omitted = len(questions) - 3
    if omitted > 0:
        lines.append(f"human_input_omitted={omitted}")
    lines.append("human_input_action_entry=.ai/human-input-needed.md#处理方式")
    return lines


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
    typer.echo(
        "如果需要修正，可以直接输入说明；如果主要技术栈不对，可以输入 `stack=java-spring`、"
        "`stack=dotnet-aspnet`、`stack=node`、`stack=python-flask` 或 `stack=unknown`。"
    )
    typer.echo("可以直接用自然语言说明多栈、噪声目录或真实主模块；这些说明会进入后续 Harness 上下文。")
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
            if value not in {"java-spring", "dotnet-aspnet", "node", "python-flask", "unknown"}:
                value = typer.prompt(
                    "请输入允许的技术栈：java-spring / dotnet-aspnet / node / python-flask / unknown",
                    default=inventory.primary_stack,
                ).strip()
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


def _show_team_rules_immediate_summary(inline_contexts: list[str]) -> None:
    if not inline_contexts:
        return
    typer.echo("\n团队规则理解")
    for item in inline_contexts[:5]:
        typer.echo(f"- 团队规则：{item}")
    if len(inline_contexts) > 5:
        typer.echo(f"- 还有 {len(inline_contexts) - 5} 条团队规则会进入交互决策。")

    typer.echo("\n团队规则影响")
    typer.echo("- 这些规则会进入 interaction-decisions.yaml、project-context.md 和 human-input-needed.md。")
    typer.echo("- 它们会作为团队提供的约束影响 Guides 和后续人工审查，但不会被当作扫描事实。")
    typer.echo("- 如果规则需要改变正式 workflow routing policy，后续仍应通过候选治理或结构化 patch 审核。")


def _show_team_rules_back_revision_notice(previous_inline_contexts: list[str]) -> None:
    if not previous_inline_contexts:
        return
    typer.echo("\n团队规则返回修改")
    typer.echo("- 你将重新填写团队规则。")
    typer.echo("- 新输入会替换上一版团队规则；直接回车会清空上一版团队规则。")
    typer.echo(f"- 上一版团队规则摘要：{_brief_text_items(previous_inline_contexts)}")


def _show_team_rules_cleared_summary() -> None:
    typer.echo("\n团队规则已清空")
    typer.echo("- 已移除上一版团队规则；后续预览和正式资产将不再保留这些团队规则。")


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


def _show_workflow_note_immediate_summary(workflow_confirmation: WorkflowConfirmation) -> None:
    if not workflow_confirmation.notes:
        return

    typer.echo("\nWorkflow 补充理解")
    for item in workflow_confirmation.notes[:5]:
        typer.echo(f"- Workflow 补充：{item}")
    if len(workflow_confirmation.notes) > 5:
        typer.echo(f"- 还有 {len(workflow_confirmation.notes) - 5} 条 Workflow 补充会进入交互决策。")

    typer.echo("\nWorkflow 补充影响")
    typer.echo("- 这些补充会进入 interaction-decisions.yaml、project-context.md 和 human-input-needed.md。")
    typer.echo("- 它们会作为 review-only 的人工说明影响后续审查；不直接修改正式 workflow routing policy。")
    typer.echo("- 如需改变正式 routing policy，后续仍应通过候选治理或结构化 workflow policy patch 审核。")


def _show_workflow_back_revision_notice(previous_workflow_confirmation: WorkflowConfirmation) -> None:
    if not previous_workflow_confirmation.notes:
        return
    typer.echo("\nWorkflow 补充返回修改")
    typer.echo("- 你将重新填写 Workflow 补充。")
    typer.echo("- 新输入会替换上一版 Workflow 补充；直接回车会清空上一版 Workflow 补充。")
    typer.echo(f"- 上一版 Workflow 补充摘要：{_brief_text_items(previous_workflow_confirmation.notes)}")


def _show_workflow_note_cleared_summary() -> None:
    typer.echo("\nWorkflow 补充已清空")
    typer.echo("- 已移除上一版 Workflow 补充；后续预览和正式资产将不再保留这些 Workflow 补充。")


def _brief_text_items(items: list[str], *, limit: int = 2) -> str:
    shown = [item for item in items if item.strip()][:limit]
    if not shown:
        return "无"
    suffix = f"；还有 {len(items) - limit} 条" if len(items) > limit else ""
    return "；".join(shown) + suffix


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


def _show_scan_supplement_immediate_summary(scan_overrides: GuidedScanOverrides) -> None:
    if not _has_scan_overrides(scan_overrides):
        return

    typer.echo("\n扫描补充理解")
    if scan_overrides.primary_stack:
        typer.echo(f"- 技术栈修正：`{scan_overrides.primary_stack}`。")
    for note in scan_overrides.notes[:5]:
        typer.echo(f"- 用户补充：{note}")
    if len(scan_overrides.notes) > 5:
        typer.echo(f"- 还有 {len(scan_overrides.notes) - 5} 条扫描补充会进入 interaction-decisions。")
    for module in scan_overrides.modules[:5]:
        typer.echo(f"- 结构化模块：`{module['path']}`（{module['kind']}，{module['name']}）。")
    for command in scan_overrides.commands[:5]:
        typer.echo(f"- 结构化验证命令：`{command.command}`，gate={command.gate}，source=`{command.source}`。")
    for risk in scan_overrides.risk_areas[:5]:
        typer.echo(f"- 结构化风险区域：`{risk['path']}`，{risk['reason']}。")

    typer.echo("\n扫描补充影响")
    typer.echo("- 这些补充会更新写入前成熟度缺口判断和后续 Harness 推荐；当前仍属于用户补充，不会被伪装成已验证扫描事实。")
    if scan_overrides.primary_stack:
        typer.echo("- 技术栈修正会影响武器库选择、stack-specific Guides / Sensors 和写入前成熟度预览。")
    if scan_overrides.modules or scan_overrides.notes:
        typer.echo("- 模块和自然语言补充会进入 project inventory / project-context，并影响 Guides 的项目事实叙事。")
    if scan_overrides.commands:
        typer.echo("- 验证命令会进入 command catalog，并影响 Sensors、hard gate 摘要和后续 benchmark 证据检查。")
    if scan_overrides.risk_areas:
        typer.echo("- 风险区域会影响 Workflow 升级、人工确认项和 human-input-needed。")


def _show_scan_back_revision_notice(previous_scan_overrides: GuidedScanOverrides) -> None:
    if not _has_scan_overrides(previous_scan_overrides):
        return
    typer.echo("\n扫描补充返回修改")
    typer.echo("- 你将基于原始扫描结果重新填写扫描补充。")
    typer.echo("- 新输入会替换上一版扫描补充；直接回车会清空上一版补充，并按扫描基线继续。")
    summary = _scan_override_brief(previous_scan_overrides)
    if summary:
        typer.echo(f"- 上一版补充摘要：{summary}")


def _show_scan_supplement_cleared_summary() -> None:
    typer.echo("\n扫描补充已清空")
    typer.echo("- 已移除上一版扫描补充；后续预览和正式资产将按扫描基线、团队规则和候选决策继续。")


def _show_scan_supplement_replacement_summary(
    previous_scan_overrides: GuidedScanOverrides,
    current_scan_overrides: GuidedScanOverrides,
) -> None:
    if not _has_scan_overrides(previous_scan_overrides) or not _has_scan_overrides(current_scan_overrides):
        return
    previous_summary = _scan_override_brief(previous_scan_overrides)
    current_summary = _scan_override_brief(current_scan_overrides)
    if not previous_summary or not current_summary:
        return
    typer.echo("\n扫描补充替换结果")
    typer.echo(f"- 上一版补充：{previous_summary}")
    typer.echo(f"- 当前生效补充：{current_summary}")
    typer.echo("- 最终写入只会使用当前生效补充；上一版补充不会进入 project inventory、command catalog、Guides、Sensors 或 init summary。")


def _scan_override_brief(scan_overrides: GuidedScanOverrides) -> str:
    parts: list[str] = []
    if scan_overrides.primary_stack:
        parts.append(f"stack={scan_overrides.primary_stack}")
    if scan_overrides.modules:
        parts.append("modules=" + ", ".join(item["path"] for item in scan_overrides.modules[:3]))
    if scan_overrides.commands:
        parts.append("commands=" + ", ".join(item.id for item in scan_overrides.commands[:3]))
    if scan_overrides.risk_areas:
        parts.append("risks=" + ", ".join(f"{item['path']}({item['reason']})" for item in scan_overrides.risk_areas[:3]))
    if scan_overrides.notes:
        parts.append("notes=" + "；".join(scan_overrides.notes[:2]))
    return "；".join(parts)


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


def _stack_label(stack: str) -> str:
    labels = {
        "java-spring": "Java 后端项目，使用 Spring / Spring Boot 相关框架",
        "dotnet-aspnet": ".NET 后端项目，使用 ASP.NET Core 相关框架",
        "node": "Node.js / 前端或服务端 JavaScript 项目",
        "python-flask": "Python Flask 后端项目",
        "unknown": "暂时无法可靠判断，需要人工确认",
    }
    return labels.get(stack, stack)


def _stack_summary_label(inventory: ProjectInventory) -> str:
    extensions = inventory.stack_extensions if isinstance(inventory.stack_extensions, dict) else {}
    profile = extensions.get("stack_profile")
    if isinstance(profile, dict):
        composition = profile.get("composition_label")
        if isinstance(composition, str) and composition.strip():
            return composition.strip()
    return _stack_label(inventory.primary_stack)
