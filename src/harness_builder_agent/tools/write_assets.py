from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibraryEntry, WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.core import llm_scan_proposal, scan_metadata, write_core_assets
from harness_builder_agent.tools.asset_writers.guides import write_guide_assets
from harness_builder_agent.tools.asset_writers.human_confirmation import write_human_confirmation_assets
from harness_builder_agent.tools.asset_writers.reports import write_report_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.human_confirmation import build_questionnaire, read_context_inputs
from harness_builder_agent.tools.llm_enhancement_candidates import (
    build_llm_enhancement_candidates,
    candidate_guides_markdown,
    candidate_sensors_markdown,
    enhancement_summary_markdown,
)
from harness_builder_agent.tools.weapon_library import select_weapon_library


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def write_initial_assets(
    repo: Path,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    trace: GenerationTrace | None = None,
    context_paths: list[Path] | None = None,
) -> Path:
    ai = repo / ".ai"
    config = HarnessConfig.default()
    weapon_selection = select_weapon_library(inventory, commands)
    scan_metadata_payload = scan_metadata(inventory)
    llm_scan_proposal_payload = llm_scan_proposal(inventory)
    context_inputs = read_context_inputs(context_paths or [])
    questionnaire = build_questionnaire(context_inputs, scan_metadata_payload)
    enhancement_candidates = build_llm_enhancement_candidates(inventory, commands)
    if trace:
        trace.event(
            "weapon-selection",
            "completed",
            "Weapon library selection completed.",
            {
                "source": weapon_selection.source,
                "selected_stacks": weapon_selection.selected_stacks,
                "guide_weapon_count": len(weapon_selection.guide_weapon_ids),
                "sensor_weapon_count": len(weapon_selection.sensor_weapon_ids),
            },
        )
        trace.event("asset-write", "started", "Initial harness asset writing started.")

    write_core_assets(
        ai,
        inventory,
        commands,
        config,
        scan_metadata_payload,
        llm_scan_proposal_payload,
        weapon_selection,
        trace=trace,
    )
    write_human_confirmation_assets(ai, context_inputs, questionnaire, trace=trace)
    if trace:
        trace.event(
            "human-confirmation",
            "completed",
            "Human confirmation assets generated.",
            {"context_count": len(context_inputs["contexts"]), "question_count": len(questionnaire["questions"])},
        )

    write_report_assets(ai, inventory, commands, config, weapon_selection, trace=trace)

    write_guide_assets(ai, inventory, weapon_selection, trace=trace)

    _write_text(ai / "sensors" / "verification.md", _sensor_doc(commands, weapon_selection))
    _record_artifact(trace, ai / "sensors" / "verification.md", "sensor")
    _write_text(ai / "sensors" / "test-strategy.md", _test_strategy(commands, weapon_selection))
    _record_artifact(trace, ai / "sensors" / "test-strategy.md", "sensor")
    _copy_workflow_skills(ai)
    _record_artifact(trace, ai / "skills" / "lightweight" / "SKILL.md", "skill")
    _record_artifact(trace, ai / "skills" / "bugfix" / "SKILL.md", "skill")
    _write_text(ai / "experience" / "pending-improvements.md", "# Pending Improvements\n\nNo reviewed improvements yet.\n")
    _record_artifact(trace, ai / "experience" / "pending-improvements.md", "experience")
    _write_yaml(ai / "experience" / "weapon-library-candidates.yaml", enhancement_candidates)
    _record_artifact(trace, ai / "experience" / "weapon-library-candidates.yaml", "weapon_library_candidates")
    _write_text(ai / "review" / "llm-enhancement-candidates.md", enhancement_summary_markdown(enhancement_candidates))
    _record_artifact(trace, ai / "review" / "llm-enhancement-candidates.md", "review")
    _write_text(ai / "review" / "candidate-guides.md", candidate_guides_markdown(enhancement_candidates))
    _record_artifact(trace, ai / "review" / "candidate-guides.md", "review")
    _write_text(ai / "review" / "candidate-sensors.md", candidate_sensors_markdown(enhancement_candidates))
    _record_artifact(trace, ai / "review" / "candidate-sensors.md", "review")
    if trace:
        trace.event("asset-write", "completed", "Initial harness asset writing completed.", {"artifact_count": len(trace.artifacts)})
    return ai


def _record_artifact(trace: GenerationTrace | None, path: Path, kind: str) -> None:
    if trace:
        trace.artifact(path, kind)


def _sensor_doc(commands: CommandCatalog, weapon_selection: WeaponLibrarySelection) -> str:
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
        "## 缺失验证能力\n\n"
        f"{missing}\n\n"
        "## 推荐验证活动\n\n"
        f"{recommendation_lines}\n\n"
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


def _copy_workflow_skills(ai: Path) -> None:
    template_root = files("harness_builder_agent").joinpath("templates", "skills")
    for name in ("lightweight", "bugfix"):
        content = template_root.joinpath(name, "SKILL.md").read_text(encoding="utf-8")
        _write_text(ai / "skills" / name / "SKILL.md", content)


def _weapon_match_lines(weapons: list[WeaponLibraryEntry]) -> str:
    return "\n".join(f"- `{weapon.id}`：{weapon.title}。" for weapon in weapons) or "- 暂未命中武器库条目。"


def _missing_sensor_lines(commands: CommandCatalog) -> str:
    present_types = {command.type for command in commands.commands}
    missing = []
    for sensor_type in ("lint", "typecheck", "security"):
        if sensor_type not in present_types:
            missing.append(f"- `{sensor_type}`：当前未发现稳定命令，建议人工确认后补齐。")
    return "\n".join(missing) if missing else "- 暂未发现明显缺失项。"
