from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.maturity_evidence import (
    BenchmarkEvidence,
    CommandEvidenceSummary,
    ExperienceEvidence,
    HarnessAssetEvidence,
    InventoryEvidenceSummary,
    MaturityEvidencePack,
    ObservabilityEvidence,
)
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.tools.experience_summary import load_experience_summary

MATURITY_INPUTS = [
    ".ai/project-inventory.json",
    ".ai/command-catalog.yaml",
    ".ai/harness-config.yaml",
    ".ai/scan-metadata.yaml",
    ".ai/llm-scan-proposal.json",
    ".ai/weapon-library-selection.yaml",
    ".ai/guides/",
    ".ai/sensors/",
    ".ai/skills/",
    ".ai/runs/",
    ".ai/experience/experience-index.yaml",
    ".ai/experience/experience-summary.yaml",
    ".ai/experience/pending-improvements.md",
    ".ai/benchmark-report.yaml",
]


def build_maturity_evidence_pack(
    *,
    ai: Path,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    config: HarnessConfig,
    weapon_selection: WeaponLibrarySelection | None = None,
) -> MaturityEvidencePack:
    return MaturityEvidencePack(
        repo_name=inventory.repo_name,
        primary_stack=inventory.primary_stack,
        inventory_summary=_inventory_summary(inventory),
        command_summary=_command_summary(commands),
        harness_assets=_harness_assets(ai, config, weapon_selection),
        observability=_observability(ai),
        experience=_experience(ai),
        benchmark=_benchmark(ai),
        maturity_inputs=list(MATURITY_INPUTS),
        warnings=_warnings(ai),
    )


def collect_maturity_evidence(ai: Path) -> MaturityEvidencePack:
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))
    commands = CommandCatalog.model_validate(yaml.safe_load((ai / "command-catalog.yaml").read_text(encoding="utf-8")))
    config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
    weapon_selection_path = ai / "weapon-library-selection.yaml"
    weapon_selection = (
        WeaponLibrarySelection.model_validate(yaml.safe_load(weapon_selection_path.read_text(encoding="utf-8")))
        if weapon_selection_path.exists()
        else None
    )
    return build_maturity_evidence_pack(
        ai=ai,
        inventory=inventory,
        commands=commands,
        config=config,
        weapon_selection=weapon_selection,
    )


def _inventory_summary(inventory: ProjectInventory) -> InventoryEvidenceSummary:
    risk_areas = inventory.stack_extensions.get("risk_areas", [])
    return InventoryEvidenceSummary(
        module_count=len(inventory.modules),
        evidence_count=len(inventory.evidence),
        risk_area_count=len(risk_areas) if isinstance(risk_areas, list) else 0,
    )


def _command_summary(commands: CommandCatalog) -> CommandEvidenceSummary:
    return CommandEvidenceSummary(
        total_count=len(commands.commands),
        hard_gate_count=sum(1 for command in commands.commands if command.gate == "hard"),
        soft_gate_count=sum(1 for command in commands.commands if command.gate == "soft"),
        command_ids=[command.id for command in commands.commands],
    )


def _harness_assets(ai: Path, config: HarnessConfig, weapon_selection: WeaponLibrarySelection | None) -> HarnessAssetEvidence:
    guides = ai / "guides"
    sensors = ai / "sensors"
    skills = ai / "skills"
    guide_count = _count_files(guides, "*.md")
    sensor_count = _count_files(sensors, "*.md")
    workflow_skill_count = _count_files(skills, "SKILL.md")
    if guide_count == 0 and weapon_selection:
        guide_count = len(weapon_selection.guide_weapon_ids)
    if sensor_count == 0 and weapon_selection:
        sensor_count = len(weapon_selection.sensor_weapon_ids)
    if workflow_skill_count == 0:
        workflow_skill_count = len(config.workflows)
    routing_rules = config.workflow_routing.rules
    has_standard_escalation_rule = any(
        rule.selected_workflow == "standard" and "high_risk_module" in rule.triggers for rule in routing_rules
    )
    return HarnessAssetEvidence(
        guide_count=guide_count,
        sensor_count=sensor_count,
        workflow_skill_count=workflow_skill_count,
        workflow_routing_rule_count=len(routing_rules),
        has_standard_escalation_rule=has_standard_escalation_rule,
        has_harness_config=(ai / "harness-config.yaml").exists() or bool(config.workflows),
        has_weapon_library_selection=(ai / "weapon-library-selection.yaml").exists() or weapon_selection is not None,
    )


