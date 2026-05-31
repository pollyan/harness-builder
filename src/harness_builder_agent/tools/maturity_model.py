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
            MaturityEvidence(source=".ai/guides/project-context.md", summary="项目上下文 Guide 记录稳定项目事实。"),
            MaturityEvidence(source=".ai/project-inventory.json", summary=f"主技术栈：{inventory.primary_stack}。"),
            MaturityEvidence(source=".ai/weapon-library-selection.yaml", summary=f"已选择 Guide 武器数量：{guide_count}。"),
        ],
        blockers=[
            MaturityBlocker(
                id="guides-not-risk-routed",
                reason="Guides 已结构化，但还没有按任务风险和上下文动态加载。",
                prevents_level="L3",
            )
        ],
        next_level_requirements=["绑定 Guides 到 Workflow routing 和任务风险上下文。"],
        confidence="high" if structured_guides else "medium",
    )


def _sensors_dimension(commands: CommandCatalog) -> MaturityDimensionReport:
    has_commands = bool(commands.commands)
    return MaturityDimensionReport(
        level="L2" if has_commands else "L0",
        evidence=[
            MaturityEvidence(source=".ai/command-catalog.yaml", summary=f"验证命令数量：{len(commands.commands)}。")
        ],
        blockers=[] if has_commands else [
            MaturityBlocker(
                id="no-executable-sensors",
                reason="当前没有可供 Harness Sensors 使用的可执行验证命令。",
                prevents_level="L1",
            )
        ],
        next_level_requirements=[
            "把 Sensor 失败接入 Workflow repair 行为。",
            "按 gate 强度区分 lint、typecheck、test、build 和 security 检查。",
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
                reason="Runtime 证据已 resolved，但 routing 还没有基于多次任务结果优化。",
                prevents_level="L4",
            )
        ]
        next_level_requirements = ["使用任务结果持续调优 routing 和升级规则。"]
    elif workflow_ready and has_standard_escalation:
        level = "L2"
        if runtime_summary.task_run_count > 0:
            blockers = [
                MaturityBlocker(
                    id="runtime-sensors-unresolved",
                    reason="Runtime Sensor 结果尚未全部 resolved，因此 Workflow-bound L3 仍被阻断。",
                    prevents_level="L3",
                )
            ]
        else:
            blockers = [
                MaturityBlocker(
                    id="runtime-workflow-not-observed",
                    reason="Workflow routing policy 已存在，但还没有 Runtime task-run 验证执行协议。",
                    prevents_level="L3",
                )
            ]
        next_level_requirements = ["用全部 resolved 的 Runtime task-run 证据验证 Workflow routing。"]
    else:
        level = "L2" if workflow_ready else "L1"
        blockers = [
            MaturityBlocker(
                id="workflow-not-risk-adaptive",
                reason="Workflow routing 已存在，但还没有按成熟度、任务风险和历史结果自适应调整。",
                prevents_level="L3",
            )
        ]
        next_level_requirements = ["增加基于风险的 Workflow routing 和不可随意跳过的 hard gate 策略。"]
    runtime_evidence = [
        MaturityEvidence(source=source, summary="Runtime task-run 提供 Workflow 执行验证证据。")
        for source in runtime_summary.source_paths
    ]
    return MaturityDimensionReport(
        level=level,
        evidence=[
            MaturityEvidence(source=".ai/harness-config.yaml", summary=f"已配置 Workflow 数量：{len(config.workflows)}。"),
            MaturityEvidence(source=".ai/skills/", summary=f"Workflow Skill 文件就绪：{workflow_ready}。"),
            MaturityEvidence(source=".ai/harness-config.yaml", summary=f"Workflow routing 规则数量：{len(routing_rules)}。"),
        ] + runtime_evidence,
        blockers=blockers,
        next_level_requirements=next_level_requirements,
        confidence="high" if workflow_ready else "medium",
    )


def _risk_control_dimension(inventory: ProjectInventory) -> MaturityDimensionReport:
    risk_count = len(inventory.stack_extensions.get("risk_areas", [])) if inventory.stack_extensions else 0
    return MaturityDimensionReport(
        level="L1" if risk_count else "L0",
        evidence=[MaturityEvidence(source=".ai/project-inventory.json", summary=f"风险区域线索数量：{risk_count}。")],
        blockers=[
            MaturityBlocker(
                id="risk-zones-not-confirmed",
                reason="风险区域尚未确认，也还没有被 Workflow routing 强制执行。",
                prevents_level="L2",
            )
        ],
        next_level_requirements=["确认风险区域，并连接到 Workflow 升级规则。"],
        confidence="medium",
    )


