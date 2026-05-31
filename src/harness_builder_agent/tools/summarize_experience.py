from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.experience_index import write_experience_index
from harness_builder_agent.tools.llm_experience_summarizer import summarize_experience_with_llm
from harness_builder_agent.tools.runtime_task_runs import render_runtime_task_run_source

SOURCE_PATHS = [
    ".ai/experience/pending-improvements.md",
    ".ai/experience/project-experience.md",
    ".ai/experience/repair-patterns.md",
    ".ai/experience/sensor-feedback.md",
    ".ai/experience/team-preferences.md",
    ".ai/experience/deprecated-experience.md",
    ".ai/review/maturity-review.yaml",
    ".ai/review/asset-candidates.yaml",
    ".ai/review/workflow-routing-recommendation.yaml",
]


def summarize_experience(repo: Path) -> Path:
    root = repo.resolve()
    ai = root / ".ai"
    if not ai.exists():
        raise FileNotFoundError(f"Missing .ai harness directory: {ai}")
    if not (ai / "experience" / "experience-index.yaml").exists():
        write_experience_index(ai)
    index = ExperienceIndex.model_validate(yaml.safe_load((ai / "experience" / "experience-index.yaml").read_text(encoding="utf-8")))
    sources = _collect_sources(root)
    report = summarize_experience_with_llm(index, sources)
    _write_yaml(ai / "experience" / "experience-summary.yaml", report.model_dump(mode="json"))
    (ai / "experience" / "experience-summary.md").write_text(_summary_markdown(report), encoding="utf-8")
    write_experience_index(ai)
    assess_maturity(root)
    return ai


def _collect_sources(root: Path) -> dict[str, str]:
    sources: dict[str, str] = {}
    for rel in SOURCE_PATHS:
        path = root / rel
        if path.exists():
            sources[rel] = path.read_text(encoding="utf-8")[:12000]
    task_runs = root / ".ai" / "task-runs"
    if task_runs.exists():
        for run_dir in sorted(path for path in task_runs.iterdir() if path.is_dir()):
            sources[f".ai/task-runs/{run_dir.name}/"] = render_runtime_task_run_source(run_dir)[:12000]
    return sources


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _summary_markdown(report: ExperienceSummaryReport) -> str:
    finding_sections = "\n\n".join(
        f"### {item.title}\n\n"
        f"- id: `{item.id}`\n"
        f"- kind: `{item.kind}`\n"
        f"- confidence: `{item.confidence}`\n"
        f"- evidence: {', '.join(f'`{source}`' for source in item.evidence_sources) or 'none'}\n\n"
        f"{item.summary}\n\n"
        f"Follow-up: {item.suggested_follow_up or 'None.'}"
        for item in report.findings
    ) or "No findings."
    warnings = "\n".join(f"- {item}" for item in report.warnings) or "- None."
    return (
        "# Experience Summary\n\n"
        f"- review status: `{report.review_status}`\n"
        f"- source: `{report.source}`\n\n"
        "## Summary\n\n"
        f"{report.summary}\n\n"
        "## Findings\n\n"
        f"{finding_sections}\n\n"
        "## Warnings\n\n"
        f"{warnings}\n"
    )
