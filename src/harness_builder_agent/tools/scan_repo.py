from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from harness_builder_agent.prompts.registry import (
    LLM_EVIDENCE_PLAN_V1,
    LLM_FIRST_SCAN_V2,
    build_machine_prompt_messages,
)
from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.evidence_collector import collect_evidence, expand_evidence_with_requested_paths
from harness_builder_agent.tools.llm_evidence_planner import plan_evidence_expansion_with_llm
from harness_builder_agent.tools.llm_config import DeepSeekConfig
from harness_builder_agent.tools.llm_scan_analyzer import analyze_evidence_with_llm
from harness_builder_agent.tools.llm_scan_self_checker import review_scan_followups_with_llm
from harness_builder_agent.tools.scan_reconciler import reconcile_scan
from harness_builder_agent.schemas.scan import LLMEvidencePlan


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
    scan_self_check_caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
    progress: ScanProgressCallback | None = None,
) -> tuple[ProjectInventory, CommandCatalog]:
    root = repo.resolve()
    _emit_progress(progress, "collect-evidence", "started", "Collecting repository evidence.")
    evidence = collect_evidence(root)
    evidence_plan_input_chars = _evidence_plan_input_chars(evidence)
    _emit_progress(
        progress,
        "collect-evidence",
        "completed",
        "Repository evidence collected.",
        {
            "evidence_file_count": evidence.detected_file_count,
            "selected_evidence_count": evidence.coverage.selected_evidence_count if evidence.coverage else 0,
            "llm_input_chars": evidence_plan_input_chars,
        },
    )
    evidence_plan: LLMEvidencePlan | None = None
    if evidence_planner_caller is not None or llm_caller is None:
        _emit_progress(
            progress,
            "plan-evidence-expansion",
            "started",
            "Planning evidence expansion with LLM.",
            _llm_progress_details("evidence planner", evidence_plan_input_chars, config),
        )
        evidence_plan = plan_evidence_expansion_with_llm(evidence, caller=evidence_planner_caller, config=config)
        _emit_progress(
            progress,
            "plan-evidence-expansion",
            "completed",
            "Evidence expansion plan completed.",
            {"requested_path_count": len(evidence_plan.requested_paths)},
        )
        _emit_progress(progress, "expand-evidence", "started", "Reading LLM requested evidence files.")
        evidence = expand_evidence_with_requested_paths(root, evidence, evidence_plan.requested_paths)
        _emit_progress(
            progress,
            "expand-evidence",
            "completed",
            "LLM requested evidence files read.",
            {"requested_path_count": len(evidence_plan.requested_paths), "llm_requested_file_count": len(evidence.llm_requested_files)},
        )
    scan_input_chars = _scan_input_chars(evidence)
    _emit_progress(
        progress,
        "llm-scan",
        "started",
        "Requesting structured LLM scan.",
        _llm_progress_details("scan analyzer", scan_input_chars, config),
    )
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
        evidence_plan=evidence_plan,
    )
    metadata = _metadata
    _emit_progress(
        progress,
        "reconcile-scan",
        "completed",
        "Scan reconciliation completed.",
        {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)},
    )
    if metadata.followup_questions and (scan_self_check_caller is not None or llm_caller is None):
        _emit_progress(progress, "scan-self-check", "started", "Requesting LLM scan follow-up self-check.")
        self_check = review_scan_followups_with_llm(
            evidence,
            metadata,
            caller=scan_self_check_caller,
            config=config,
        )
        metadata = metadata.model_copy(update={"self_check": self_check})
        extensions = dict(inventory.stack_extensions)
        extensions["scan_metadata"] = metadata.model_dump(mode="json")
        inventory = inventory.model_copy(update={"stack_extensions": extensions})
        _emit_progress(
            progress,
            "scan-self-check",
            "completed",
            "LLM scan follow-up self-check completed.",
            {"resolution_count": len(self_check.resolutions), "overall_risk": self_check.overall_risk},
        )
    return inventory, commands


def _llm_progress_details(llm_phase: str, input_chars: int, config: DeepSeekConfig | None) -> dict[str, object]:
    return {
        "llm_phase": llm_phase,
        "llm_input_chars": input_chars,
        "model": config.model if config else "unknown",
        "timeout_seconds": config.timeout_seconds if config else None,
    }


def _evidence_plan_input_chars(evidence) -> int:
    return _message_content_chars(
        build_machine_prompt_messages(LLM_EVIDENCE_PLAN_V1.key, evidence.model_dump(mode="json", exclude_none=True))
    )


def _scan_input_chars(evidence) -> int:
    return _message_content_chars(
        build_machine_prompt_messages(LLM_FIRST_SCAN_V2.key, evidence.model_dump(mode="json", exclude_none=True))
    )


def _message_content_chars(messages: list[dict[str, str]]) -> int:
    return sum(len(message["content"]) for message in messages)


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
