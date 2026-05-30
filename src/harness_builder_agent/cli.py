from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from harness_builder_agent.tools.benchmark import run_benchmark
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.interactive_init import run_guided_init, run_non_interactive_init

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
    except Exception as exc:
        trace.event("init", "failed", str(exc), {"error_type": type(exc).__name__})
        trace.finish("failed", {"error_type": type(exc).__name__})
        raise
    typer.echo(f"Generated harness assets in {output_dir}")


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
        trace.event("maturity", "completed", "Maturity assessment completed.", {"artifact_count": 3})
        trace.finish("completed", {"artifact_count": 3})
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


def _stdin_is_tty() -> bool:
    return typer.get_text_stream("stdin").isatty()


if __name__ == "__main__":
    main()
