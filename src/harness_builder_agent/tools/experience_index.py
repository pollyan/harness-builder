from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.experience_index import ExperienceIndex, ExperienceSource
from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceLog
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_yaml
from harness_builder_agent.tools.generation_trace import GenerationTrace

EXPERIENCE_FILES = {
    "project-experience.md": "# Project Experience\n\n## Recorded Experience\n\nNo project experience recorded yet.\n",
    "repair-patterns.md": "# Repair Patterns\n\n## Recorded Patterns\n\nNo repair patterns recorded yet.\n",
    "sensor-feedback.md": "# Sensor Feedback\n\n## Recorded Feedback\n\nNo sensor feedback recorded yet.\n",
    "team-preferences.md": "# Team Preferences\n\n## Recorded Preferences\n\nNo team preferences recorded yet.\n",
    "deprecated-experience.md": "# Deprecated Experience\n\n## Deprecated Items\n\nNo deprecated experience recorded yet.\n",
}


def ensure_experience_files(ai: Path) -> None:
    experience = ai / "experience"
    experience.mkdir(parents=True, exist_ok=True)
    for name, content in EXPERIENCE_FILES.items():
        path = experience / name
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def write_experience_index(ai: Path, trace: GenerationTrace | None = None) -> ExperienceIndex:
    ensure_experience_files(ai)
    index = build_experience_index(ai)
    write_yaml(ai / "experience" / "experience-index.yaml", index.model_dump(mode="json"))
    record_artifact(trace, ai / "experience" / "experience-index.yaml", "experience_index")
    return index


def build_experience_index(ai: Path) -> ExperienceIndex:
    experience = ai / "experience"
    pending_count = _pending_improvement_count(experience / "pending-improvements.md")
    asset_candidate_count = _yaml_candidate_count(ai / "review" / "asset-candidates.yaml")
    maturity_review_count = _yaml_candidate_count(ai / "review" / "maturity-review.yaml", key="candidate_reviews")
    candidate_governance_decision_count = _candidate_governance_count(ai / "review" / "candidate-governance.yaml")
    workflow_recommendation_count = _workflow_recommendation_count(ai / "review" / "workflow-routing-recommendation.yaml")
    task_runs = ai / "task-runs"
    runtime_task_run_count = sum(1 for path in task_runs.iterdir() if path.is_dir()) if task_runs.exists() else 0
    sources: list[ExperienceSource] = [
        ExperienceSource(path=".ai/experience/pending-improvements.md", kind="pending_improvements", item_count=pending_count)
    ]
    if (ai / "review" / "maturity-review.yaml").exists():
        sources.append(ExperienceSource(path=".ai/review/maturity-review.yaml", kind="maturity_review", item_count=maturity_review_count))
    if (ai / "review" / "asset-candidates.yaml").exists():
        sources.append(ExperienceSource(path=".ai/review/asset-candidates.yaml", kind="asset_candidates", item_count=asset_candidate_count))
    if (ai / "review" / "candidate-governance.yaml").exists():
        sources.append(
            ExperienceSource(
                path=".ai/review/candidate-governance.yaml",
                kind="candidate_governance",
                item_count=candidate_governance_decision_count,
            )
        )
    if workflow_recommendation_count:
        sources.append(
            ExperienceSource(
                path=".ai/review/workflow-routing-recommendation.yaml",
                kind="workflow_recommendation",
                item_count=workflow_recommendation_count,
            )
        )
    if runtime_task_run_count:
        sources.append(ExperienceSource(path=".ai/task-runs/", kind="runtime_task_runs", item_count=runtime_task_run_count))

    warnings: list[str] = []
    if runtime_task_run_count == 0:
        warnings.append("runtime task-runs absent; experience is based on generated candidates and reviews only")
    return ExperienceIndex(
        experience_files={name: (experience / name).exists() for name in [*EXPERIENCE_FILES, "pending-improvements.md"]},
        sources=sources,
        pending_improvement_count=pending_count,
        asset_candidate_count=asset_candidate_count,
        maturity_review_count=maturity_review_count,
        candidate_governance_decision_count=candidate_governance_decision_count,
        workflow_recommendation_count=workflow_recommendation_count,
        runtime_task_run_count=runtime_task_run_count,
        warnings=warnings,
    )


def _pending_improvement_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.lstrip().startswith("- "))


def _yaml_candidate_count(path: Path, key: str = "candidates") -> int:
    if not path.exists():
        return 0
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = payload.get(key, [])
    return len(items) if isinstance(items, list) else 0


def _workflow_recommendation_count(path: Path) -> int:
    if not path.exists():
        return 0
    WorkflowRecommendationReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    return 1


def _candidate_governance_count(path: Path) -> int:
    if not path.exists():
        return 0
    report = CandidateGovernanceLog.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    return len(report.decisions)
