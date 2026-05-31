from __future__ import annotations

from pathlib import Path
from typing import Any

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
    command_lines = "\n".join(
        f"- `{command.gate}` `{command.type}` `{command.id}`: `{command.command}` "
        f"(source=`{command.source}`, confidence=`{command.confidence}`)"
        for command in commands.commands
    ) or "- No commands detected"
    return (
        "# Scan Report\n\n"
        f"Repository: `{inventory.repo_name}`\n\n"
        f"Primary stack: `{inventory.primary_stack}`\n\n"
        "## Evidence\n\n"
        f"{_scan_evidence_lines(inventory)}\n\n"
        "## LLM Evidence Expansion\n\n"
        f"{_llm_evidence_expansion_lines(inventory)}\n\n"
        "## Evidence Coverage\n\n"
        f"{_evidence_coverage_lines(inventory)}\n\n"
        "## Stack Evidence Validation\n\n"
        f"{_stack_validation_lines(inventory)}\n\n"
        "## Scan Warnings\n\n"
        f"{_scan_warning_lines(inventory)}\n\n"
        "## Risk Areas\n\n"
        f"{_risk_area_lines(inventory)}\n\n"
        "## Command Candidates\n\n"
        f"{command_lines}\n"
    )


def _scan_evidence_lines(inventory: ProjectInventory) -> str:
    lines: list[str] = []
    seen_paths: set[str] = set()
    for bucket in (inventory.evidence, inventory.documents, inventory.configs, inventory.ci_files):
        for item in bucket:
            path = str(item.get("path") or "").strip()
            if not path or path in seen_paths:
                continue
            seen_paths.add(path)
            reason = str(item.get("reason") or item.get("kind") or "evidence").strip()
            lines.append(f"- `{path}`: {reason}")
    return "\n".join(lines) or "- No evidence detected"


def _llm_evidence_expansion_lines(inventory: ProjectInventory) -> str:
    plan = _inventory_evidence_expansion(inventory)
    if not plan:
        return "- evidence_expansion=not_run"
    requested_paths = _plan_list_value(plan, "requested_paths")
    read_paths = _plan_list_value(plan, "read_paths")
    risk_focus = _plan_list_value(plan, "risk_focus")
    confidence = _plan_scalar_value(plan, "confidence") or "unknown"
    rationale = _plan_scalar_value(plan, "rationale") or "not_available"
    read_file_count = _plan_scalar_value(plan, "read_file_count") or str(len(read_paths))
    return "\n".join(
        [
            f"- requested_paths={_inline_code_list(requested_paths)}",
            f"- read_paths={_inline_code_list(read_paths)}",
            f"- risk_focus={_inline_code_list(risk_focus)}",
            f"- confidence=`{confidence}`",
            f"- read_file_count={read_file_count}",
            f"- rationale={rationale}",
        ]
    )


def _evidence_coverage_lines(inventory: ProjectInventory) -> str:
    metadata = _scan_metadata(inventory)
    coverage = metadata.get("coverage") if metadata else None
    if not isinstance(coverage, dict):
        return "- evidence_coverage=not_available"
    selected = coverage.get("selected_evidence_count", "unknown")
    detected = coverage.get("detected_file_count", metadata.get("evidence_file_count", "unknown"))
    lines = [f"- evidence_selected={selected}/{detected}"]
    buckets = coverage.get("bucket_coverage")
    if isinstance(buckets, list) and buckets:
        for bucket in buckets[:12]:
            if not isinstance(bucket, dict):
                continue
            selected_paths = _inline_code_list([str(item) for item in bucket.get("selected_paths", []) or []])
            lines.append(
                "- "
                f"`{bucket.get('bucket', 'unknown')}`: "
                f"selected={bucket.get('selected_count', 0)} "
                f"total={bucket.get('total_count', 0)} "
                f"skipped={bucket.get('skipped_count', 0)} "
                f"selected_paths={selected_paths}"
            )
    else:
        lines.append("- bucket_coverage=not_available")
    return "\n".join(lines)


