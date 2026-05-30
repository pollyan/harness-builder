from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools.assess_maturity import assess_maturity
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
    return ai


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_markdown(path: Path, recommendation: WorkflowRecommendationReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    matched_rules = "\n".join(f"- `{rule_id}`" for rule_id in recommendation.matched_rule_ids) or "- None."
    guides = "\n".join(f"- `{guide}`" for guide in recommendation.required_guides) or "- None."
    sensors = "\n".join(f"- `{sensor}`" for sensor in recommendation.required_sensors) or "- None."
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
        "## Task Brief\n\n"
        f"{recommendation.task_brief}\n\n"
        "## Rationale\n\n"
        f"{recommendation.rationale}\n\n"
        "## Matched Routing Rules\n\n"
        f"{matched_rules}\n\n"
        "## Required Guides\n\n"
        f"{guides}\n\n"
        "## Required Sensors\n\n"
        f"{sensors}\n\n"
        "## Evidence Sources\n\n"
        f"{evidence}\n\n"
        "## Boundary\n\n"
        "This is a review-only workflow recommendation. Harness Builder does not execute the workflow or create `.ai/task-runs`.\n",
        encoding="utf-8",
    )
