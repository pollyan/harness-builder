from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.benchmark import run_benchmark
from harness_builder_agent.tools.experience_index import write_experience_index
from harness_builder_agent.tools.existing_harness_action_summaries import (
    benchmark_summary,
    top_improvement_candidate,
)
from harness_builder_agent.tools.generate_improvements import generate_improvements


def run_assess_action(repo: Path, inventory: ProjectInventory | Any, trace) -> Path:
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


def run_improve_action(repo: Path, ai: Path, inventory: ProjectInventory | Any, trace) -> Path:
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


def run_benchmark_action(repo: Path, ai: Path, inventory: ProjectInventory | Any, trace) -> Path:
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