def _stack_validation_lines(inventory: ProjectInventory) -> str:
    validation = inventory.stack_extensions.get("scan_validation")
    if not isinstance(validation, dict):
        return "- scan_validation=not_available"
    lines = [
        f"- checked_claims={_inline_code_list(_list_value(validation, 'checked_claims'))}",
        f"- supported_claims={_inline_code_list(_list_value(validation, 'supported_claims'))}",
    ]
    unsupported = validation.get("unsupported_claims")
    if isinstance(unsupported, list) and unsupported:
        for item in unsupported[:8]:
            if isinstance(item, dict):
                stack = str(item.get("stack") or "unknown")
                reason = str(item.get("reason") or "No supporting evidence was found.")
                lines.append(f"- unsupported_claim=`{stack}`: {reason}")
    else:
        lines.append("- unsupported_claims=none")
    return "\n".join(lines)


def _scan_warning_lines(inventory: ProjectInventory) -> str:
    warnings = inventory.stack_extensions.get("scan_warnings")
    if not isinstance(warnings, list) or not warnings:
        metadata = _scan_metadata(inventory)
        warnings = metadata.get("warnings", []) if metadata else []
    if not isinstance(warnings, list) or not warnings:
        return "- scan_warnings=none"
    lines: list[str] = []
    for warning in warnings[:12]:
        if not isinstance(warning, dict):
            continue
        code = str(warning.get("code") or "unknown")
        severity = str(warning.get("severity") or "warning")
        message = str(warning.get("message") or "")
        evidence = warning.get("evidence")
        evidence_text = ""
        if isinstance(evidence, list) and evidence:
            evidence_text = " evidence=" + _inline_code_list([str(item) for item in evidence])
        lines.append(f"- `{severity}` `{code}`: {message}{evidence_text}")
    return "\n".join(lines) or "- scan_warnings=none"


def _risk_area_lines(inventory: ProjectInventory) -> str:
    risk_areas = inventory.stack_extensions.get("risk_areas", [])
    if not isinstance(risk_areas, list) or not risk_areas:
        proposal = inventory.stack_extensions.get("llm_scan_proposal", {})
        if isinstance(proposal, dict):
            risk_areas = proposal.get("risk_areas", [])
    if not isinstance(risk_areas, list) or not risk_areas:
        return "- No explicit risk areas detected; maintainers should still confirm business-critical paths."
    lines: list[str] = []
    for risk in risk_areas[:12]:
        if not isinstance(risk, dict):
            continue
        path = str(risk.get("path") or risk.get("area") or "unknown")
        reason = str(risk.get("reason") or risk.get("summary") or "Needs maintainer confirmation.")
        lines.append(f"- `{path}`: {reason}")
    return "\n".join(lines) or "- No explicit risk areas detected; maintainers should still confirm business-critical paths."


def _inventory_evidence_expansion(inventory: ProjectInventory) -> Any:
    metadata = _scan_metadata(inventory)
    if not metadata:
        return None
    return metadata.get("evidence_expansion") or metadata.get("evidence_expansion_plan")


def _scan_metadata(inventory: ProjectInventory) -> dict[str, Any]:
    metadata = inventory.stack_extensions.get("scan_metadata", {})
    return metadata if isinstance(metadata, dict) else {}


def _inline_code_list(items: list[str]) -> str:
    return ", ".join(f"`{item}`" for item in items) if items else "none"


def _list_value(container: dict[str, Any], field: str) -> list[str]:
    value = container.get(field)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _plan_list_value(plan: Any, field: str) -> list[str]:
    value = plan.get(field) if isinstance(plan, dict) else getattr(plan, field, None)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _plan_scalar_value(plan: Any, field: str) -> str:
    value = plan.get(field) if isinstance(plan, dict) else getattr(plan, field, None)
    return str(value).strip() if value is not None else ""


def _evolution_plan() -> str:
    return (
        "# 演进计划\n\n"
        "1. 确认生成的项目上下文、架构说明和编码规则。\n"
        "2. 在开发机验证命令候选，并将稳定命令提升为 hard gate。\n"
        "3. 为重复出现的任务模式补充任务特定 Sensor。\n"
    )
