from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.maturity_report import (
    MaturityBlocker,
    MaturityBlockingCap,
    MaturityDimensionReport,
    MaturityEvidence,
    MaturityLevel,
    MaturityNextStep,
    MaturityReport,
)
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.runtime_task_run import RuntimeTaskRunCollectionSummary
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.tools.runtime_task_runs import summarize_runtime_task_runs

MATURITY_DIMENSIONS = [
    "guides",
    "sensors",
    "workflow",
    "risk_control",
    "repair_loop",
    "observability",
    "experience",
    "verification_sophistication",
    "governance_auditability",
]


def build_maturity_report(
    *,
    ai: Path | None,
    inventory: ProjectInventory,
    commands: CommandCatalog,
    config: HarnessConfig,
    weapon_selection: WeaponLibrarySelection | None = None,
    assessed_at: str | None = None,
) -> MaturityReport:
    workflow_ready = _workflow_ready(ai, config)
    runtime_summary = summarize_runtime_task_runs(ai) if ai is not None else RuntimeTaskRunCollectionSummary()
    runtime_resolved = _runtime_resolved(runtime_summary)
    dimensions = {
        "guides": _guides_dimension(ai, inventory, weapon_selection),
        "sensors": _sensors_dimension(commands),
        "workflow": _workflow_dimension(workflow_ready, config, runtime_summary, runtime_resolved),
        "risk_control": _risk_control_dimension(inventory),
        "repair_loop": _repair_loop_dimension(runtime_summary),
        "observability": _observability_dimension(ai, runtime_summary),
        "experience": _experience_dimension(ai),
        "verification_sophistication": _verification_dimension(commands),
        "governance_auditability": _governance_dimension(ai, runtime_summary),
    }
    dimension_scores = {name: report.level for name, report in dimensions.items()}
    overall_level = _overall_level(commands, workflow_ready, config, runtime_resolved)
    next_steps = _next_steps(dimensions)
    blocking_caps = _blocking_caps(ai, commands, runtime_summary, runtime_resolved)
    return MaturityReport(
        overall_level=overall_level,
        target_next_level=_next_level(overall_level),
        dimension_scores=dimension_scores,
        dimensions=dimensions,
        blocking_caps=blocking_caps,
        next_steps=next_steps,
        evidence=[
            f"主技术栈：{inventory.primary_stack}",
            f"模块数量：{len(inventory.modules)}",
            f"验证命令数量：{len(commands.commands)}",
            f"Workflow Skill 完整：{workflow_ready}",
        ],
        blocking_reasons=[blocker.reason for report in dimensions.values() for blocker in report.blockers][:6],
        recommended_next_steps=[step.action for step in next_steps[:5]],
        last_assessed_at=assessed_at,
    )


def _guides_dimension(
    ai: Path | None, inventory: ProjectInventory, weapon_selection: WeaponLibrarySelection | None
) -> MaturityDimensionReport:
    structured_guides = ai is None or _contains_section(ai / "guides" / "project-context.md", "## 当前项目事实")
    level: MaturityLevel = "L2" if structured_guides else "L1"
    guide_count = len(weapon_selection.guide_weapon_ids) if weapon_selection else 0
    return MaturityDimensionReport(
        level=level,
        evidence=[
            MaturityEvidence(source=".ai/guides/project-context.md", summary="Project context guide records stable project facts."),
            MaturityEvidence(source=".ai/project-inventory.json", summary=f"Primary stack is {inventory.primary_stack}."),
            MaturityEvidence(source=".ai/weapon-library-selection.yaml", summary=f"Selected guide weapons: {guide_count}."),
        ],
        blockers=[
            MaturityBlocker(
                id="guides-not-risk-routed",
                reason="Guides are structured but not yet dynamically loaded by task risk and context.",
                prevents_level="L3",
            )
        ],
        next_level_requirements=["Bind guides to workflow routing and task risk context."],
        confidence="high" if structured_guides else "medium",
    )


