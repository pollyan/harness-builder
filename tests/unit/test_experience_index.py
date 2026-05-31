from pathlib import Path

import yaml

from harness_builder_agent.tools.experience_index import build_experience_index


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_runtime_task_run(ai: Path, task_id: str = "task-1") -> None:
    run = ai / "task-runs" / task_id
    _write_yaml(
        run / "harness-map.yaml",
        {"schema_version": "1.0", "task_id": task_id, "task_type": "bugfix", "selected_workflow": "bugfix"},
    )
    _write_yaml(
        run / "sensor-report.yaml",
        {
            "schema_version": "1.0",
            "task_id": task_id,
            "task": "Fix checkout bug",
            "sensor_results": [
                {
                    "id": "pytest",
                    "command": "pytest",
                    "status": "passed",
                    "exit_code": 0,
                    "duration_seconds": 1.0,
                    "summary": "pytest passed",
                }
            ],
        },
    )
    _write_yaml(
        run / "runtime-summary.yaml",
        {
            "schema_version": "1.0",
            "task_id": task_id,
            "selected_workflow": "bugfix",
            "status": "completed",
            "sensor_status": "passed",
            "repair_attempts": 0,
            "unresolved_sensor_count": 0,
            "risk_count": 0,
            "summary": "Runtime completed.",
        },
    )
    (run / "decision-log.md").write_text("# Decision Log\n\nNo special decision.\n", encoding="utf-8")
    (run / "handoff-summary.md").write_text("# Handoff Summary\n\nReady for review.\n", encoding="utf-8")


def test_build_experience_index_records_valid_runtime_task_runs(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_runtime_task_run(ai, "task-1")

    index = build_experience_index(ai)

    assert index.runtime_task_run_count == 1
    source = next(item for item in index.sources if item.kind == "runtime_task_runs")
    assert source.path == ".ai/task-runs/"
    assert source.item_count == 1
    assert not any("runtime task-runs absent" in warning for warning in index.warnings)


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
