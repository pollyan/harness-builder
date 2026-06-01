from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
import yaml

from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceLog
from harness_builder_agent.schemas.human_input_governance import HumanInputGovernanceLog
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.benchmark import run_benchmark
from harness_builder_agent.tools.candidate_governance import review_candidate
from harness_builder_agent.tools.experience_index import write_experience_index
from harness_builder_agent.tools.existing_harness_action_summaries import (
    asset_candidate_apply_preview,
    asset_candidate_detail,
    benchmark_summary,
    candidate_governance_summary,
    human_input_governance_summary,
    self_improve_summary,
    top_improvement_candidate,
    workflow_recommendation_summary,
)
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.human_input_governance import review_human_input
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
            trace.event(
                "existing-harness",
                "failed",
                "Workflow recommendation requires a task brief.",
                {"primary_stack": inventory.primary_stack, "action": "recommend-workflow"},
            )
            trace.finish(
                "failed",
                {
                    "primary_stack": inventory.primary_stack,
                    "existing_harness_action": "recommend-workflow",
                    "error": "empty_task_brief",
                },
            )
            raise typer.BadParameter("recommend-workflow requires a non-empty task brief.")
        task_id = typer.prompt("任务 ID", default="manual-task").strip() or "manual-task"
        typer.echo("正在生成 review-only Workflow 推荐...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose workflow recommendation.",
            {"primary_stack": inventory.primary_stack, "action": "recommend-workflow", "task_id": task_id},
        )
        output_dir = recommend_workflow(repo, task_brief=task_brief, task_id=task_id)
        recommendation = WorkflowRecommendationReport.model_validate(
            yaml.safe_load((output_dir / "review" / "workflow-routing-recommendation.yaml").read_text(encoding="utf-8"))
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
        candidate_report = show_asset_candidate_summary(ai / "review" / "asset-candidates.yaml")
        candidate_id = typer.prompt("候选 ID", default="", show_default=False).strip()
        candidate = find_asset_candidate(candidate_report, candidate_id)
        typer.echo(asset_candidate_detail(candidate))
        typer.echo(asset_candidate_apply_preview(repo, candidate))
        decision = typer.prompt("决策 accepted/deferred/rejected/applied", default="deferred").strip().lower()
        if decision == "applied" and candidate.kind == "workflow_policy":
            trace.event(
                "existing-harness",
                "failed",
                "Guided candidate governance does not apply workflow policy candidates.",
                {"primary_stack": inventory.primary_stack, "action": "review-candidate", "candidate_id": candidate_id},
            )
            trace.finish(
                "failed",
                {
                    "primary_stack": inventory.primary_stack,
                    "existing_harness_action": "review-candidate",
                    "candidate_id": candidate_id,
                    "error": "workflow_policy_applied_requires_expert_command",
                },
            )
            raise typer.BadParameter("guided workflow_policy applied requires the expert command with structured patch review.")
        if decision not in {"accepted", "deferred", "rejected", "applied"}:
            trace.event(
                "existing-harness",
                "failed",
                "Unsupported guided candidate governance decision.",
                {"primary_stack": inventory.primary_stack, "action": "review-candidate", "candidate_id": candidate_id, "decision": decision},
            )
            trace.finish(
                "failed",
                {
                    "primary_stack": inventory.primary_stack,
                    "existing_harness_action": "review-candidate",
                    "candidate_id": candidate_id,
                    "decision": decision,
                    "error": "unsupported_decision",
                },
            )
            raise typer.BadParameter("decision must be accepted, deferred, rejected, or applied.")
        rationale = typer.prompt("决策理由", default="", show_default=False).strip()
        reviewer = typer.prompt("Reviewer", default="harness-maintainer").strip() or "harness-maintainer"
        typer.echo("正在记录候选治理决策...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose candidate governance.",
            {"primary_stack": inventory.primary_stack, "action": "review-candidate", "candidate_id": candidate_id, "decision": decision},
        )
        try:
            output_dir = review_candidate(repo, candidate_id, decision, rationale, reviewer)
        except (FileNotFoundError, ValueError) as exc:
            trace.event(
                "existing-harness",
                "failed",
                "Existing Harness candidate governance failed.",
                {
                    "primary_stack": inventory.primary_stack,
                    "action": "review-candidate",
                    "candidate_id": candidate_id,
                    "decision": decision,
                    "error": str(exc),
                },
            )
            trace.finish(
                "failed",
                {
                    "primary_stack": inventory.primary_stack,
                    "existing_harness_action": "review-candidate",
                    "candidate_id": candidate_id,
                    "decision": decision,
                    "error": str(exc),
                },
            )
            raise typer.BadParameter(str(exc)) from exc
        governance = CandidateGovernanceLog.model_validate(
            yaml.safe_load((output_dir / "review" / "candidate-governance.yaml").read_text(encoding="utf-8"))
        )
        latest = governance.decisions[-1]
        trace.artifact(output_dir / "review" / "candidate-governance.yaml", "candidate_governance")
        trace.artifact(output_dir / "review" / "candidate-governance.md", "review")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness candidate governance decision recorded.",
            {
                "primary_stack": inventory.primary_stack,
                "action": "review-candidate",
                "candidate_id": latest.candidate_id,
                "decision": latest.decision,
                "reviewer": latest.reviewer,
            },
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "review-candidate",
                "candidate_id": latest.candidate_id,
                "decision": latest.decision,
                "reviewer": latest.reviewer,
                "applied_path_count": len(latest.applied_paths),
            },
        )
        typer.echo(candidate_governance_summary(latest.candidate_id, latest.decision, latest.reviewer, len(latest.applied_paths)))
        return output_dir
    if action == "review-human-input":
        default_interaction_id = review_human_input_default_interaction_id(maintenance_actions)
        interaction_id = typer.prompt(
            "Human input interaction ID",
            default=default_interaction_id or "",
            show_default=default_interaction_id is not None,
        ).strip()
        decision = typer.prompt("决策 resolved/reopened", default="resolved").strip().lower()
        rationale = typer.prompt("决策理由", default="", show_default=False).strip()
        reviewer = typer.prompt("Reviewer", default="harness-maintainer").strip() or "harness-maintainer"
        typer.echo("正在记录 human-input 治理决策...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose human input governance.",
            {"primary_stack": inventory.primary_stack, "action": "review-human-input", "interaction_id": interaction_id, "decision": decision},
        )
        try:
            output_dir = review_human_input(repo, interaction_id, decision, rationale, reviewer)
        except (FileNotFoundError, ValueError) as exc:
            trace.event(
                "existing-harness",
                "failed",
                "Existing Harness human input governance failed.",
                {
                    "primary_stack": inventory.primary_stack,
                    "action": "review-human-input",
                    "interaction_id": interaction_id,
                    "decision": decision,
                    "error": str(exc),
                },
            )
            trace.finish(
                "failed",
                {
                    "primary_stack": inventory.primary_stack,
                    "existing_harness_action": "review-human-input",
                    "interaction_id": interaction_id,
                    "decision": decision,
                    "error": str(exc),
                },
            )
            raise typer.BadParameter(str(exc)) from exc
        governance = HumanInputGovernanceLog.model_validate(
            yaml.safe_load((output_dir / "review" / "human-input-governance.yaml").read_text(encoding="utf-8"))
        )
        latest = governance.decisions[-1]
        trace.artifact(output_dir / "questionnaire.yaml", "questionnaire")
        trace.artifact(output_dir / "human-input-needed.md", "human_confirmation")
        trace.artifact(output_dir / "review" / "human-input-governance.yaml", "human_input_governance")
        trace.artifact(output_dir / "review" / "human-input-governance.md", "review")
        trace.event(
            "existing-harness",
            "completed",
            "Existing Harness human input governance decision recorded.",
            {
                "primary_stack": inventory.primary_stack,
                "action": "review-human-input",
                "interaction_id": latest.interaction_id,
                "decision": latest.decision,
                "reviewer": latest.reviewer,
            },
        )
        trace.finish(
            "completed",
            {
                "primary_stack": inventory.primary_stack,
                "existing_harness_action": "review-human-input",
                "interaction_id": latest.interaction_id,
                "decision": latest.decision,
                "reviewer": latest.reviewer,
                "new_response_status": latest.new_response_status,
            },
        )
        typer.echo(human_input_governance_summary(latest.interaction_id, latest.decision, latest.reviewer, latest.new_response_status))
        return output_dir
    if action == "self-improve":
        typer.echo("正在生成 review-only 自改进审查包...")
        trace.event(
            "existing-harness",
            "started",
            "Existing Harness detected; user chose self-improve package generation.",
            {"primary_stack": inventory.primary_stack, "action": "self-improve"},
        )
        output_dir = run_self_improve(repo)
        manifest = SelfImprovePackageManifest.model_validate(
            yaml.safe_load((output_dir / "review" / "self-improve-package.yaml").read_text(encoding="utf-8"))
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
    typer.echo("未识别的选择，默认退出且不覆盖现有 Harness。")
    trace.event(
        "existing-harness",
        "warning",
        "Unknown existing Harness action; defaulted to exit.",
        {"primary_stack": inventory.primary_stack, "action": action},
    )
    trace.finish(
        "completed",
        {
            "primary_stack": inventory.primary_stack,
            "existing_harness_action": "exit",
        },
    )
    return ai


def review_human_input_default_interaction_id(maintenance_actions: list[MaintenanceAction]) -> str | None:
    for action in maintenance_actions:
        if action.action == "review-human-input" and action.reason == "human_input_scan_followups_pending":
            return action.detail
    return None


def show_asset_candidate_summary(path: Path) -> AssetCandidateReport:
    report = AssetCandidateReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    typer.echo("\n待治理候选")
    for candidate in report.candidates[:10]:
        typer.echo(
            f"- `{candidate.id}`：{candidate.title}，kind={candidate.kind}，"
            f"target=`{candidate.suggested_path}`，risk={candidate.risk_level}"
        )
    if len(report.candidates) > 10:
        typer.echo(f"- 还有 {len(report.candidates) - 10} 个候选，请查看 `.ai/review/asset-candidates.yaml`。")
    typer.echo("guided review-candidate 可记录 accepted/deferred/rejected；Guide/Sensor 候选可显式 applied。")
    typer.echo("workflow_policy 候选应用仍需使用专家命令。")
    return report


def find_asset_candidate(report: AssetCandidateReport, candidate_id: str):
    for candidate in report.candidates:
        if candidate.id == candidate_id:
            return candidate
    raise typer.BadParameter(f"unknown asset candidate id: {candidate_id}")