def _sensors_dimension(commands: CommandCatalog) -> MaturityDimensionReport:
    has_commands = bool(commands.commands)
    return MaturityDimensionReport(
        level="L2" if has_commands else "L0",
        evidence=[
            MaturityEvidence(source=".ai/command-catalog.yaml", summary=f"Validation command count: {len(commands.commands)}.")
        ],
        blockers=[] if has_commands else [
            MaturityBlocker(
                id="no-executable-sensors",
                reason="No executable validation command is available for Harness sensors.",
                prevents_level="L1",
            )
        ],
        next_level_requirements=[
            "Bind sensor failures into workflow repair behavior.",
            "Classify lint, typecheck, test, build, and security checks by gate strength.",
        ],
        confidence="high",
    )


def _workflow_dimension(
    workflow_ready: bool,
    config: HarnessConfig,
    runtime_summary: RuntimeTaskRunCollectionSummary,
    runtime_resolved: bool,
) -> MaturityDimensionReport:
    routing_rules = config.workflow_routing.rules
    has_standard_escalation = any(
        rule.selected_workflow == "standard" and "high_risk_module" in rule.triggers for rule in routing_rules
    )
    if workflow_ready and has_standard_escalation and runtime_resolved:
        level: MaturityLevel = "L3"
        blockers = [
            MaturityBlocker(
                id="workflow-routing-not-adaptive",
                reason="Runtime evidence is resolved, but routing has not yet been optimized from repeated task outcomes.",
                prevents_level="L4",
            )
        ]
        next_level_requirements = ["Use task outcomes to tune routing and escalation rules."]
    elif workflow_ready and has_standard_escalation:
        level = "L2"
        if runtime_summary.task_run_count > 0:
            blockers = [
                MaturityBlocker(
                    id="runtime-sensors-unresolved",
                    reason="Runtime sensor results are not fully resolved, so workflow-bound L3 is blocked.",
                    prevents_level="L3",
                )
            ]
        else:
            blockers = [
                MaturityBlocker(
                    id="runtime-workflow-not-observed",
                    reason="Workflow routing policy exists, but no Runtime task-run has validated the execution protocol.",
                    prevents_level="L3",
                )
            ]
        next_level_requirements = ["Validate workflow routing with resolved Runtime task-run evidence."]
    else:
        level = "L2" if workflow_ready else "L1"
        blockers = [
            MaturityBlocker(
                id="workflow-not-risk-adaptive",
                reason="Workflow routing is present but not yet adaptive by maturity, task risk, and historical outcomes.",
                prevents_level="L3",
            )
        ]
        next_level_requirements = ["Add risk-based workflow routing and non-skippable hard gate policy."]
    runtime_evidence = [
        MaturityEvidence(source=source, summary="Runtime task-run validates workflow execution evidence.")
        for source in runtime_summary.source_paths
    ]
    return MaturityDimensionReport(
        level=level,
        evidence=[
            MaturityEvidence(source=".ai/harness-config.yaml", summary=f"Configured workflow count: {len(config.workflows)}."),
            MaturityEvidence(source=".ai/skills/", summary=f"Workflow skill files ready: {workflow_ready}."),
            MaturityEvidence(source=".ai/harness-config.yaml", summary=f"Workflow routing rules configured: {len(routing_rules)}."),
        ] + runtime_evidence,
        blockers=blockers,
        next_level_requirements=next_level_requirements,
        confidence="high" if workflow_ready else "medium",
    )


def _risk_control_dimension(inventory: ProjectInventory) -> MaturityDimensionReport:
    risk_count = len(inventory.stack_extensions.get("risk_areas", [])) if inventory.stack_extensions else 0
    return MaturityDimensionReport(
        level="L1" if risk_count else "L0",
        evidence=[MaturityEvidence(source=".ai/project-inventory.json", summary=f"Risk area hints: {risk_count}.")],
        blockers=[
            MaturityBlocker(
                id="risk-zones-not-confirmed",
                reason="Risk zones are not yet confirmed and enforced by workflow routing.",
                prevents_level="L2",
            )
        ],
        next_level_requirements=["Confirm risk zones and connect them to workflow escalation rules."],
        confidence="medium",
    )


