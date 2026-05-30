from __future__ import annotations

from pathlib import Path

from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibraryEntry, WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_text
from harness_builder_agent.tools.generation_trace import GenerationTrace


def write_guide_assets(
    ai: Path,
    inventory: ProjectInventory,
    weapon_selection: WeaponLibrarySelection,
    trace: GenerationTrace | None = None,
) -> None:
    write_text(ai / "guides" / "project-context.md", _guide("project-context", inventory, weapon_selection))
    record_artifact(trace, ai / "guides" / "project-context.md", "guide")
    write_text(ai / "guides" / "coding-rules.md", _guide("coding-rules", inventory, weapon_selection))
    record_artifact(trace, ai / "guides" / "coding-rules.md", "guide")
    write_text(ai / "guides" / "architecture.md", _guide("architecture", inventory, weapon_selection))
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


def _guide(name: str, inventory: ProjectInventory, weapon_selection: WeaponLibrarySelection) -> str:
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
        + "## 当前项目事实\n\n"
        + f"- 主技术栈：`{inventory.primary_stack}`。\n"
        + f"- 技术栈线索：{', '.join(inventory.stacks) if inventory.stacks else '未知'}。\n"
        + "- 模块识别：\n"
        + f"{module_lines}\n\n"
        + "## 来源证据\n\n"
        + f"{evidence_lines}\n\n"
        + "## 候选规则\n\n"
        + f"{_guide_rule_lines(weapon_selection.guide_weapons)}\n\n"
        + "## Harness Builder 推荐补齐项\n\n"
        + f"{recommended_lines}\n\n"
        + "## 人工确认点\n\n"
        + "- 请确认模块边界是否符合团队真实架构。\n"
        + "- 请确认候选规则是否可以提升为正式 Guide。\n"
    )


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
