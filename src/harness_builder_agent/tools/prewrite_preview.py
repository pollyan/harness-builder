from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import typer

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.interaction_decision import WorkflowConfirmation
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibraryEntry, WeaponLibrarySelection
from harness_builder_agent.tools.maturity_model import build_maturity_report


@dataclass
class GuidedScanOverrides:
    primary_stack: str | None = None
    notes: list[str] = field(default_factory=list)
    modules: list[dict[str, str]] = field(default_factory=list)
    commands: list[CommandDefinition] = field(default_factory=list)
    risk_areas: list[dict[str, str]] = field(default_factory=list)


def show_prewrite_maturity_preview(
    repo: Path,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    weapon_selection: WeaponLibrarySelection,
    scan_overrides: GuidedScanOverrides | None = None,
    inline_contexts: list[str] | None = None,
    workflow_confirmation: WorkflowConfirmation | None = None,
) -> None:
    config = HarnessConfig.default()
    planned = build_maturity_report(
        ai=None,
        inventory=inventory,
        commands=commands,
        config=config,
        weapon_selection=weapon_selection,
    )
    current_level = "L1" if has_existing_partial_harness(repo) else "L0"

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

    _show_maturity_storyline(
        current_level=current_level,
        planned=planned,
        scan_overrides=scan_overrides or GuidedScanOverrides(),
        inline_contexts=inline_contexts or [],
        workflow_confirmation=workflow_confirmation,
    )

    typer.echo("\n写入前 Harness 设计预览")
    _show_scan_supplement_preview_section(scan_overrides or GuidedScanOverrides())

    typer.echo("团队规则约束")
    if inline_contexts:
        for item in inline_contexts[:5]:
            typer.echo(f"- {item}")
        if len(inline_contexts) > 5:
            typer.echo(f"- 还有 {len(inline_contexts) - 5} 条团队规则会写入团队上下文。")
        typer.echo("- 影响范围：进入 Guides、human-input-needed 和后续人工审查；不直接修改正式 workflow routing policy。")
    else:
        typer.echo("- 暂无团队规则输入；当前按扫描证据和内置 Harness 基线生成。")

    typer.echo("Workflow 补充约束")
    workflow_notes = workflow_confirmation.notes if workflow_confirmation else []
    if workflow_notes:
        for item in workflow_notes[:5]:
            typer.echo(f"- {item}")
        if len(workflow_notes) > 5:
            typer.echo(f"- 还有 {len(workflow_notes) - 5} 条 Workflow 补充会写入交互决策。")
        typer.echo(
            "- 影响范围：进入 interaction-decisions.yaml、project-context.md、human-input-needed.md 和后续人工确认；"
            "作为 review-only 说明，不直接修改正式 workflow routing policy。"
        )
    else:
        typer.echo("- 暂无 Workflow 补充；当前按内置 bugfix / lightweight / standard routing 预览。")

    typer.echo("将生成的 Guides")
    for weapon in weapon_selection.guide_weapons[:3]:
        _show_weapon_preview_item(weapon, planned)
    if not weapon_selection.guide_weapons:
        typer.echo("- 暂未匹配到专门 Guide，保留通用项目上下文和人工确认点。")

    typer.echo("将生成的 Sensors")
    for weapon in weapon_selection.sensor_weapons[:3]:
        _show_weapon_preview_item(weapon, planned, include_gate=True)
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


def has_existing_partial_harness(repo: Path) -> bool:
    ai = repo / ".ai"
    return (ai / "project-inventory.json").exists() or (ai / "harness-config.yaml").exists()


def _show_scan_supplement_preview_section(scan_overrides: GuidedScanOverrides) -> None:
    typer.echo("扫描补充约束")
    if not has_scan_overrides(scan_overrides):
        typer.echo("- 暂无扫描补充；当前按扫描基线、团队规则和内置 Harness 基线生成。")
        return

    if scan_overrides.primary_stack:
        typer.echo(f"- 技术栈修正：`{scan_overrides.primary_stack}`。")
    for note in scan_overrides.notes[:5]:
        typer.echo(f"- 自然语言补充：{note}")
    if len(scan_overrides.notes) > 5:
        typer.echo(f"- 还有 {len(scan_overrides.notes) - 5} 条自然语言 scan 补充会写入交互决策。")
    for module in scan_overrides.modules[:5]:
        typer.echo(f"- 结构化模块：`{module['path']}`（{module['kind']}，{module['name']}）。")
    if len(scan_overrides.modules) > 5:
        typer.echo(f"- 还有 {len(scan_overrides.modules) - 5} 个结构化模块会进入 project inventory。")
    for command in scan_overrides.commands[:5]:
        typer.echo(f"- 结构化验证命令：`{command.command}`，gate={command.gate}，source=`{command.source}`。")
    if len(scan_overrides.commands) > 5:
        typer.echo(f"- 还有 {len(scan_overrides.commands) - 5} 条验证命令会进入 command catalog。")
    for risk in scan_overrides.risk_areas[:5]:
        typer.echo(f"- 结构化风险区域：`{risk['path']}`，{risk['reason']}。")
    if len(scan_overrides.risk_areas) > 5:
        typer.echo(f"- 还有 {len(scan_overrides.risk_areas) - 5} 个风险区域会进入 risk hints。")
    typer.echo("- 影响范围：影响 project inventory、command catalog、risk hints、Guides、Sensors、Workflow 升级和人工确认。")
    typer.echo("- 事实边界：这些内容属于用户补充，不会被伪装成已验证扫描事实。")


