from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.schemas.workflow_recommendation_history import (
    HISTORY_RECOMMENDATION_DIR,
    WorkflowRecommendationHistory,
    WorkflowRecommendationHistoryEntry,
)
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.experience_index import write_experience_index
from harness_builder_agent.tools.llm_workflow_router import recommend_workflow_with_llm


def recommend_workflow(repo: Path, *, task_brief: str, task_id: str) -> Path:
    root = repo.resolve()
    ai = root / ".ai"
    if not (ai / "maturity-evidence.yaml").exists():
        assess_maturity(root)
    config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
    evidence_pack = MaturityEvidencePack.model_validate(yaml.safe_load((ai / "maturity-evidence.yaml").read_text(encoding="utf-8")))
    recommendation = recommend_workflow_with_llm(
        task_id=task_id,
        task_brief=task_brief,
        config=config,
        evidence_pack=evidence_pack,
    )
    review_dir = ai / "review"
    _write_yaml(review_dir / "workflow-routing-recommendation.yaml", recommendation.model_dump(mode="json"))
    _write_markdown(review_dir / "workflow-routing-recommendation.md", recommendation)
    _write_history(review_dir, recommendation)
    write_experience_index(ai)
    assess_maturity(root)
    return ai


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_markdown(path: Path, recommendation: WorkflowRecommendationReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    matched_rules = "\n".join(f"- `{rule_id}`" for rule_id in recommendation.matched_rule_ids) or "- None."
    guides = "\n".join(f"- `{guide}`" for guide in recommendation.required_guides) or "- None."
    sensors = "\n".join(f"- `{sensor}`" for sensor in recommendation.required_sensors) or "- None."
    assets = "\n".join(
        [
            "Guides:",
            guides,
            "",
            "Sensors:",
            sensors,
        ]
    )
    evidence = "\n".join(f"- `{source}`" for source in recommendation.evidence_sources) or "- None."
    path.write_text(
        "# Workflow Routing Recommendation\n\n"
        "## Summary\n\n"
        f"- task id: `{recommendation.task_id}`\n"
        f"- recommended workflow: `{recommendation.recommended_workflow}`\n"
        f"- risk level: `{recommendation.risk_level}`\n"
        f"- confidence: `{recommendation.confidence}`\n"
        f"- human confirmation required: `{recommendation.human_confirmation_required}`\n"
        f"- review status: `{recommendation.review_status}`\n\n"
        "## Task\n\n"
        f"{recommendation.task_brief}\n\n"
        "## Recommended Workflow\n\n"
        f"`{recommendation.recommended_workflow}`\n\n"
        "## Rationale\n\n"
        f"{recommendation.rationale}\n\n"
        "## Matched Routing Rules\n\n"
        f"{matched_rules}\n\n"
        "## Required Harness Assets\n\n"
        f"{assets}\n\n"
        "## Evidence Sources\n\n"
        f"{evidence}\n\n"
        "## Review Boundary\n\n"
        "This is a review-only workflow recommendation. Harness Builder does not execute the workflow or create `.ai/task-runs`.\n",
        encoding="utf-8",
    )


def _write_history(review_dir: Path, recommendation: WorkflowRecommendationReport) -> WorkflowRecommendationHistory:
    now = datetime.now(UTC)
    created_at = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    recommendation_id = f"{_safe_slug(recommendation.task_id)}-{now.strftime('%Y%m%dT%H%M%S%fZ')}"
    history_dir = review_dir / "workflow-routing-recommendations"
    history_yaml = history_dir / f"{recommendation_id}.yaml"
    history_markdown = history_dir / f"{recommendation_id}.md"
    _write_yaml(history_yaml, recommendation.model_dump(mode="json"))
    _write_markdown(history_markdown, recommendation)

    history = _load_history(history_dir / "index.yaml")
    entry = WorkflowRecommendationHistoryEntry(
        recommendation_id=recommendation_id,
        task_id=recommendation.task_id,
        created_at=created_at,
        yaml_path=f"{HISTORY_RECOMMENDATION_DIR}/{recommendation_id}.yaml",
        markdown_path=f"{HISTORY_RECOMMENDATION_DIR}/{recommendation_id}.md",
        recommended_workflow=recommendation.recommended_workflow,
        risk_level=recommendation.risk_level,
        confidence=recommendation.confidence,
        review_status=recommendation.review_status,
    )
    history = WorkflowRecommendationHistory(
        latest_recommendation_id=recommendation_id,
        recommendations=[*history.recommendations, entry],
    )
    _write_yaml(history_dir / "index.yaml", history.model_dump(mode="json"))
    _write_history_summary(review_dir / "workflow-routing-recommendations.md", history)
    return history


def _load_history(path: Path) -> WorkflowRecommendationHistory:
    if not path.exists():
        return WorkflowRecommendationHistory()
    return WorkflowRecommendationHistory.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def _write_history_summary(path: Path, history: WorkflowRecommendationHistory) -> None:
    latest = next(
        (item for item in history.recommendations if item.recommendation_id == history.latest_recommendation_id),
        None,
    )
    recommendations = "\n".join(
        f"- `{item.recommendation_id}`: task `{item.task_id}`, workflow `{item.recommended_workflow}`, "
        f"risk `{item.risk_level}`, status `{item.review_status}`"
        for item in history.recommendations
    )
    latest_section = (
        f"- recommendation id: `{latest.recommendation_id}`\n"
        f"- task id: `{latest.task_id}`\n"
        f"- recommended workflow: `{latest.recommended_workflow}`\n"
        f"- YAML: `{latest.yaml_path}`\n"
        f"- Markdown: `{latest.markdown_path}`"
        if latest
        else "- None."
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Workflow Routing Recommendation History\n\n"
        "## Latest Recommendation\n\n"
        f"{latest_section}\n\n"
        "## Recommendations\n\n"
        f"{recommendations or '- None.'}\n\n"
        "## Review Boundary\n\n"
        "This history is review-only. Harness Builder does not execute workflows, apply routing policy changes, "
        "or create `.ai/task-runs`. Each entry remains `pending_harness_maintainer_review` until a maintainer "
        "reviews the related Harness change.\n",
        encoding="utf-8",
    )


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "manual-task"
