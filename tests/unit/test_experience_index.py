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


def test_build_experience_index_counts_workflow_recommendation_history(tmp_path: Path):
    ai = tmp_path / ".ai"
    history_dir = ai / "review" / "workflow-routing-recommendations"
    _write_yaml(
        history_dir / "task-1.yaml",
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
    _write_yaml(
        history_dir / "task-2.yaml",
        {
            "schema_version": "1.0",
            "task_id": "task-2",
            "task_brief": "Change a risky policy.",
            "recommended_workflow": "standard",
            "matched_rule_ids": ["standard-escalation"],
            "risk_level": "high",
            "confidence": "medium",
            "rationale": "Risky policy change.",
            "required_guides": [".ai/guides/architecture.md"],
            "required_sensors": [".ai/sensors/verification.md"],
            "human_confirmation_required": True,
            "review_status": "pending_harness_maintainer_review",
            "evidence_sources": [".ai/harness-config.yaml"],
        },
    )
    _write_yaml(
        history_dir / "index.yaml",
        {
            "schema_version": "1.0",
            "latest_recommendation_id": "task-2",
            "recommendations": [
                {
                    "recommendation_id": "task-1",
                    "task_id": "task-1",
                    "created_at": "2026-05-31T11:59:00Z",
                    "yaml_path": ".ai/review/workflow-routing-recommendations/task-1.yaml",
                    "markdown_path": ".ai/review/workflow-routing-recommendations/task-1.md",
                    "recommended_workflow": "bugfix",
                    "risk_level": "medium",
                    "confidence": "high",
                    "review_status": "pending_harness_maintainer_review",
                },
                {
                    "recommendation_id": "task-2",
                    "task_id": "task-2",
                    "created_at": "2026-05-31T12:00:00Z",
                    "yaml_path": ".ai/review/workflow-routing-recommendations/task-2.yaml",
                    "markdown_path": ".ai/review/workflow-routing-recommendations/task-2.md",
                    "recommended_workflow": "standard",
                    "risk_level": "high",
                    "confidence": "medium",
                    "review_status": "pending_harness_maintainer_review",
                },
            ],
        },
    )

    index = build_experience_index(ai)

    assert index.workflow_recommendation_count == 2
    source = next(item for item in index.sources if item.kind == "workflow_recommendation")
    assert source.path == ".ai/review/workflow-routing-recommendations/index.yaml"
    assert source.item_count == 2


def test_build_experience_index_counts_candidate_governance_decisions(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_yaml(
        ai / "review" / "candidate-governance.yaml",
        {
            "schema_version": "1.0",
            "decisions": [
                {
                    "candidate_id": "guide-project-context-scope",
                    "candidate_kind": "guide",
                    "source_report": ".ai/review/asset-candidates.yaml",
                    "suggested_path": ".ai/guides/project-context.md",
                    "decision": "applied",
                    "rationale": "Maintainer accepted the candidate.",
                    "reviewer": "harness-maintainer",
                    "decided_at": "2026-05-31T00:00:00Z",
                    "applied_paths": [".ai/guides/project-context.md"],
                }
            ],
        },
    )

    index = build_experience_index(ai)

    assert index.candidate_governance_decision_count == 1
    source = next(item for item in index.sources if item.kind == "candidate_governance")
    assert source.path == ".ai/review/candidate-governance.yaml"
    assert source.item_count == 1
