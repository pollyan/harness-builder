from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.maturity_report import MaturityReport


@dataclass(frozen=True)
class MaintenanceAction:
    priority: int
    action: str
    reason: str
    source: str
    next_action: str
    count: int | None = None
    detail: str | None = None


def build_maintenance_triage(ai: Path, score: MaturityReport | None = None) -> list[MaintenanceAction]:
    actions: list[MaintenanceAction] = []
    if score is None:
        actions.append(
            MaintenanceAction(
                priority=5,
                action="assess",
                reason="maturity_score_missing",
                source=".ai/maturity-score.yaml",
                next_action="assess",
            )
        )

    benchmark = _read_benchmark(ai)
    if benchmark is None:
        actions.append(
            MaintenanceAction(
                priority=10,
                action="benchmark",
                reason="benchmark_not_run",
                source=".ai/benchmark-report.yaml",
                next_action="benchmark",
            )
        )
    else:
        risk_context_failed = _risk_context_failed_count(benchmark)
        hard_gate_detail = _hard_gate_weak_command_detail(benchmark)
        project_context_evidence_failed = _project_context_evidence_failed_count(benchmark)
        project_context_evidence_detail = _project_context_evidence_missing_detail(benchmark)
        schema_content_failed = _schema_content_failed_count(benchmark)
        if risk_context_failed:
            actions.append(
                MaintenanceAction(
                    priority=14,
                    action="benchmark",
                    reason="risk_context_inconsistent",
                    source=".ai/benchmark-report.yaml",
                    next_action="benchmark",
                    count=risk_context_failed,
                )
            )
        elif hard_gate_detail is not None:
            command_id, detail = hard_gate_detail
            actions.append(
                MaintenanceAction(
                    priority=15,
                    action="benchmark",
                    reason="hard_gate_command_evidence",
                    source=f".ai/benchmark-report.yaml#content:hard-gate-command-evidence:{command_id}",
                    next_action="benchmark",
                    count=1,
                    detail=detail,
                )
            )
        elif project_context_evidence_failed:
            actions.append(
                MaintenanceAction(
                    priority=15,
                    action="benchmark",
                    reason="project_context_evidence_incomplete",
                    source=".ai/benchmark-report.yaml#content:project-context-evidence-context",
                    next_action="benchmark",
                    count=project_context_evidence_failed,
                    detail=project_context_evidence_detail,
                )
            )
        elif schema_content_failed:
            actions.append(
                MaintenanceAction(
                    priority=16,
                    action="benchmark",
                    reason="schema_content_failed_checks",
                    source=".ai/benchmark-report.yaml",
                    next_action="benchmark",
                    count=schema_content_failed,
                )
            )
        elif benchmark.status == "failed":
            actions.append(
                MaintenanceAction(
                    priority=16,
                    action="benchmark",
                    reason="benchmark_failed_checks",
                    source=".ai/benchmark-report.yaml",
                    next_action="benchmark",
                    count=sum(1 for check in benchmark.checks if not check.passed),
                )
            )

    index = _read_experience_index(ai)
    if index is None:
        actions.append(
            MaintenanceAction(
                priority=18,
                action="improve",
                reason="experience_index_missing",
                source=".ai/experience/experience-index.yaml",
                next_action="improve",
            )
        )
    else:
        pending_asset_candidates = max(index.asset_candidate_count - index.candidate_governance_decision_count, 0)
        if pending_asset_candidates:
            actions.append(
                MaintenanceAction(
                    priority=20,
                    action="review-candidate",
                    reason="asset_candidates_pending",
                    source=".ai/review/asset-candidates.yaml",
                    next_action="review-candidate",
                    count=pending_asset_candidates,
                )
            )
        if index.workflow_recommendation_count:
            actions.append(
                MaintenanceAction(
                    priority=30,
                    action="improve",
                    reason="workflow_recommendations_pending",
                    source=_workflow_recommendation_source(index),
                    next_action="improve",
                    count=index.workflow_recommendation_count,
                )
            )
        if index.pending_improvement_count and not pending_asset_candidates:
            actions.append(
                MaintenanceAction(
                    priority=40,
                    action="self-improve",
                    reason="pending_improvements_need_review_package",
                    source=".ai/experience/pending-improvements.md",
                    next_action="self-improve",
                    count=index.pending_improvement_count,
                )
            )

    if not actions:
        actions.append(
            MaintenanceAction(
                priority=90,
                action="recommend-workflow",
                reason="no_pending_maintenance_signal",
                source=".ai/harness-config.yaml",
                next_action="recommend-workflow",
            )
        )
    return sorted(actions, key=lambda item: (item.priority, item.action))[:3]


def render_maintenance_triage_lines(actions: list[MaintenanceAction]) -> list[str]:
    lines: list[str] = []
    for index, action in enumerate(actions[:3], start=1):
        count = f" count={action.count}" if action.count is not None else ""
        detail = f" detail={action.detail}" if action.detail else ""
        lines.append(
            f"top_action_{index}={action.action} "
            f"reason={action.reason} "
            f"source={action.source} "
            f"next={action.next_action}"
            f"{count}"
            f"{detail}"
        )
    return lines


