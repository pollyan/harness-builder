from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
import yaml

from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.benchmark import run_benchmark
from harness_builder_agent.tools.experience_index import write_experience_index
from harness_builder_agent.tools.existing_harness_action_failures import (
    fail_existing_harness_action,
    short_action_error_message,
)
from harness_builder_agent.tools.existing_harness_action_summaries import (
    benchmark_summary,
    self_improve_summary,
    top_improvement_candidate,
    workflow_recommendation_summary,
)
from harness_builder_agent.tools.existing_harness_review_actions import (
    run_review_candidate_action,
    run_review_human_input_action,
    run_review_initial_candidate_action,
)
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.maintenance_triage import MaintenanceAction
from harness_builder_agent.tools.recommend_workflow import recommend_workflow
from harness_builder_agent.tools.self_improve import run_self_improve


def run_existing_harness_action(
    repo: Path,
    ai: Path,
    inventory: ProjectInventory | Any,
    action: str,
    trace,
    maintenance_actions: list[MaintenanceAction],
) -> Path | None:
    if action == "exit":
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness detected; user exited without rewriting formal assets.",
            {"primary_stack": inventory.primary_stack, "action": "exit"},
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "exit",
            },
        )
        return ai
    if action == "assess":
        typer.echo("正在重新评估现有 Harness 成熟度...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose maturity reassessment.",
            {"primary_stack": inventory.primary_stack, "action": "assess"},
        )
        output_dir = assess_maturity(repo)
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-report.md", "maturity_report")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.artifact(output_dir / "init-summary.md", "init_summary")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness maturity assessment refreshed.",
            {"primary_stack": inventory.primary_stack, "action": "assess", "artifact_count": 4},
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "assess",
                "artifact_count": 4,
            },
        )
        typer.echo("成熟度评估已刷新。")
        typer.echo("- `.ai/maturity-score.yaml`")
        typer.echo("- `.ai/maturity-report.md`")
        typer.echo("- `.ai/maturity-evidence.yaml`")
        typer.echo("- `.ai/init-summary.md`")
        return output_dir
    if action == "improve":
        typer.echo("正在生成成熟度驱动的改进候选...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose improvement candidate generation.",
            {"primary_stack": inventory.primary_stack, "action": "improve"},
        )
        write_experience_index(ai)
        output_dir = assess_maturity(repo)
        output_dir = generate_improvements(repo)
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-report.md", "maturity_report")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.artifact(output_dir / "init-summary.md", "init_summary")
        trace.artifact(output_dir / "improvement-candidates.yaml", "improvement_candidates")
        trace.artifact(output_dir / "evolution-plan.md", "plan")
        trace.artifact(output_dir / "experience" / "pending-improvements.md", "experience")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness improvement candidates generated.",
            {"primary_stack": inventory.primary_stack, "action": "improve", "artifact_count": 8},
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "improve",
                "artifact_count": 8,
            },
        )
        typer.echo("改进候选已生成。")
        typer.echo(top_improvement_candidate(output_dir / "improvement-candidates.yaml"))
        typer.echo("- `.ai/improvement-candidates.yaml`")
        typer.echo("- `.ai/evolution-plan.md`")
        typer.echo("- `.ai/experience/pending-improvements.md`")
        typer.echo("- `.ai/experience/experience-index.yaml`")
        return output_dir
    if action == "benchmark":
        typer.echo("正在运行 Harness benchmark...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose benchmark validation.",
            {"primary_stack": inventory.primary_stack, "action": "benchmark"},
        )
        report = BenchmarkReport.model_validate(run_benchmark(repo, profile=inventory.primary_stack, trace=trace))
        failed_checks = [check for check in report.checks if not check.passed]
        output_dir = ai
        trace.artifact(output_dir / "benchmark-report.yaml", "benchmark_report")
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-report.md", "maturity_report")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.artifact(output_dir / "init-summary.md", "init_summary")
        trace.artifact(output_dir / "improvement-candidates.yaml", "improvement_candidates")
        trace.artifact(output_dir / "evolution-plan.md", "plan")
        trace.artifact(output_dir / "experience" / "pending-improvements.md", "experience")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.event(
            "existing-harness",
            "completed" if report.status == "passed" else "failed",
            "Existing Harness benchmark validation completed.",
            {
                "primary_stack": inventory.primary_stack,
                "action": "benchmark",
                "benchmark_status": report.status,
                "quality_status": report.quality_status,
                "failed_check_count": len(failed_checks),
            },
        )
        trace.finish(
            "completed" if report.status == "passed" else "failed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "benchmark",
                "benchmark_status": report.status,
                "quality_status": report.quality_status,
                "check_count": len(report.checks),
                "failed_check_count": len(failed_checks),
            },
        )
        typer.echo(benchmark_summary(report))
        return output_dir
    if action == "recommend-workflow":
        task_brief = typer.prompt("任务说明", default="", show_default=False).strip()
        if not task_brief:
            fail_existing_harness_action(
                trace,
                inventory,
                "recommend-workflow",
                "Workflow recommendation requires a task brief.",
                "empty_task_brief",
            )
        task_id = typer.prompt("任务 ID", default="manual-task").strip() or "manual-task"
        typer.echo("正在生成 review-only Workflow 推荐...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose workflow recommendation.",
            {"primary_stack": inventory.primary_stack, "action": "recommend-workflow", "task_id": task_id},
        )
        try:
            output_dir = recommend_workflow(repo, task_brief=task_brief, task_id=task_id)
            recommendation = WorkflowRecommendationReport.model_validate(
                yaml.safe_load(
                    (output_dir / "review" / "workflow-routing-recommendation.yaml").read_text(encoding="utf-8")
                )
            )
        except Exception as exc:
            fail_existing_harness_action(
                trace,
                inventory,
                "recommend-workflow",
                "Existing Harness workflow recommendation failed.",
                "workflow_recommendation_failed",
                {
                    "task_id": task_id,
                    "error_type": type(exc).__name__,
                    "error_message": short_action_error_message(exc),
                },
            )
        trace.artifact(output_dir / "review" / "workflow-routing-recommendation.yaml", "workflow_recommendation")
        trace.artifact(output_dir / "review" / "workflow-routing-recommendation.md", "review")
        trace.artifact(output_dir / "review" / "workflow-routing-recommendations" / "index.yaml", "workflow_recommendation_history")
        trace.artifact(output_dir / "review" / "workflow-routing-recommendations.md", "review")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness workflow recommendation generated.",
            {
                "primary_stack": inventory.primary_stack,
                "action": "recommend-workflow",
                "task_id": recommendation.task_id,
                "recommended_workflow": recommendation.recommended_workflow,
                "risk_level": recommendation.risk_level,
                "confidence": recommendation.confidence,
            },
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "recommend-workflow",
                "task_id": recommendation.task_id,
                "recommended_workflow": recommendation.recommended_workflow,
                "risk_level": recommendation.risk_level,
                "confidence": recommendation.confidence,
                "human_confirmation_required": recommendation.human_confirmation_required,
            },
        )
        typer.echo(workflow_recommendation_summary(recommendation))
        return output_dir
    if action == "review-candidate":
        return run_review_candidate_action(repo, ai, inventory, trace)
    if action == "review-human-input":
        return run_review_human_input_action(repo, inventory, trace, maintenance_actions)
    if action == "review-initial-candidate":
        return run_review_initial_candidate_action(repo, ai, inventory, trace)
    if action == "self-improve":
        typer.echo("正在生成 review-only 自改进审查包...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose self-improve package generation.",
            {"primary_stack": inventory.primary_stack, "action": "self-improve"},
        )
        try:
            output_dir = run_self_improve(repo)
            manifest = SelfImprovePackageManifest.model_validate(
                yaml.safe_load((output_dir / "review" / "self-improve-package.yaml").read_text(encoding="utf-8"))
            )
        except Exception as exc:
            fail_existing_harness_action(
                trace,
                inventory,
                "self-improve",
                "Existing Harness self-improve package generation failed.",
                "self_improve_failed",
                {
                    "error_type": type(exc).__name__,
                    "error_message": short_action_error_message(exc),
                },
            )
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.artifact(output_dir / "improvement-candidates.yaml", "improvement_candidates")
        trace.artifact(output_dir / "evolution-plan.md", "plan")
        trace.artifact(output_dir / "experience" / "pending-improvements.md", "experience")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.artifact(output_dir / "review" / "maturity-review.yaml", "maturity_review")
        trace.artifact(output_dir / "review" / "maturity-review.md", "review")
        trace.artifact(output_dir / "review" / "asset-candidates.yaml", "asset_candidates")
        trace.artifact(output_dir / "review" / "asset-candidate-guides.md", "review")
        trace.artifact(output_dir / "review" / "asset-candidate-sensors.md", "review")
        trace.artifact(output_dir / "review" / "asset-candidate-workflows.md", "review")
        trace.artifact(output_dir / "review" / "self-improve-package.yaml", "self_improve_package")
        trace.artifact(output_dir / "review" / "self-improve-package.md", "review")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness self-improve package generated.",
            {
                "primary_stack": inventory.primary_stack,
                "action": "self-improve",
                "improvement_candidate_count": manifest.candidate_counts.improvement_candidates,
                "asset_candidate_count": manifest.candidate_counts.asset_candidates,
            },
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "self-improve",
                "overall_level": manifest.maturity.overall_level,
                "target_next_level": manifest.maturity.target_next_level,
                "improvement_candidate_count": manifest.candidate_counts.improvement_candidates,
                "maturity_review_count": manifest.candidate_counts.maturity_reviews,
                "asset_candidate_count": manifest.candidate_counts.asset_candidates,
            },
        )
        typer.echo(self_improve_summary(manifest))
        return output_dir
    if action == "reinit":
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness detected; user chose to continue guided regeneration.",
            {"primary_stack": inventory.primary_stack, "action": "reinit"},
        )
        return None
    fail_existing_harness_action(
        trace,
        inventory,
        action,
        "Unknown existing Harness action.",
        "unknown_existing_harness_action",
    )
    return None
