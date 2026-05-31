from __future__ import annotations

from pathlib import Path

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.interaction_decision import InteractionDecisions
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_text, write_yaml
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.init_summary import write_init_summary
from harness_builder_agent.tools.maturity_evidence import build_maturity_evidence_pack
from harness_builder_agent.tools.maturity_model import build_maturity_report
from harness_builder_agent.tools.maturity_rendering import render_maturity_report_markdown


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
    write_text(ai / "maturity-report.md", render_maturity_report_markdown(maturity))
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


def _evolution_plan() -> str:
    return (
        "# 演进计划\n\n"
        "1. 确认生成的项目上下文、架构说明和编码规则。\n"
        "2. 在开发机验证命令候选，并将稳定命令提升为 hard gate。\n"
        "3. 为重复出现的任务模式补充任务特定 Sensor。\n"
    )