def _repair_loop_dimension(runtime_summary: RuntimeTaskRunCollectionSummary) -> MaturityDimensionReport:
    if runtime_summary.task_run_count > 0:
        level: MaturityLevel = "L2" if runtime_summary.repair_attempt_count > 0 else "L1"
        repair_summary = (
            f"Runtime repair attempts observed: {runtime_summary.repair_attempt_count}."
            if runtime_summary.repair_attempt_count > 0
            else "Runtime task-runs exist, but no repair attempt has been observed."
        )
        return MaturityDimensionReport(
            level=level,
            evidence=[
                MaturityEvidence(source=source, summary=repair_summary)
                for source in runtime_summary.source_paths
            ],
            blockers=[
                MaturityBlocker(
                    id="repair-loop-not-history-optimized",
                    reason="Repair loop evidence is available, but repair policy is not yet optimized from repeated outcomes.",
                    prevents_level="L3",
                )
            ],
            next_level_requirements=["Use repeated Runtime repair outcomes to tune workflow repair policy."],
            confidence="medium",
        )
    return MaturityDimensionReport(
        level="L0",
        evidence=[
            MaturityEvidence(
                source="docs/strategy/README.md",
                summary="Task runtime execution is owned by the host AI Coding Runtime, not Harness Builder CLI.",
            )
        ],
        blockers=[
            MaturityBlocker(
                id="runtime-repair-loop-external",
                reason="Repair loop evidence requires host Runtime task execution artifacts.",
                prevents_level="L1",
            )
        ],
        next_level_requirements=["Consume host Runtime sensor reports and repair loop summaries when available."],
        confidence="high",
    )


def _observability_dimension(ai: Path | None, runtime_summary: RuntimeTaskRunCollectionSummary) -> MaturityDimensionReport:
    has_generation_runs = ai is None or _has_generation_runs(ai)
    if runtime_summary.task_run_count > 0:
        return MaturityDimensionReport(
            level="L2",
            evidence=[
                MaturityEvidence(source=".ai/runs/", summary=f"Generation trace exists: {has_generation_runs}."),
                *[
                    MaturityEvidence(source=source, summary="Runtime task-run includes sensor report and handoff evidence.")
                    for source in runtime_summary.source_paths
                ],
            ],
            blockers=[
                MaturityBlocker(
                    id="runtime-trends-not-available",
                    reason="Runtime task evidence exists, but trend and replay analysis are not available yet.",
                    prevents_level="L3",
                )
            ],
            next_level_requirements=["Aggregate Runtime task events into trend and replay evidence."],
            confidence="high",
        )
    return MaturityDimensionReport(
        level="L1" if has_generation_runs else "L0",
        evidence=[MaturityEvidence(source=".ai/runs/", summary=f"Generation trace exists: {has_generation_runs}.")],
        blockers=[
            MaturityBlocker(
                id="runtime-observability-not-present",
                reason="Runtime task events are not available to support trend and replay analysis.",
                prevents_level="L2",
            )
        ],
        next_level_requirements=["Ingest host Runtime task events, sensor reports, and decision logs."],
        confidence="high" if has_generation_runs else "medium",
    )