def _observability(ai: Path) -> ObservabilityEvidence:
    runs = ai / "runs"
    run_dirs = sorted(path for path in runs.iterdir() if path.is_dir()) if runs.exists() else []
    latest_status = None
    if run_dirs:
        trace_path = run_dirs[-1] / "trace.yaml"
        if trace_path.exists():
            trace = yaml.safe_load(trace_path.read_text(encoding="utf-8")) or {}
            latest_status = trace.get("status")
    task_runs = ai / "task-runs"
    runtime_dirs = [path for path in task_runs.iterdir() if path.is_dir()] if task_runs.exists() else []
    return ObservabilityEvidence(
        generation_run_count=len(run_dirs),
        has_runtime_task_runs=bool(runtime_dirs),
        latest_generation_status=latest_status,
    )


def _experience(ai: Path) -> ExperienceEvidence:
    summary = load_experience_summary(ai)
    index_path = ai / "experience" / "experience-index.yaml"
    if index_path.exists():
        index = ExperienceIndex.model_validate(yaml.safe_load(index_path.read_text(encoding="utf-8")))
        experience_file_count = sum(1 for exists in index.experience_files.values() if exists)
        return ExperienceEvidence(
            has_pending_improvements=index.pending_improvement_count > 0,
            pending_improvement_count=index.pending_improvement_count,
            has_experience_index=True,
            asset_candidate_count=index.asset_candidate_count,
            maturity_review_count=index.maturity_review_count,
            runtime_task_run_count=index.runtime_task_run_count,
            experience_file_count=experience_file_count,
            has_experience_summary=summary is not None,
            experience_summary_finding_count=len(summary.findings) if summary else 0,
        )

    pending = ai / "experience" / "pending-improvements.md"
    if not pending.exists():
        return ExperienceEvidence(
            has_experience_summary=summary is not None,
            experience_summary_finding_count=len(summary.findings) if summary else 0,
        )
    text = pending.read_text(encoding="utf-8")
    count = sum(1 for line in text.splitlines() if line.lstrip().startswith("- "))
    return ExperienceEvidence(
        has_pending_improvements=count > 0,
        pending_improvement_count=count,
        has_experience_summary=summary is not None,
        experience_summary_finding_count=len(summary.findings) if summary else 0,
    )


def _benchmark(ai: Path) -> BenchmarkEvidence:
    report = ai / "benchmark-report.yaml"
    if not report.exists():
        return BenchmarkEvidence(has_report=False, status="missing")
    payload = yaml.safe_load(report.read_text(encoding="utf-8")) or {}
    status = payload.get("status")
    if status not in {"passed", "failed"}:
        status = "unknown"
    return BenchmarkEvidence(has_report=True, status=status)


def _warnings(ai: Path) -> list[str]:
    warnings: list[str] = []
    task_runs = ai / "task-runs"
    has_task_runs = task_runs.exists() and any(path.is_dir() for path in task_runs.iterdir())
    if not has_task_runs:
        warnings.append("runtime task-runs absent; host AI Coding Runtime has not supplied task execution evidence")
    if not (ai / "benchmark-report.yaml").exists():
        warnings.append("benchmark report absent; maturity evidence does not include benchmark status yet")
    return warnings


def _count_files(root: Path, pattern: str) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob(pattern) if path.is_file())
