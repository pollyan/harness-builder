from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from harness_builder_agent.tools.benchmark import run_benchmark
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.run_task import run_task
from harness_builder_agent.tools.scan_repo import scan_repository
from harness_builder_agent.tools.write_assets import write_initial_assets

app = typer.Typer(help="Generate and exercise project-level AI Coding Harness assets.")


@app.command("init")
def init_command(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True)) -> None:
    """Scan a repository and generate initial .ai harness assets."""
    trace = GenerationTrace.start(repo, "init")
    try:
        trace.event("scan", "started", "Repository scan started.")
        inventory, commands = scan_repository(repo)
        trace.event(
            "scan",
            "completed",
            "Repository scan completed.",
            {"primary_stack": inventory.primary_stack, "stacks": inventory.stacks, "command_count": len(commands.commands)},
        )
        output_dir = write_initial_assets(repo, inventory, commands, trace=trace)
        trace.finish("completed", {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)})
    except Exception as exc:
        trace.event("init", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Generated harness assets in {output_dir}")


@app.command("run")
def run_command(
    task: str = typer.Argument(...),
    repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True),
) -> None:
    """Generate a task-level harness map and controlled task handoff assets."""
    task_dir = run_task(repo, task)
    typer.echo(f"Generated task run assets in {task_dir}")


@app.command("benchmark")
def benchmark_command(
    repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True),
    profile: Optional[str] = typer.Option(None, "--profile"),
) -> None:
    """Run benchmark checks for a fixture or real target repository."""
    trace = GenerationTrace.start(repo, "benchmark")
    try:
        trace.event("benchmark", "started", "Benchmark started.", {"profile": profile})
        report = run_benchmark(repo, profile)
        report_path = repo.resolve() / ".ai" / "benchmark-report.yaml"
        trace.artifact(report_path, "benchmark_report")
        event_type = "completed" if report["status"] == "passed" else "failed"
        trace.event(
            "benchmark",
            event_type,
            f"Benchmark {report['status']}.",
            {"profile": report["profile"], "status": report["status"], "check_count": len(report["checks"])},
        )
        trace.finish("completed" if report["status"] == "passed" else "failed", {"status": report["status"], "profile": report["profile"]})
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
        trace.event("maturity", "completed", "Maturity assessment completed.", {"artifact_count": 2})
        trace.finish("completed", {"artifact_count": 2})
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
        trace.event("improvement", "completed", "Improvement candidate generation completed.", {"artifact_count": 3})
        trace.finish("completed", {"artifact_count": 3})
    except Exception as exc:
        trace.event("improvement", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Generated improvement candidates in {output_dir}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