def _experience_dimension(ai: Path | None) -> MaturityDimensionReport:
    if ai is not None and (ai / "experience" / "experience-index.yaml").exists():
        index = ExperienceIndex.model_validate(yaml.safe_load((ai / "experience" / "experience-index.yaml").read_text(encoding="utf-8")))
        signal_count = (
            index.pending_improvement_count
            + index.asset_candidate_count
            + index.maturity_review_count
            + index.workflow_recommendation_count
            + index.runtime_task_run_count
        )
        evidence = [
            MaturityEvidence(source=".ai/experience/experience-index.yaml", summary=f"Pending improvements: {index.pending_improvement_count}."),
            MaturityEvidence(source=".ai/experience/experience-index.yaml", summary=f"Asset candidates: {index.asset_candidate_count}."),
            MaturityEvidence(source=".ai/experience/experience-index.yaml", summary=f"Maturity reviews: {index.maturity_review_count}."),
            MaturityEvidence(
                source=".ai/experience/experience-index.yaml",
                summary=f"Workflow recommendation reviews: {index.workflow_recommendation_count}.",
            ),
            MaturityEvidence(source=".ai/experience/experience-index.yaml", summary=f"Runtime task runs: {index.runtime_task_run_count}."),
        ]
        return MaturityDimensionReport(
            level="L2" if signal_count else "L1",
            evidence=evidence,
            blockers=[
                MaturityBlocker(
                    id="experience-not-runtime-derived",
                    reason="Experience candidates are not yet derived from real task outcomes and review feedback.",
                    prevents_level="L3",
                )
            ],
            next_level_requirements=["Extract experience candidates from Runtime artifacts and review feedback."],
            confidence="medium",
        )

    has_pending = ai is None or (ai / "experience" / "pending-improvements.md").exists()
    return MaturityDimensionReport(
        level="L1" if has_pending else "L0",
        evidence=[
            MaturityEvidence(source=".ai/experience/pending-improvements.md", summary=f"Pending improvements file exists: {has_pending}.")
        ],
        blockers=[
            MaturityBlocker(
                id="experience-not-runtime-derived",
                reason="Experience candidates are not yet derived from real task outcomes and review feedback.",
                prevents_level="L2",
            )
        ],
        next_level_requirements=["Extract experience candidates from Runtime artifacts and review feedback."],
        confidence="medium",
    )


def _verification_dimension(commands: CommandCatalog) -> MaturityDimensionReport:
    has_commands = bool(commands.commands)
    return MaturityDimensionReport(
        level="L1" if has_commands else "L0",
        evidence=[MaturityEvidence(source=".ai/command-catalog.yaml", summary=f"Command count: {len(commands.commands)}.")],
        blockers=[
            MaturityBlocker(
                id="verification-not-mapped-to-task-risk",
                reason="Verification commands are not yet mapped to task type, risk level, or invariants.",
                prevents_level="L2",
            )
        ],
        next_level_requirements=["Map validation commands to task type, gate strength, and risk context."],
        confidence="high" if has_commands else "medium",
    )


def _governance_dimension(ai: Path | None, runtime_summary: RuntimeTaskRunCollectionSummary) -> MaturityDimensionReport:
    has_generation_runs = ai is None or _has_generation_runs(ai)
    if runtime_summary.task_run_count > 0:
        return MaturityDimensionReport(
            level="L2",
            evidence=[
                MaturityEvidence(source=source, summary="Runtime task-run includes decision log and handoff summary.")
                for source in runtime_summary.source_paths
            ],
            blockers=[
                MaturityBlocker(
                    id="workflow-event-store-missing",
                    reason="Decision logs and handoff summaries exist, but task-level event store and replay are not available.",
                    prevents_level="L3",
                )
            ],
            next_level_requirements=["Aggregate Runtime decision logs into workflow event history."],
            confidence="high",
        )
    return MaturityDimensionReport(
        level="L1" if has_generation_runs else "L0",
        evidence=[MaturityEvidence(source=".ai/runs/", summary=f"Generation audit trail exists: {has_generation_runs}.")],
        blockers=[
            MaturityBlocker(
                id="runtime-audit-not-ingested",
                reason="Runtime decision logs and handoff summaries are not yet ingested.",
                prevents_level="L2",
            )
        ],
        next_level_requirements=["Ingest Runtime decision logs and expose governance audit checks."],
        confidence="high" if has_generation_runs else "medium",
    )


