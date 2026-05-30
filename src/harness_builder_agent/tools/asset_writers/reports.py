from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_text, write_yaml
from harness_builder_agent.tools.generation_trace import GenerationTrace


def write_report_assets(
    ai: Path,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    config: HarnessConfig,
    weapon_selection: WeaponLibrarySelection,
    trace: GenerationTrace | None = None,
) -> None:
    write_text(ai / "scan-report.md", _scan_report(inventory, commands))
    record_artifact(trace, ai / "scan-report.md", "report")
    write_text(ai / "maturity-report.md", _maturity_report(inventory, commands, weapon_selection))
    record_artifact(trace, ai / "maturity-report.md", "report")
    write_yaml(ai / "maturity-score.yaml", _maturity_score(inventory, commands, config, weapon_selection))
    record_artifact(trace, ai / "maturity-score.yaml", "maturity_score")
    write_text(ai / "evolution-plan.md", _evolution_plan())
    record_artifact(trace, ai / "evolution-plan.md", "plan")


def _scan_report(inventory: ProjectInventory, commands: CommandCatalog) -> str:
    command_lines = "\n".join(f"- `{command.command}` from `{command.source}`" for command in commands.commands) or "- No commands detected"
    evidence_lines = "\n".join(f"- `{item['path']}`: {item['reason']}" for item in inventory.evidence) or "- No evidence detected"
    return (
        "# Scan Report\n\n"
        f"Repository: `{inventory.repo_name}`\n\n"
        f"Primary stack: `{inventory.primary_stack}`\n\n"
        "## Evidence\n\n"
        f"{evidence_lines}\n\n"
        "## Command Candidates\n\n"
        f"{command_lines}\n"
    )


def _maturity_report(inventory: ProjectInventory, commands: CommandCatalog, weapon_selection: WeaponLibrarySelection) -> str:
    level = "L2" if commands.commands else "L1"
    return (
        "# 成熟度评估报告\n\n"
        f"整体等级：`{level}`\n\n"
        "## 评分维度\n\n"
        "- Guides: L1\n"
        f"- Sensors: {'L2' if commands.commands else 'L0'}\n"
        "- Workflow: L2\n"
        "- Risk Control: L0\n"
        "- Observability: L1\n"
        "- Experience: L0\n\n"
        "## 证据\n\n"
        f"- 已识别技术栈：`{inventory.primary_stack}`。\n"
        f"- 已识别验证命令数量：{len(commands.commands)}。\n"
        f"- 已命中武器库：{len(weapon_selection.guide_weapon_ids)} 条 Guide，{len(weapon_selection.sensor_weapon_ids)} 条 Sensor。\n"
        "- 已生成项目级 Workflow Skill，但尚未接入完整 IDE Runtime。\n\n"
        "## 阻断原因\n\n"
        "- 风险目录和团队规则仍需要人工确认。\n"
        "- Sensor 失败后的自动修复闭环仍处于 POC 状态。\n\n"
        "## 推荐下一步\n\n"
        "- 由维护者确认核心风险目录和候选规则。\n"
        "- 将稳定的测试命令提升为 hard gate。\n"
        "- 根据真实任务结果审查 experience candidates。\n"
    )


def _maturity_score(
    inventory: ProjectInventory, commands: CommandCatalog, config: HarnessConfig, weapon_selection: WeaponLibrarySelection
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "overall_level": "L2" if commands.commands else "L1",
        "dimension_scores": {
            "guides": "L1",
            "sensors": "L2" if commands.commands else "L0",
            "workflow": "L2" if config.workflows else "L0",
            "risk_control": "L0",
            "observability": "L1",
            "experience": "L0",
        },
        "evidence": [
            f"识别到主技术栈：{inventory.primary_stack}",
            f"识别到模块数量：{len(inventory.modules)}",
            f"识别到验证命令数量：{len(commands.commands)}",
            f"命中武器库：Guide {len(weapon_selection.guide_weapon_ids)} 条，Sensor {len(weapon_selection.sensor_weapon_ids)} 条",
            "已生成 lightweight 与 bugfix Workflow Skill",
        ],
        "blocking_reasons": [
            "候选 Guides / Sensors 尚未经过维护者确认",
            "Sensor 结果尚未形成长期趋势数据",
        ],
        "recommended_next_steps": [
            "审查并确认候选规则",
            "补齐缺失的 lint / typecheck / 安全检查",
            "基于真实任务记录运行 improve",
        ],
    }


def _evolution_plan() -> str:
    return (
        "# 演进计划\n\n"
        "1. 确认生成的项目上下文、架构说明和编码规则。\n"
        "2. 在开发机验证命令候选，并将稳定命令提升为 hard gate。\n"
        "3. 为重复出现的任务模式补充任务特定 Sensor。\n"
    )
