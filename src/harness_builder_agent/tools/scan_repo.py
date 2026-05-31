from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.evidence_collector import collect_evidence, expand_evidence_with_requested_paths
from harness_builder_agent.tools.llm_evidence_planner import plan_evidence_expansion_with_llm
from harness_builder_agent.tools.llm_config import DeepSeekConfig
from harness_builder_agent.tools.llm_scan_analyzer import analyze_evidence_with_llm
from harness_builder_agent.tools.scan_reconciler import reconcile_scan


def scan_repository(
    repo: Path,
    *,
    llm_caller: Callable[[list[dict[str, str]]], str] | None = None,
    evidence_planner_caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
) -> tuple[ProjectInventory, CommandCatalog]:
    root = repo.resolve()
    evidence = collect_evidence(root)
    if evidence_planner_caller is not None or llm_caller is None:
        plan = plan_evidence_expansion_with_llm(evidence, caller=evidence_planner_caller, config=config)
        evidence = expand_evidence_with_requested_paths(root, evidence, plan.requested_paths)
    proposal = analyze_evidence_with_llm(evidence, caller=llm_caller, config=config)
    inventory, commands, _metadata = reconcile_scan(
        evidence,
        proposal,
        model=config.model if config else None,
        base_url=config.base_url if config else None,
    )
    return inventory, commands