def _show_maturity_storyline(
    *,
    current_level: str,
    planned: MaturityReport,
    scan_overrides: GuidedScanOverrides,
    inline_contexts: list[str],
    workflow_confirmation: WorkflowConfirmation | None,
) -> None:
    target_level = planned.target_next_level or planned.overall_level
    typer.echo("\n成熟度叙事主线")
    typer.echo(f"- 当前等级：{current_level}；写入后基线：{planned.overall_level}；下一目标：{target_level}。")
    typer.echo("- 预览依据：使用当前扫描调和结果、验证命令、风险线索和内置 Harness 武器库选择。")

    impact_lines: list[str] = []
    if has_scan_overrides(scan_overrides):
        impact_lines.append("扫描补充已更新本轮 inventory / command catalog / risk hints，再进入成熟度预览和 Harness 推荐。")
    if inline_contexts:
        impact_lines.append("团队规则会进入 Guides 与 human-input-needed，用于解释团队约束，但不会伪装成扫描事实。")
    workflow_notes = workflow_confirmation.notes if workflow_confirmation else []
    if workflow_notes:
        impact_lines.append("Workflow 补充会进入 review-only 交互决策，作为后续 routing policy 审查线索。")

    if impact_lines:
        for line in impact_lines:
            typer.echo(f"- 用户补充影响：{line}")
    else:
        typer.echo("- 用户补充影响：当前没有用户补充改变本轮预览；先按扫描证据和内置 Harness 基线生成。")

    typer.echo("- 未完成边界：确认写入只建立可审计 Harness 基线，仍需后续 benchmark 和 Runtime task-run 证据验证。")


def has_scan_overrides(scan_overrides: GuidedScanOverrides) -> bool:
    return bool(
        scan_overrides.primary_stack
        or scan_overrides.notes
        or scan_overrides.modules
        or scan_overrides.commands
        or scan_overrides.risk_areas
    )


def _show_weapon_preview_item(weapon: WeaponLibraryEntry, planned: MaturityReport, *, include_gate: bool = False) -> None:
    suffix = f"，建议 gate={weapon.gate}" if include_gate else ""
    dimension_keys = weapon_maturity_dimension_keys(weapon)
    typer.echo(f"- {weapon.title}：{weapon.recommended_action}{suffix}")
    typer.echo(f"  关联成熟度：{maturity_dimension_labels(dimension_keys)}")
    typer.echo(f"  解决阻断：{weapon_blocker_summary(dimension_keys, planned)}")
    typer.echo(f"  下一阶段贡献：{weapon_next_lift_summary(dimension_keys, planned)}")


def weapon_maturity_dimension_keys(weapon: WeaponLibraryEntry) -> list[str]:
    keys: list[str] = ["guides"] if weapon.kind == "guide" else ["sensors"]
    tags = set(weapon.tags)
    if weapon.kind == "guide" and tags.intersection({"risk", "auth", "sql", "config", "review", "publicapi", "infrastructure"}):
        keys.append("risk_control")
    if weapon.kind == "sensor" and (
        weapon.gate == "hard" or tags.intersection({"hard-gate", "test", "gap", "verification"})
    ):
        keys.append("verification_sophistication")
    return list(dict.fromkeys(keys))


def maturity_dimension_labels(dimension_keys: list[str]) -> str:
    labels = {
        "guides": "Guides 上下文",
        "sensors": "Sensors 验证",
        "risk_control": "Risk Control 风险控制",
        "verification_sophistication": "Verification 验证成熟度",
    }
    return "、".join(labels.get(key, key) for key in dimension_keys)


def weapon_blocker_summary(dimension_keys: list[str], planned: MaturityReport) -> str:
    blockers: list[str] = []
    for key in dimension_keys:
        dimension = planned.dimensions.get(key)
        if not dimension:
            continue
        blockers.extend(blocker.id for blocker in dimension.blockers[:2])
    if blockers:
        return "、".join(dict.fromkeys(blockers))
    return "当前维度暂无直接阻断；该项用于保持基线并支撑后续 benchmark / Runtime 验证。"


def weapon_next_lift_summary(dimension_keys: list[str], planned: MaturityReport) -> str:
    phrases = {
        "guides": "绑定 Guides 到任务风险上下文",
        "sensors": "建立可执行 Sensor 基线",
        "risk_control": "确认风险区域并连接 Workflow 升级策略",
        "verification_sophistication": "将验证命令映射到任务类型、风险等级和 gate 强度",
    }
    selected = [phrases[key] for key in dimension_keys if key in phrases]
    if selected:
        return "；".join(selected)
    requirements: list[str] = []
    for key in dimension_keys:
        dimension = planned.dimensions.get(key)
        if dimension:
            requirements.extend(dimension.next_level_requirements[:1])
    return "；".join(requirements) or "为下一阶段成熟度评估保留可审计依据。"
