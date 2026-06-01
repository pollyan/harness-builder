from __future__ import annotations

import typer

from harness_builder_agent.schemas.interaction_decision import WorkflowConfirmation
from harness_builder_agent.tools.prewrite_preview import GuidedScanOverrides, has_scan_overrides


def show_scan_supplement_immediate_summary(scan_overrides: GuidedScanOverrides) -> None:
    if not has_scan_overrides(scan_overrides):
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


def show_scan_back_revision_notice(previous_scan_overrides: GuidedScanOverrides) -> None:
    if not has_scan_overrides(previous_scan_overrides):
        return
    typer.echo("\n扫描补充返回修改")
    typer.echo("- 你将基于原始扫描结果重新填写扫描补充。")
    typer.echo("- 新输入会替换上一版扫描补充；直接回车会清空上一版补充，并按扫描基线继续。")
    summary = scan_override_brief(previous_scan_overrides)
    if summary:
        typer.echo(f"- 上一版补充摘要：{summary}")


def show_scan_supplement_cleared_summary() -> None:
    typer.echo("\n扫描补充已清空")
    typer.echo("- 已移除上一版扫描补充；后续预览和正式资产将按扫描基线、团队规则和候选决策继续。")


def show_scan_supplement_replacement_summary(
    previous_scan_overrides: GuidedScanOverrides,
    current_scan_overrides: GuidedScanOverrides,
) -> None:
    if not has_scan_overrides(previous_scan_overrides) or not has_scan_overrides(current_scan_overrides):
        return
    previous_summary = scan_override_brief(previous_scan_overrides)
    current_summary = scan_override_brief(current_scan_overrides)
    if not previous_summary or not current_summary:
        return
    typer.echo("\n扫描补充替换结果")
    typer.echo(f"- 上一版补充：{previous_summary}")
    typer.echo(f"- 当前生效补充：{current_summary}")
    typer.echo("- 最终写入只会使用当前生效补充；上一版补充不会进入 project inventory、command catalog、Guides、Sensors 或 init summary。")


def scan_override_brief(scan_overrides: GuidedScanOverrides) -> str:
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


def show_team_rules_immediate_summary(inline_contexts: list[str]) -> None:
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


def show_team_rules_back_revision_notice(previous_inline_contexts: list[str]) -> None:
    if not previous_inline_contexts:
        return
    typer.echo("\n团队规则返回修改")
    typer.echo("- 你将重新填写团队规则。")
    typer.echo("- 新输入会替换上一版团队规则；直接回车会清空上一版团队规则。")
    typer.echo(f"- 上一版团队规则摘要：{brief_text_items(previous_inline_contexts)}")


def show_team_rules_cleared_summary() -> None:
    typer.echo("\n团队规则已清空")
    typer.echo("- 已移除上一版团队规则；后续预览和正式资产将不再保留这些团队规则。")


def show_workflow_note_immediate_summary(workflow_confirmation: WorkflowConfirmation) -> None:
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


def show_workflow_back_revision_notice(previous_workflow_confirmation: WorkflowConfirmation) -> None:
    if not previous_workflow_confirmation.notes:
        return
    typer.echo("\nWorkflow 补充返回修改")
    typer.echo("- 你将重新填写 Workflow 补充。")
    typer.echo("- 新输入会替换上一版 Workflow 补充；直接回车会清空上一版 Workflow 补充。")
    typer.echo(f"- 上一版 Workflow 补充摘要：{brief_text_items(previous_workflow_confirmation.notes)}")


def show_workflow_note_cleared_summary() -> None:
    typer.echo("\nWorkflow 补充已清空")
    typer.echo("- 已移除上一版 Workflow 补充；后续预览和正式资产将不再保留这些 Workflow 补充。")


def brief_text_items(items: list[str], *, limit: int = 2) -> str:
    shown = [item for item in items if item.strip()][:limit]
    if not shown:
        return "无"
    suffix = f"；还有 {len(items) - limit} 条" if len(items) > limit else ""
    return "；".join(shown) + suffix


def show_supplement_impact_summary(
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
