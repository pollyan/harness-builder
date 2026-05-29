from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Generate and exercise project-level AI Coding Harness assets.")


@app.command("init")
def init_command(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True)) -> None:
    """Scan a repository and generate initial .ai harness assets."""
    typer.echo(f"init not implemented yet: {repo}")


@app.command("run")
def run_command(
    task: str = typer.Argument(...),
    repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True),
) -> None:
    """Generate a task-level harness map and controlled task handoff assets."""
    typer.echo(f"run not implemented yet: {repo} :: {task}")


@app.command("benchmark")
def benchmark_command(
    repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, dir_okay=True),
    profile: Optional[str] = typer.Option(None, "--profile"),
) -> None:
    """Run benchmark checks for a fixture or real target repository."""
    typer.echo(f"benchmark not implemented yet: {repo} :: {profile or 'auto'}")


def main() -> None:
    app()
