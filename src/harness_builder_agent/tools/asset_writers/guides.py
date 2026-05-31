from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.interaction_decision import InteractionDecisions
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibraryEntry, WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_text
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.risk_signals import classify_risk_area


def write_guide_assets(
    ai: Path,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    weapon_selection: WeaponLibrarySelection,
    context_inputs: dict[str, Any] | None = None,
    interaction_decisions: InteractionDecisions | None = None,
    trace: GenerationTrace | None = None,
) -> None:
    write_text(
        ai / "guides" / "project-context.md",
        _guide("project-context", inventory, commands, weapon_selection, context_inputs, interaction_decisions),
    )
    record_artifact(trace, ai / "guides" / "project-context.md", "guide")
    write_text(ai / "guides" / "coding-rules.md", _guide("coding-rules", inventory, commands, weapon_selection))
    record_artifact(trace, ai / "guides" / "coding-rules.md", "guide")
    write_text(ai / "guides" / "architecture.md", _guide("architecture", inventory, commands, weapon_selection))
    record_artifact(trace, ai / "guides" / "architecture.md", "guide")
    write_text(ai / "guides" / "task-templates" / "bugfix.md", _task_template("bugfix"))
    record_artifact(trace, ai / "guides" / "task-templates" / "bugfix.md", "task_template")
    write_text(ai / "guides" / "task-templates" / "lightweight-feature.md", _task_template("lightweight"))
    record_artifact(trace, ai / "guides" / "task-templates" / "lightweight-feature.md", "task_template")


def _frontmatter(asset_type: str) -> str:
    return (
        "---\n"
        f"asset_type: {asset_type}\n"
        "status: candidate\n"
        "source: inferred_from_codebase\n"
        "confidence: medium\n"
        "needs_human_confirmation: true\n"
        "---\n\n"
    )


def _guide(
    name: str,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    weapon_selection: WeaponLibrarySelection,
    context_inputs: dict[str, Any] | None = None,
    interaction_decisions: InteractionDecisions | None = None,
) -> str:
    module_lines = "\n".join(f"- `{module['path']}` ({module['kind']})" for module in inventory.modules) or "- No modules detected"
    evidence_lines = "\n".join(f"- `{item['path']}`：{item['reason']}" for item in inventory.evidence) or "- 暂未发现直接证据"
    match_lines = _weapon_match_lines(weapon_selection.guide_weapons)
    recommended_lines = "\n".join(f"- `{item.id}`：{item.recommended_action}" for item in weapon_selection.guide_weapons)
    return (
        _frontmatter("guide")
        + f"# {name}\n\n"
        + f"仓库 `{inventory.repo_name}` 被识别为 `{inventory.primary_stack}`。\n\n"
        + "## 武器库匹配结果\n\n"
        + f"- 来源：`{weapon_selection.source}`。\n"
        + f"- 已选择技术栈：{', '.join(f'`{stack}`' for stack in weapon_selection.selected_stacks)}。\n"
        + f"{match_lines}\n\n"
        + "## 适用范围\n\n"
        + "当前覆盖整个仓库，正式生效前需要维护者审查。\n\n"
        + "## 团队上下文\n\n"
        + f"{_team_context_section(context_inputs, interaction_decisions)}\n\n"
        + "## 人工补充与修正\n\n"
        + f"{_human_override_section(inventory, interaction_decisions)}\n\n"
        + "## 当前项目事实\n\n"
        + f"- 主技术栈：`{inventory.primary_stack}`。\n"
        + f"- 技术栈线索：{', '.join(inventory.stacks) if inventory.stacks else '未知'}。\n"
        + "- 模块识别：\n"
        + f"{module_lines}\n\n"
        + "## 风险区域\n\n"
        + f"{_risk_area_lines(inventory)}\n\n"
        + "## 验证入口\n\n"
        + f"{_validation_entry_lines(commands)}\n\n"
        + "## 来源证据\n\n"
        + f"{evidence_lines}\n\n"
        + "## 候选规则\n\n"
        + f"{_guide_rule_lines(weapon_selection.guide_weapons)}\n\n"
        + "## Harness Builder 推荐补齐项\n\n"
        + f"{recommended_lines}\n\n"
        + "## 成熟度缺口关联\n\n"
        + f"{_maturity_gap_lines(inventory, commands, interaction_decisions)}\n\n"
        + "## 人工确认点\n\n"
        + "- 请确认模块边界是否符合团队真实架构。\n"
        + "- 请确认候选规则是否可以提升为正式 Guide。\n"
    )


def _team_context_section(context_inputs: dict[str, Any] | None, interaction_decisions: InteractionDecisions | None) -> str:
    lines: list[str] = []
    for item in (context_inputs or {}).get("contexts", []):
        lines.append(f"- `{item['path']}`: {item['summary']}")
    if interaction_decisions:
        for item in interaction_decisions.context_confirmation.inline_contexts:
            lines.append(f"- {item}")
    return "\n".join(lines) or "- 暂未提供团队上下文。"