def _repair_loop_dimension(runtime_summary: RuntimeTaskRunCollectionSummary) -> MaturityDimensionReport:
    if runtime_summary.task_run_count > 0:
        level: MaturityLevel = "L2" if runtime_summary.repair_attempt_count > 0 else "L1"
        repair_summary = (
            f"已观察到 Runtime repair 尝试次数：{runtime_summary.repair_attempt_count}。"
            if runtime_summary.repair_attempt_count > 0
            else "已存在 Runtime task-runs，但尚未观察到 repair 尝试。"
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
                    reason="Repair loop 证据已存在，但 repair 策略还没有基于重复结果优化。",
                    prevents_level="L3",
                )
            ],
            next_level_requirements=["使用重复出现的 Runtime repair 结果调优 Workflow repair 策略。"],
            confidence="medium",
        )
    return MaturityDimensionReport(
        level="L0",
        evidence=[
            MaturityEvidence(
                source=".ai/task-runs/",
                summary="任务级 Runtime 执行由宿主 AI Coding Runtime 负责，不由 Harness Builder CLI 执行。",
            )
        ],
        blockers=[
            MaturityBlocker(
                id="runtime-repair-loop-external",
                reason="Repair loop 证据需要宿主 Runtime 任务执行产物。",
                prevents_level="L1",
            )
        ],
        next_level_requirements=["在可用时消费宿主 Runtime sensor reports 和 repair loop summaries。"],
        confidence="high",
    )


def _observability_dimension(ai: Path | None, runtime_summary: RuntimeTaskRunCollectionSummary) -> MaturityDimensionReport:
    has_generation_runs = ai is None or _has_generation_runs(ai)
    if runtime_summary.task_run_count > 0:
        return MaturityDimensionReport(
            level="L2",
            evidence=[
                MaturityEvidence(source=".ai/runs/", summary=f"Generation trace 是否存在：{has_generation_runs}。"),
                *[
                    MaturityEvidence(source=source, summary="Runtime task-run 包含 sensor report 和 handoff 证据。")
                    for source in runtime_summary.source_paths
                ],
            ],
            blockers=[
                MaturityBlocker(
                    id="runtime-trends-not-available",
                    reason="Runtime task 证据已存在，但趋势分析和 replay 分析尚不可用。",
                    prevents_level="L3",
                )
            ],
            next_level_requirements=["把 Runtime task events 汇总为趋势和 replay 证据。"],
            confidence="high",
        )
    return MaturityDimensionReport(
        level="L1" if has_generation_runs else "L0",
        evidence=[MaturityEvidence(source=".ai/runs/", summary=f"Generation trace 是否存在：{has_generation_runs}。")],
        blockers=[
            MaturityBlocker(
                id="runtime-observability-not-present",
                reason="Runtime task events 尚不可用，无法支撑趋势和 replay 分析。",
                prevents_level="L2",
            )
        ],
        next_level_requirements=["摄取宿主 Runtime task events、sensor reports 和 decision logs。"],
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
            MaturityEvidence(source=".ai/experience/experience-index.yaml", summary=f"Pending improvements 数量：{index.pending_improvement_count}。"),
            MaturityEvidence(source=".ai/experience/experience-index.yaml", summary=f"Asset candidates 数量：{index.asset_candidate_count}。"),
            MaturityEvidence(source=".ai/experience/experience-index.yaml", summary=f"Maturity reviews 数量：{index.maturity_review_count}。"),
            MaturityEvidence(
                source=".ai/experience/experience-index.yaml",
                summary=f"Workflow recommendation reviews 数量：{index.workflow_recommendation_count}。",
            ),
            MaturityEvidence(source=".ai/experience/experience-index.yaml", summary=f"Runtime task runs 数量：{index.runtime_task_run_count}。"),
        ]
        return MaturityDimensionReport(
            level="L2" if signal_count else "L1",
            evidence=evidence,
            blockers=[
                MaturityBlocker(
                    id="experience-not-runtime-derived",
                    reason="Experience candidates 尚未来自真实任务结果和 Review 反馈。",
                    prevents_level="L3",
                )
            ],
            next_level_requirements=["从 Runtime artifacts 和 Review 反馈中提取 Experience candidates。"],
            confidence="medium",
        )

    has_pending = ai is None or (ai / "experience" / "pending-improvements.md").exists()
    return MaturityDimensionReport(
        level="L1" if has_pending else "L0",
        evidence=[
            MaturityEvidence(source=".ai/experience/pending-improvements.md", summary=f"Pending improvements 文件是否存在：{has_pending}。")
        ],
        blockers=[
            MaturityBlocker(
                id="experience-not-runtime-derived",
                reason="Experience candidates 尚未来自真实任务结果和 Review 反馈。",
                prevents_level="L2",
            )
        ],
        next_level_requirements=["从 Runtime artifacts 和 Review 反馈中提取 Experience candidates。"],
        confidence="medium",
    )


