from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml

from harness_builder_agent.tools.benchmark import run_benchmark
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.candidate_governance import review_candidate
from harness_builder_agent.tools.generate_asset_candidates import generate_asset_candidates
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.human_input_governance import review_human_input
from harness_builder_agent.tools.init_summary import render_init_completion_message
from harness_builder_agent.tools.interactive_init import run_guided_init, run_non_interactive_init
from harness_builder_agent.tools.recommend_workflow import recommend_workflow
from harness_builder_agent.tools.review_maturity import review_maturity
from harness_builder_agent.tools.self_improve import run_self_improve
from harness_builder_agent.tools.summarize_experience import summarize_experience

app = typer.Typer(help="Generate, assess, improve, and benchmark project-level AI Coding Harness assets.")


@app.command("init")
def init_command(
    repo: Optional[Path] = typer.Option(None, "--repo", file_okay=False, dir_okay=True),
    context: Optional[list[Path]] = typer.Option(None, "--context", exists=True, file_okay=True, dir_okay=False),
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Run init without prompts for CI, scripts, and acceptance.",
    ),
) -> None:
    """Scan a repository and generate initial .ai harness assets."""
    target_repo = (repo or Path.cwd()).resolve()
    if not target_repo.exists() or not target_repo.is_dir():
        raise typer.BadParameter(f"Repository path must be an existing directory: {target_repo}")
    if not non_interactive and not _stdin_is_tty():
        raise typer.BadParameter("`init` defaults to guided interactive mode. Non-TTY automation must pass --non-interactive.")
    trace = GenerationTrace.start(target_repo, "init")
    try:
        if non_interactive:
            output_dir = run_non_interactive_init(target_repo, context or [], trace)
        else:
            output_dir = run_guided_init(target_repo, context or [], trace)
    except (typer.Exit, typer.Abort):
        raise
    except Exception as exc:
        trace.event("init", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    if _should_render_initial_init_completion(trace):
        typer.echo(render_init_completion_message(output_dir))


def _should_render_initial_init_completion(trace: GenerationTrace) -> bool:
    trace_payload = yaml.safe_load((trace.run_dir / "trace.yaml").read_text(encoding="utf-8"))
    summary = trace_payload.get("summary", {}) if isinstance(trace_payload, dict) else {}
    return "existing_harness_action" not in summary


@app.command("benchmark")
def benchmark_command(
    repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True),
    profile: Optional[str] = typer.Option(None, "--profile"),
) -> None:
    """Run benchmark checks for a fixture or real target repository."""
    trace = GenerationTrace.start(repo, "benchmark")
    try:
        report = run_benchmark(repo, profile, trace=trace)
    except Exception as exc:
        trace.event("benchmark", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Benchmark {report['status']} for {repo}")
    if report["status"] != "passed":
        raise typer.Exit(code=1)


@app.command("assess")
def assess_command(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True)) -> None:
    """Re-assess generated harness maturity and write maturity score assets."""
    trace = GenerationTrace.start(repo, "assess")
    try:
        trace.event("maturity", "started", "Maturity assessment started.")
        output_dir = assess_maturity(repo)
        trace.artifact(output_dir / "maturity-report.md", "maturity_report")
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.artifact(output_dir / "init-summary.md", "init_summary")
        trace.event("maturity", "completed", "Maturity assessment completed.", {"artifact_count": 4})
        trace.finish("completed", {"artifact_count": 4})
    except Exception as exc:
        trace.event("maturity", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Updated maturity assets in {output_dir}")


@app.command("improve")
def improve_command(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True)) -> None:
    """Generate reviewable harness improvement candidates."""
    trace = GenerationTrace.start(repo, "improve")
    try:
        trace.event("improvement", "started", "Improvement candidate generation started.")
        output_dir = generate_improvements(repo)
        trace.artifact(output_dir / "improvement-candidates.yaml", "improvement_candidates")
        trace.artifact(output_dir / "evolution-plan.md", "plan")
        trace.artifact(output_dir / "experience" / "pending-improvements.md", "experience")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.event("improvement", "completed", "Improvement candidate generation completed.", {"artifact_count": 4})
        trace.finish("completed", {"artifact_count": 4})
    except Exception as exc:
        trace.event("improvement", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Generated improvement candidates in {output_dir}")


@app.command("self-improve")
def self_improve_command(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True)) -> None:
    """Generate one review-only maturity-driven self-improvement package."""
    trace = GenerationTrace.start(repo, "self-improve")
    try:
        trace.event("self-improve", "started", "Self-improve package generation started.")
        output_dir = run_self_improve(repo)
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.artifact(output_dir / "improvement-candidates.yaml", "improvement_candidates")
        trace.artifact(output_dir / "review" / "maturity-review.yaml", "maturity_review")
        trace.artifact(output_dir / "review" / "asset-candidates.yaml", "asset_candidates")
        trace.artifact(output_dir / "review" / "self-improve-package.yaml", "self_improve_package")
        trace.artifact(output_dir / "review" / "self-improve-package.md", "review")
        trace.event("self-improve", "completed", "Self-improve package generation completed.", {"artifact_count": 7})
        trace.finish("completed", {"artifact_count": 7})
    except Exception as exc:
        trace.event("self-improve", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Generated self-improve package in {output_dir / 'review'}")


@app.command("review-maturity")
def review_maturity_command(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True)) -> None:
    """Run explicit LLM review for maturity-driven improvement candidates."""
    trace = GenerationTrace.start(repo, "review-maturity")
    try:
        trace.event("maturity-review", "started", "LLM maturity review started.")
        output_dir = review_maturity(repo)
        trace.artifact(output_dir / "review" / "maturity-review.yaml", "maturity_review")
        trace.artifact(output_dir / "review" / "maturity-review.md", "review")
        trace.event("maturity-review", "completed", "LLM maturity review completed.", {"artifact_count": 2})
        trace.finish("completed", {"artifact_count": 2})
    except Exception as exc:
        trace.event("maturity-review", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Generated maturity review in {output_dir / 'review'}")


@app.command("generate-asset-candidates")
def generate_asset_candidates_command(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True)) -> None:
    """Generate review-only draft Guide, Sensor, and Workflow asset candidates."""
    trace = GenerationTrace.start(repo, "generate-asset-candidates")
    try:
        trace.event("asset-candidates", "started", "Asset candidate generation started.")
        output_dir = generate_asset_candidates(repo)
        trace.artifact(output_dir / "review" / "asset-candidates.yaml", "asset_candidates")
        trace.artifact(output_dir / "review" / "asset-candidate-guides.md", "review")
        trace.artifact(output_dir / "review" / "asset-candidate-sensors.md", "review")
        trace.artifact(output_dir / "review" / "asset-candidate-workflows.md", "review")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.event("asset-candidates", "completed", "Asset candidate generation completed.", {"artifact_count": 7})
        trace.finish("completed", {"artifact_count": 7})
    except Exception as exc:
        trace.event("asset-candidates", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Generated asset candidates in {output_dir / 'review'}")


@app.command("review-candidate")
def review_candidate_command(
    repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True),
    candidate_id: str = typer.Option(..., "--candidate-id", help="Asset candidate id from .ai/review/asset-candidates.yaml."),
    decision: str = typer.Option(..., "--decision", help="accepted, deferred, rejected, or applied."),
    rationale: str = typer.Option(..., "--rationale", help="Maintainer rationale for the governance decision."),
    reviewer: str = typer.Option("harness-maintainer", "--reviewer", help="Reviewer identity recorded in governance artifacts."),
) -> None:
    """Record a governance decision for a review-only asset candidate."""
    trace = GenerationTrace.start(repo, "review-candidate")
    try:
        trace.event("candidate-governance", "started", "Candidate governance decision started.", {"candidate_id": candidate_id})
        output_dir = review_candidate(repo, candidate_id, decision, rationale, reviewer)
        trace.artifact(output_dir / "review" / "candidate-governance.yaml", "candidate_governance")
        trace.artifact(output_dir / "review" / "candidate-governance.md", "review")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        if (output_dir / "maturity-score.yaml").exists():
            trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        if (output_dir / "maturity-evidence.yaml").exists():
            trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.event(
            "candidate-governance",
            "completed",
            "Candidate governance decision completed.",
            {"candidate_id": candidate_id, "decision": decision},
        )
        trace.finish("completed", {"candidate_id": candidate_id, "decision": decision})
    except Exception as exc:
        trace.event("candidate-governance", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Recorded candidate governance decision in {output_dir / 'review'}")


@app.command("review-human-input")
def review_human_input_command(
    repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True),
    interaction_id: str = typer.Option(..., "--interaction-id", help="Human input interaction id from .ai/questionnaire.yaml."),
    decision: str = typer.Option(..., "--decision", help="resolved or reopened."),
    rationale: str = typer.Option(..., "--rationale", help="Maintainer rationale for the human input review decision."),
    reviewer: str = typer.Option("harness-maintainer", "--reviewer", help="Reviewer identity recorded in governance artifacts."),
) -> None:
    """Record a governance decision for a scan follow-up human input item."""
    trace = GenerationTrace.start(repo, "review-human-input")
    try:
        trace.event(
            "human-input-governance",
            "started",
            "Human input governance decision started.",
            {"interaction_id": interaction_id},
        )
        output_dir = review_human_input(repo, interaction_id, decision, rationale, reviewer)
        trace.artifact(output_dir / "questionnaire.yaml", "questionnaire")
        trace.artifact(output_dir / "human-input-needed.md", "human_confirmation")
        trace.artifact(output_dir / "review" / "human-input-governance.yaml", "human_input_governance")
        trace.artifact(output_dir / "review" / "human-input-governance.md", "review")
        trace.event(
            "human-input-governance",
            "completed",
            "Human input governance decision completed.",
            {"interaction_id": interaction_id, "decision": decision},
        )
        trace.finish("completed", {"interaction_id": interaction_id, "decision": decision})
    except Exception as exc:
        trace.event("human-input-governance", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Recorded human input governance decision in {output_dir / 'review'}")


@app.command("recommend-workflow")
def recommend_workflow_command(
    repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True),
    task: str = typer.Option(..., "--task", help="Task brief to evaluate against the workflow routing policy."),
    task_id: str = typer.Option("manual-task", "--task-id", help="Stable task id for the recommendation artifact."),
) -> None:
    """Generate a review-only workflow recommendation for a task brief."""
    trace = GenerationTrace.start(repo, "recommend-workflow")
    try:
        trace.event("workflow-recommendation", "started", "Workflow recommendation started.", {"task_id": task_id})
        output_dir = recommend_workflow(repo, task_brief=task, task_id=task_id)
        trace.artifact(output_dir / "review" / "workflow-routing-recommendation.yaml", "workflow_recommendation")
        trace.artifact(output_dir / "review" / "workflow-routing-recommendation.md", "review")
        trace.artifact(output_dir / "review" / "workflow-routing-recommendations" / "index.yaml", "workflow_recommendation_history")
        trace.artifact(output_dir / "review" / "workflow-routing-recommendations.md", "review")
        trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
        trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.event("workflow-recommendation", "completed", "Workflow recommendation completed.", {"artifact_count": 7})
        trace.finish("completed", {"artifact_count": 7})
    except Exception as exc:
        trace.event("workflow-recommendation", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Generated workflow recommendation in {output_dir / 'review'}")


@app.command("summarize-experience")
def summarize_experience_command(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True)) -> None:
    """Run LLM semantic summarization over review-only Experience evidence."""
    trace = GenerationTrace.start(repo, "summarize-experience")
    try:
        trace.event("experience-summary", "started", "LLM experience summary started.")
        output_dir = summarize_experience(repo)
        trace.artifact(output_dir / "experience" / "experience-summary.yaml", "experience_summary")
        trace.artifact(output_dir / "experience" / "experience-summary.md", "experience")
        trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
        trace.event("experience-summary", "completed", "LLM experience summary completed.", {"artifact_count": 3})
        trace.finish("completed", {"artifact_count": 3})
    except Exception as exc:
        trace.event("experience-summary", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Generated experience summary in {output_dir / 'experience'}")


def main() -> None:
    app()


def _stdin_is_tty() -> bool:
    return typer.get_text_stream("stdin").isatty()


if __name__ == "__main__":
    main()