def _human_override_section(inventory: ProjectInventory, interaction_decisions: InteractionDecisions | None) -> str:
    lines: list[str] = []
    overrides = inventory.stack_extensions.get("human_overrides", {})
    if isinstance(overrides, dict):
        for note in overrides.get("scan_notes", []) or []:
            lines.append(f"- 扫描修正：{note}")
        if overrides.get("primary_stack"):
            lines.append(f"- 主要技术栈人工修正为：`{overrides['primary_stack']}`。")
    if interaction_decisions:
        for note in interaction_decisions.scan_confirmation.notes:
            if f"- 扫描修正：{note}" not in lines:
                lines.append(f"- 扫描修正：{note}")
        if interaction_decisions.workflow_confirmation.shown_workflows:
            lines.append(
                "- 已向用户展示推荐工作流："
                + ", ".join(f"`{item}`" for item in interaction_decisions.workflow_confirmation.shown_workflows)
                + "。"
            )
        for note in interaction_decisions.workflow_confirmation.notes:
            lines.append(f"- Workflow 补充：{note}")
    return "\n".join(lines) or "- 暂无人工修正。"


def _task_template(kind: str) -> str:
    title = "缺陷修复任务模板" if kind == "bugfix" else "轻量级任务模板"
    return (
        _frontmatter("task_template")
        + f"# {title}\n\n"
        + "1. 复述任务和期望结果。\n"
        + "2. 映射影响模块、必读 Guides 和 Workflow Skill。\n"
        + "3. 执行选定的 hard gate Sensors。\n"
        + "4. 输出 decision log、sensor report 和 handoff summary。\n"
    )


def _weapon_match_lines(weapons: list[WeaponLibraryEntry]) -> str:
    return "\n".join(f"- `{weapon.id}`：{weapon.title}。" for weapon in weapons) or "- 暂未命中武器库条目。"


def _guide_rule_lines(weapons: list[WeaponLibraryEntry]) -> str:
    return "\n".join(f"- `{weapon.id}`：{weapon.guidance}" for weapon in weapons) or "- 当前技术栈置信度不足，所有规则先保持 candidate 状态。"


def _risk_area_lines(inventory: ProjectInventory) -> str:
    risk_areas = inventory.stack_extensions.get("risk_areas", [])
    lines: list[str] = []
    if isinstance(risk_areas, list):
        for item in risk_areas:
            if isinstance(item, dict):
                signal = classify_risk_area(item)
                if signal.is_high_impact:
                    lines.append(
                        f"- 【待确认高风险】`{signal.path}`：{signal.reason}；"
                        f"{signal.confirmation_reason} 维护者确认前不得当作已确认事实，"
                        "命中后建议进入 standard workflow / 人工升级。"
                    )
                else:
                    lines.append(f"- `{signal.path}`：{signal.reason}")
    return "\n".join(lines) or "- 当前扫描未确认具体风险区域，变更前仍需维护者确认影响面。"


def _validation_entry_lines(commands: CommandCatalog) -> str:
    lines = [
        f"- `{command.id}`：`{command.command}`，type=`{command.type}`，gate=`{command.gate}`，source=`{command.source}`，confidence=`{command.confidence}`。"
        for command in commands.commands
    ]
    return "\n".join(lines) or "- 当前扫描未确认可执行验证入口，建议维护者补充 build/test/lint/typecheck 命令。"


def _maturity_gap_lines(
    inventory: ProjectInventory,
    commands: CommandCatalog,
    interaction_decisions: InteractionDecisions | None,
) -> str:
    lines = [
        "- Guides 已记录模块、证据、风险区域和团队上下文，用于补齐项目事实可审计性。",
    ]
    if commands.commands:
        hard_count = sum(1 for command in commands.commands if command.gate == "hard")
        lines.append(f"- Sensors 可基于 `{len(commands.commands)}` 个验证入口建立初始验证策略，其中 hard gate `{hard_count}` 个。")
    else:
        lines.append("- Sensors 仍缺少可执行验证入口，这是进入更高成熟度前的优先缺口。")
    if _risk_area_lines(inventory).startswith("- 当前扫描未确认"):
        lines.append("- 风险控制仍缺少已确认风险区域，后续应通过人工补充或候选治理完善。")
    else:
        lines.append("- 风险区域已进入 Guide，后续任务命中这些路径时应优先升级验证和工作流。")
    if interaction_decisions and (
        interaction_decisions.scan_confirmation.notes
        or interaction_decisions.context_confirmation.inline_contexts
        or interaction_decisions.workflow_confirmation.notes
    ):
        lines.append("- 用户补充已进入正式 Guide 与 human-input 记录，用于后续成熟度复评和改进候选。")
    else:
        lines.append("- 当前没有用户补充，后续维护入口应继续收集团队规则和任务边界。")
    return "\n".join(lines)
