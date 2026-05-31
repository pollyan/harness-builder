from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.evidence_collector import collect_evidence, expand_evidence_with_requested_paths
from harness_builder_agent.tools.llm_evidence_planner import plan_evidence_expansion_with_llm
from harness_builder_agent.tools.llm_config import DeepSeekConfig
from harness_builder_agent.tools.llm_scan_analyzer import analyze_evidence_with_llm
from harness_builder_agent.tools.scan_reconciler import reconcile_scan


@dataclass(frozen=True)
class ScanProgressEvent:
    phase: str
    status: Literal["started", "completed"]
    message: str
    details: dict[str, object] = field(default_factory=dict)


ScanProgressCallback = Callable[[ScanProgressEvent], None]


def scan_repository(
    repo: Path,
    *,
    llm_caller: Callable[[list[dict[str, str]]], str] | None = None,
    evidence_planner_caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
    progress: ScanProgressCallback | None = None,
) -> tuple[ProjectInventory, CommandCatalog]:
    root = repo.resolve()
    _emit_progress(progress, "collect-evidence", "started", "Collecting repository evidence.")
    evidence = collect_evidence(root)
    _emit_progress(
        progress,
        "collect-evidence",
        "completed",
        "Repository evidence collected.",
        {"evidence_file_count": evidence.detected_file_count},
    )
    if evidence_planner_caller is not None or llm_caller is None:
        _emit_progress(progress, "plan-evidence-expansion", "started", "Planning evidence expansion with LLM.")
        plan = plan_evidence_expansion_with_llm(evidence, caller=evidence_planner_caller, config=config)
        _emit_progress(
            progress,
            "plan-evidence-expansion",
            "completed",
            "Evidence expansion plan completed.",
            {"requested_path_count": len(plan.requested_paths)},
        )
        _emit_progress(progress, "expand-evidence", "started", "Reading LLM requested evidence files.")
        evidence = expand_evidence_with_requested_paths(root, evidence, plan.requested_paths)
        _emit_progress(
            progress,
            "expand-evidence",
            "completed",
            "LLM requested evidence files read.",
            {"requested_path_count": len(plan.requested_paths), "llm_requested_file_count": len(evidence.llm_requested_files)},
        )
    _emit_progress(progress, "llm-scan", "started", "Requesting structured LLM scan.")
    proposal = analyze_evidence_with_llm(evidence, caller=llm_caller, config=config)
    _emit_progress(
        progress,
        "llm-scan",
        "completed",
        "Structured LLM scan completed.",
        {"primary_stack": proposal.primary_stack, "command_candidate_count": len(proposal.command_candidates)},
    )
    _emit_progress(progress, "reconcile-scan", "started", "Reconciling LLM scan with evidence.")
    inventory, commands, _metadata = reconcile_scan(
        evidence,
        proposal,
        model=config.model if config else None,
        base_url=config.base_url if config else None,
    )
    _emit_progress(
        progress,
        "reconcile-scan",
        "completed",
        "Scan reconciliation completed.",
        {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)},
    )
    return inventory, commands


def _emit_progress(
    progress: ScanProgressCallback | None,
    phase: str,
    status: Literal["started", "completed"],
    message: str,
    details: dict[str, object] | None = None,
) -> None:
    if progress is None:
        return
    progress(ScanProgressEvent(phase=phase, status=status, message=message, details=details or {}))
