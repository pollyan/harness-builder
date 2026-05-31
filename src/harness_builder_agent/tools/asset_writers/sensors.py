from __future__ import annotations

from pathlib import Path

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibraryEntry, WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_text
from harness_builder_agent.tools.generation_trace import GenerationTrace


def write_sensor_assets(
    ai: Path,
    commands: CommandCatalog,
    weapon_selection: WeaponLibrarySelection,
    inventory: ProjectInventory | None = None,
    trace: GenerationTrace | None = None,
) -> None:
    write_text(ai / "sensors" / "verification.md", _sensor_doc(commands, weapon_selection, inventory))
    record_artifact(trace, ai / "sensors" / "verification.md", "sensor")
    write_text(ai / "sensors" / "test-strategy.md", _test_strategy(commands, weapon_selection))
    record_artifact(trace, ai / "sensors" / "test-strategy.md", "sensor")


def _sensor_doc(commands: CommandCatalog, weapon_selection: WeaponLibrarySelection, inventory: ProjectInventory | None) -> str:
    command_lines = "\n".join(
        f"- `{command.id}`：`{command.command}`，gate=`{command.gate}`，来源 `{command.source}`，verified={command.verified}"
        for command in commands.commands
    ) or "- 暂未发现可执行验证命令"
    missing = _missing_sensor_lines(commands)
    match_lines = _weapon_match_lines(weapon_selection.sensor_weapons)
    recommendation_lines = "\n".join(
        f"- `{weapon.id}`：{weapon.recommended_action} gate=`{weapon.gate}`" for weapon in weapon_selection.sensor_weapons
    )
    return (
        "# 验证 Sensors\n\n"
        "## 武器库匹配结果\n\n"
        f"- 来源：`{weapon_selection.source}`。\n"
        + f"- 已选择技术栈：{', '.join(f'`{stack}`' for stack in weapon_selection.selected_stacks)}。\n"
        + f"{match_lines}\n\n"
        "## 已发现的验证命令\n\n"
        f"{command_lines}\n\n"
        "## 风险与验证映射\n\n"
        f"{_risk_validation_lines(inventory, commands)}\n\n"
        "## 缺失验证能力\n\n"
        f"{missing}\n\n"
        "## 推荐验证活动\n\n"
        f"{recommendation_lines}\n\n"
        "## 成熟度缺口关联\n\n"
        f"{_maturity_gap_lines(inventory, commands)}\n\n"
        "## 失败处理策略\n\n"
        "- hard gate 失败时任务保持未完成状态，并记录摘要和人工下一步。\n"
        "- soft signal 失败时进入 handoff summary，不直接阻断 POC 链路。\n"
        "- 本机缺少执行环境时记录 skipped，不编造通过结果。\n"
    )


def _test_strategy(commands: CommandCatalog, weapon_selection: WeaponLibrarySelection) -> str:
    hard_gates = [command for command in commands.commands if command.gate == "hard"]
    lines = "\n".join(f"- `{command.command}`" for command in hard_gates) or "- Confirm test strategy with maintainer"
    sensor_lines = "\n".join(
        f"- `{weapon.id}`：{weapon.guidance}" for weapon in weapon_selection.sensor_weapons if weapon.gate == "hard"
    )
    return (
        "# 测试策略\n\n"
        "## Hard Gates\n\n"
        + lines
        + "\n\n## 武器库建议\n\n"
        + (sensor_lines or "- 暂无 hard gate 武器。")
        + "\n\n## 人工确认点\n\n- 请确认这些命令在团队开发机和 CI 中是否稳定。\n"
    )


def _weapon_match_lines(weapons: list[WeaponLibraryEntry]) -> str:
    return "\n".join(f"- `{weapon.id}`：{weapon.title}。" for weapon in weapons) or "- 暂未命中武器库条目。"


def _missing_sensor_lines(commands: CommandCatalog) -> str:
    present_types = {command.type for command in commands.commands}
    missing = []
    for sensor_type in ("lint", "typecheck", "security"):
        if sensor_type not in present_types:
            missing.append(f"- `{sensor_type}`：当前未发现稳定命令，建议人工确认后补齐。")
    return "\n".join(missing) if missing else "- 暂未发现明显缺失项。"


def _risk_validation_lines(inventory: ProjectInventory | None, commands: CommandCatalog) -> str:
    hard_commands = [command for command in commands.commands if command.gate == "hard"]
    command_hint = ", ".join(f"`{command.command}`" for command in hard_commands) or "已确认的 hard gate"
    risk_areas = _risk_areas(inventory)
    if not risk_areas:
        return "- 当前扫描未确认具体风险区域；任务命中高影响文件时仍应记录验证选择和 skipped 原因。"
    return "\n".join(
        f"- `{path}`：{reason}；命中该区域时优先运行 {command_hint}，缺少环境时记录 skipped 和人工下一步。"
        for path, reason in risk_areas
    )


def _maturity_gap_lines(inventory: ProjectInventory | None, commands: CommandCatalog) -> str:
    lines: list[str] = []
    if commands.commands:
        lines.append("- 已发现验证命令可支撑初始 Sensors 基线，但仍需维护者确认本地和 CI 稳定性。")
    else:
        lines.append("- 当前没有可执行验证命令，Sensor 成熟度仍受阻。")
    if _risk_areas(inventory):
        lines.append("- 风险区域已经映射到验证策略，后续可继续把高风险路径绑定到 workflow escalation。")
    else:
        lines.append("- 风险区域尚未确认，后续应补充风险路径以增强验证选择。")
    return "\n".join(lines)


def _risk_areas(inventory: ProjectInventory | None) -> list[tuple[str, str]]:
    if inventory is None:
        return []
    raw_items = inventory.stack_extensions.get("risk_areas", [])
    if not isinstance(raw_items, list):
        return []
    items: list[tuple[str, str]] = []
    for item in raw_items:
        if isinstance(item, dict):
            items.append((str(item.get("path") or "unknown"), str(item.get("reason") or "当前扫描提示需要人工确认。")))
    return items
