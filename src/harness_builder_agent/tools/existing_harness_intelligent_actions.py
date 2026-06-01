from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
import yaml

from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools.existing_harness_action_failures import (
    fail_existing_harness_action,
    short_action_error_message,
)
from harness_builder_agent.tools.existing_harness_action_summaries import (
    self_improve_summary,
    workflow_recommendation_summary,
)
from harness_builder_agent.tools.recommend_workflow import recommend_workflow
from harness_builder_agent.tools.self_improve import run_self_improve


def run_recommend_workflow_action(repo: Path, inventory: ProjectInventory | Any, trace) -> Path:
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
    trace.artifact(
        output_dir / "review" / "workflow-routing-recommendations" / "index.yaml",
        "workflow_recommendation_history",
    )
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


def run_self_improve_action(repo: Path, inventory: ProjectInventory | Any, trace) -> Path:
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
