from pathlib import Path

import yaml

from harness_builder_agent.tools.experience_index import build_experience_index


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_build_experience_index_counts_workflow_recommendation_review(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_yaml(
        ai / "review" / "workflow-routing-recommendation.yaml",
        {
            "schema_version": "1.0",
            "task_id": "task-1",
            "task_brief": "Fix a regression.",
            "recommended_workflow": "bugfix",
            "matched_rule_ids": ["bugfix-intent"],
            "risk_level": "medium",
            "confidence": "high",
            "rationale": "Bugfix task.",
            "required_guides": [".ai/guides/project-context.md"],
            "required_sensors": [".ai/sensors/verification.md"],
            "human_confirmation_required": False,
            "review_status": "pending_harness_maintainer_review",
            "evidence_sources": [".ai/harness-config.yaml"],
        },
    )

    index = build_experience_index(ai)

    assert index.workflow_recommendation_count == 1
    source = next(item for item in index.sources if item.kind == "workflow_recommendation")
    assert source.path == ".ai/review/workflow-routing-recommendation.yaml"
    assert source.item_count == 1
