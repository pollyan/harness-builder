from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from harness_builder_agent.tools.benchmark import run_benchmark
from harness_builder_agent.tools.run_task import run_task
from harness_builder_agent.tools.scan_repo import scan_repository
from harness_builder_agent.tools.write_assets import write_initial_assets

app = typer.Typer(help="Generate and exercise project-level AI Coding Harness assets.")


@app.command("init")
def init_command(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True)) -> None:
    """Scan a repository and generate initial .ai harness assets."""
    inventory, commands = scan_repository(repo)
    output_dir = write_initial_assets(repo, inventory, commands)
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
    report = run_benchmark(repo, profile)
    typer.echo(f"Benchmark {report['status']} for {repo}")
    if report["status"] != "passed":
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