def _blocking_caps(
    ai: Path | None,
    commands: CommandCatalog,
    runtime_summary: RuntimeTaskRunCollectionSummary,
    runtime_resolved: bool,
) -> list[MaturityBlockingCap]:
    caps = [
        MaturityBlockingCap(
            id="runtime-audit-not-owned-by-builder",
            reason="L4 governance requires repeated host Runtime audit artifacts; Harness Builder CLI does not generate task-runs.",
            max_level="L3",
            active=runtime_summary.task_run_count == 0,
            evidence=[".ai/task-runs is an external Runtime contract"],
        )
    ]
    if runtime_summary.task_run_count > 0 and not runtime_resolved:
        caps.append(
            MaturityBlockingCap(
                id="runtime-sensors-unresolved",
                reason="Runtime task-runs exist, but failed/skipped/unresolved sensors block Workflow-bound L3.",
                max_level="L2",
                active=True,
                evidence=runtime_summary.source_paths,
            )
        )
    if not commands.commands:
        caps.append(
            MaturityBlockingCap(
                id="no-executable-sensors",
                reason="No executable validation commands are available.",
                max_level="L0",
                active=True,
                evidence=[".ai/command-catalog.yaml commands is empty"],
            )
        )
    if ai is not None and not _has_generation_runs(ai):
        caps.append(
            MaturityBlockingCap(
                id="no-generation-trace",
                reason="No Harness Builder generation trace was found.",
                max_level="L0",
                active=True,
                evidence=[".ai/runs missing or empty"],
            )
        )
    return caps


def _next_steps(dimensions: dict[str, MaturityDimensionReport]) -> list[MaturityNextStep]:
    steps: list[MaturityNextStep] = []
    for name, report in dimensions.items():
        if not report.next_level_requirements:
            continue
        priority = "high" if name in {"sensors", "workflow", "risk_control"} else "medium"
        if report.level == "L0":
            priority = "critical"
        steps.append(
            MaturityNextStep(
                id=f"{name}-next-level",
                target_dimension=name,
                action=report.next_level_requirements[0],
                priority=priority,
                expected_lift=f"{name} {report.level} -> next",
            )
        )
    return steps


def _overall_level(
    commands: CommandCatalog,
    workflow_ready: bool,
    config: HarnessConfig,
    runtime_resolved: bool,
) -> MaturityLevel:
    if not commands.commands:
        return "L0"
    has_standard_escalation = any(
        rule.selected_workflow == "standard" and "high_risk_module" in rule.triggers
        for rule in config.workflow_routing.rules
    )
    if workflow_ready and config.workflows and has_standard_escalation and runtime_resolved:
        return "L3"
    if workflow_ready and config.workflows:
        return "L2"
    return "L1"


def _next_level(level: MaturityLevel) -> MaturityLevel | None:
    levels: list[MaturityLevel] = ["L0", "L1", "L2", "L3", "L4"]
    index = levels.index(level)
    if index == len(levels) - 1:
        return None
    return levels[index + 1]


def _workflow_ready(ai: Path | None, config: HarnessConfig) -> bool:
    if not config.workflows:
        return False
    if ai is None:
        return True
    return all((ai.parent / workflow.skill_path).exists() for workflow in config.workflows.values())


def _contains_section(path: Path, section: str) -> bool:
    return path.exists() and section in path.read_text(encoding="utf-8")


def _has_generation_runs(ai: Path) -> bool:
    runs = ai / "runs"
    return runs.exists() and any(path.is_dir() for path in runs.iterdir())


def _runtime_resolved(runtime_summary: RuntimeTaskRunCollectionSummary) -> bool:
    return (
        runtime_summary.task_run_count > 0
        and runtime_summary.failed_sensor_count == 0
        and runtime_summary.skipped_sensor_count == 0
        and runtime_summary.unresolved_sensor_count == 0
    )
