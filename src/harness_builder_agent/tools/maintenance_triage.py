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
        schema_content_failed = _schema_content_failed_count(benchmark)
        if schema_content_failed:
            actions.append(
                MaintenanceAction(
                    priority=15,
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
        lines.append(
            f"top_action_{index}={action.action} "
            f"reason={action.reason} "
            f"source={action.source} "
            f"next={action.next_action}"
            f"{count}"
        )
    return lines


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


def _workflow_recommendation_source(index: ExperienceIndex) -> str:
    for source in index.sources:
        if source.kind == "workflow_recommendation":
            return source.path
    return ".ai/review/workflow-routing-recommendations/index.yaml"