def _verification_dimension(commands: CommandCatalog) -> MaturityDimensionReport:
    has_commands = bool(commands.commands)
    return MaturityDimensionReport(
        level="L1" if has_commands else "L0",
        evidence=[MaturityEvidence(source=".ai/command-catalog.yaml", summary=f"命令数量：{len(commands.commands)}。")],
        blockers=[
            MaturityBlocker(
                id="verification-not-mapped-to-task-risk",
                reason="验证命令尚未映射到任务类型、风险等级或不变量。",
                prevents_level="L2",
            )
        ],
        next_level_requirements=["把验证命令映射到任务类型、gate 强度和风险上下文。"],
        confidence="high" if has_commands else "medium",
    )


def _governance_dimension(ai: Path | None, runtime_summary: RuntimeTaskRunCollectionSummary) -> MaturityDimensionReport:
    has_generation_runs = ai is None or _has_generation_runs(ai)
    if runtime_summary.task_run_count > 0:
        return MaturityDimensionReport(
            level="L2",
            evidence=[
                MaturityEvidence(source=source, summary="Runtime task-run 包含 decision log 和 handoff summary。")
                for source in runtime_summary.source_paths
            ],
            blockers=[
                MaturityBlocker(
                    id="workflow-event-store-missing",
                    reason="Decision logs 和 handoff summaries 已存在，但任务级 event store 和 replay 尚不可用。",
                    prevents_level="L3",
                )
            ],
            next_level_requirements=["把 Runtime decision logs 汇总为 Workflow event history。"],
            confidence="high",
        )
    return MaturityDimensionReport(
        level="L1" if has_generation_runs else "L0",
        evidence=[MaturityEvidence(source=".ai/runs/", summary=f"Generation audit trail 是否存在：{has_generation_runs}。")],
        blockers=[
            MaturityBlocker(
                id="runtime-audit-not-ingested",
                reason="Runtime decision logs 和 handoff summaries 尚未摄取。",
                prevents_level="L2",
            )
        ],
        next_level_requirements=["摄取 Runtime decision logs，并暴露 governance audit checks。"],
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
            reason="L4 governance 需要重复的宿主 Runtime 审计产物；Harness Builder CLI 不生成 task-runs。",
            max_level="L3",
            active=runtime_summary.task_run_count == 0,
            evidence=[".ai/task-runs 是外部 Runtime 契约"],
        )
    ]
    if runtime_summary.task_run_count > 0 and not runtime_resolved:
        caps.append(
            MaturityBlockingCap(
                id="runtime-sensors-unresolved",
                reason="Runtime task-runs 已存在，但 failed / skipped / unresolved Sensors 会阻断 Workflow-bound L3。",
                max_level="L2",
                active=True,
                evidence=runtime_summary.source_paths,
            )
        )
    if not commands.commands:
        caps.append(
            MaturityBlockingCap(
                id="no-executable-sensors",
                reason="当前没有可执行验证命令。",
                max_level="L0",
                active=True,
                evidence=[".ai/command-catalog.yaml 中 commands 为空"],
            )
        )
    if ai is not None and not _has_generation_runs(ai):
        caps.append(
            MaturityBlockingCap(
                id="no-generation-trace",
                reason="未发现 Harness Builder generation trace。",
                max_level="L0",
                active=True,
                evidence=[".ai/runs 缺失或为空"],
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
                expected_lift=f"{name} {report.level} -> 下一等级",
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