def render_maintenance_triage_guidance_lines(actions: list[MaintenanceAction]) -> list[str]:
    return [_maintenance_action_guidance(index, action) for index, action in enumerate(actions[:3], start=1)]


def _maintenance_action_guidance(index: int, action: MaintenanceAction) -> str:
    prefix = f"建议处理 {index}："
    if action.reason == "maturity_score_missing":
        return f"{prefix}先运行 `assess` 刷新成熟度评分和入口摘要，再决定后续维护动作。"
    if action.reason == "benchmark_not_run":
        return f"{prefix}先运行 `benchmark` 生成质量门禁报告，再回到 guided `init` 查看 Benchmark signals。"
    if action.reason == "risk_context_inconsistent":
        return f"{prefix}同步检查 Guide / Sensor / Routing 中的风险路径表达，然后运行 `benchmark` 复验。"
    if action.reason == "hard_gate_command_evidence":
        detail = f"；问题详情 `{action.detail}`" if action.detail else ""
        return f"{prefix}先修正 hard gate 命令的 source、confidence 或 gate 证据，再运行 `benchmark`{detail}。"
    if action.reason == "project_context_evidence_incomplete":
        detail = f"；缺失详情 `{action.detail}`" if action.detail else ""
        return f"{prefix}补齐 project-context evidence 后运行 `benchmark`{detail}。"
    if action.reason == "schema_content_failed_checks":
        count = f"{action.count} 个 " if action.count else ""
        return f"{prefix}查看 `.ai/benchmark-report.yaml` 中的 {count}schema/content 失败项，修复 Harness 资产后运行 `benchmark`。"
    if action.reason == "benchmark_failed_checks":
        count = f"{action.count} 个 " if action.count else ""
        return f"{prefix}查看 `.ai/benchmark-report.yaml` 中的 {count}失败项，修复后运行 `benchmark`。"
    if action.reason == "experience_index_missing":
        return f"{prefix}运行 `improve` 刷新 Experience index 和成熟度派生证据。"
    if action.reason == "asset_candidates_pending":
        count = f"{action.count} 个 " if action.count else ""
        return f"{prefix}运行 `review-candidate` 处理 {count}review-only 候选，确认 accepted / deferred / rejected。"
    if action.reason == "workflow_recommendations_pending":
        count = f"{action.count} 条 " if action.count else ""
        return f"{prefix}运行 `improve` 把 {count}Workflow 推荐转成可审查的 routing policy 改进候选。"
    if action.reason == "pending_improvements_need_review_package":
        count = f"{action.count} 条 " if action.count else ""
        return f"{prefix}运行 `self-improve` 把 {count}pending improvements 打包成 review-only 自改进审查包。"
    if action.reason == "no_pending_maintenance_signal":
        return f"{prefix}输入一个真实任务说明，运行 `recommend-workflow` 生成 review-only Workflow 推荐；Builder 不执行 Runtime。"
    return f"{prefix}运行 `{action.next_action}` 处理 `{action.reason}`，来源 `{action.source}`。"


def _read_benchmark(ai: Path) -> BenchmarkReport | None:
    path = ai / "benchmark-report.yaml"
    if not path.exists():
        return None
    return BenchmarkReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def _read_experience_index(ai: Path) -> ExperienceIndex | None:
    path = ai / "experience" / "experience-index.yaml"
    if not path.exists():
        return None
    return ExperienceIndex.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def _schema_content_failed_count(report: BenchmarkReport) -> int:
    return sum(
        1
        for check in report.checks
        if not check.passed and (check.id.startswith("schema:") or check.id.startswith("content:"))
    )


def _risk_context_failed_count(report: BenchmarkReport) -> int:
    return sum(1 for check in report.checks if not check.passed and check.id == "content:risk-context-consistency")


def _project_context_evidence_failed_count(report: BenchmarkReport) -> int:
    return sum(1 for check in report.checks if not check.passed and check.id == "content:project-context-evidence-context")


def _project_context_evidence_missing_detail(report: BenchmarkReport) -> str | None:
    for check in report.checks:
        if check.passed or check.id != "content:project-context-evidence-context" or not check.missing:
            continue
        return str(check.missing[0])
    return None


def _hard_gate_weak_command_detail(report: BenchmarkReport) -> tuple[str, str] | None:
    for check in report.checks:
        if check.passed or check.id != "content:hard-gate-command-evidence" or not check.weak_commands:
            continue
        command = check.weak_commands[0]
        command_id = str(command.id or "unknown")
        reason = _weak_command_reason(command)
        source = str(command.source or "missing_source")
        return command_id, f"{command_id}:{reason}:{source}"
    return None


def _weak_command_reason(command) -> str:
    if command.reason:
        return str(command.reason)
    if not command.source:
        return "missing_source"
    if command.confidence == "low":
        return "low_confidence"
    return "weak_command"


def _workflow_recommendation_source(index: ExperienceIndex) -> str:
    for source in index.sources:
        if source.kind == "workflow_recommendation":
            return source.path
    return ".ai/review/workflow-routing-recommendations/index.yaml"
