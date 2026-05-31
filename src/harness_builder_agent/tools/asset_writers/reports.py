from __future__ import annotations

from pathlib import Path

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.interaction_decision import InteractionDecisions
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_text, write_yaml
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.init_summary import write_init_summary
from harness_builder_agent.tools.maturity_evidence import build_maturity_evidence_pack
from harness_builder_agent.tools.maturity_model import build_maturity_report


def write_report_assets(
    ai: Path,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    config: HarnessConfig,
    weapon_selection: WeaponLibrarySelection,
    interaction_decisions: InteractionDecisions | None = None,
    trace: GenerationTrace | None = None,
) -> None:
    maturity = build_maturity_report(
        ai=None,
        inventory=inventory,
        commands=commands,
        config=config,
        weapon_selection=weapon_selection,
    )
    write_text(ai / "scan-report.md", _scan_report(inventory, commands))
    record_artifact(trace, ai / "scan-report.md", "report")
    write_text(ai / "maturity-report.md", _maturity_report(maturity))
    record_artifact(trace, ai / "maturity-report.md", "report")
    record_artifact(
        trace,
        write_init_summary(
            ai,
            maturity,
            inventory=inventory,
            commands=commands,
            interaction_decisions=interaction_decisions,
        ),
        "init_summary",
    )
    write_yaml(ai / "maturity-score.yaml", maturity.model_dump(mode="json"))
    record_artifact(trace, ai / "maturity-score.yaml", "maturity_score")
    evidence = build_maturity_evidence_pack(
        ai=ai,
        inventory=inventory,
        commands=commands,
        config=config,
        weapon_selection=weapon_selection,
    )
    write_yaml(ai / "maturity-evidence.yaml", evidence.model_dump(mode="json"))
    record_artifact(trace, ai / "maturity-evidence.yaml", "maturity_evidence")
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


def _maturity_report(score: MaturityReport) -> str:
    dimensions = "\n".join(f"- {name}: {level}" for name, level in score.dimension_scores.items())
    evidence = "\n".join(f"- {item}" for item in score.evidence)
    blockers = "\n".join(f"- {item}" for item in score.blocking_reasons)
    next_steps = "\n".join(f"- {item}" for item in score.recommended_next_steps)
    dimension_details = "\n".join(_dimension_detail(name, report) for name, report in score.dimensions.items())
    next_level_requirements = "\n".join(
        f"- {name}: {requirement}"
        for name, report in score.dimensions.items()
        for requirement in report.next_level_requirements
    )
    return (
        "# 成熟度评估报告\n\n"
        f"整体等级：`{score.overall_level}`\n\n"
        f"下一目标等级：`{score.target_next_level or score.overall_level}`\n\n"
        "## 评分维度\n\n"
        f"{dimensions}\n\n"
        "## 证据\n\n"
        f"{evidence}\n\n"
        "## 阻断原因\n\n"
        f"{blockers}\n\n"
        "## 维度详情\n\n"
        f"{dimension_details}\n\n"
        "## 下一等级要求\n\n"
        f"{next_level_requirements}\n\n"
        "## 推荐下一步\n\n"
        f"{next_steps}\n"
    )


def _dimension_detail(name: str, report) -> str:
    evidence = "; ".join(f"{item.source}: {item.summary}" for item in report.evidence) or "无"
    blockers = "; ".join(item.reason for item in report.blockers) or "无"
    return f"- {name}: {report.level}\n  - evidence: {evidence}\n  - blockers: {blockers}"


def _evolution_plan() -> str:
    return (
        "# 演进计划\n\n"
        "1. 确认生成的项目上下文、架构说明和编码规则。\n"
        "2. 在开发机验证命令候选，并将稳定命令提升为 hard gate。\n"
        "3. 为重复出现的任务模式补充任务特定 Sensor。\n"
    )
