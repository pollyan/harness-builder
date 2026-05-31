from pathlib import Path

import pytest
import yaml

from harness_builder_agent.tools.runtime_task_runs import (
    RuntimeTaskRunError,
    load_runtime_task_run,
    summarize_runtime_task_runs,
)


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_task_run(ai: Path, task_id: str = "task-1", sensor_status: str = "failed") -> Path:
    run = ai / "task-runs" / task_id
    _write_yaml(
        run / "harness-map.yaml",
        {
            "schema_version": "1.0",
            "task_id": task_id,
            "task_type": "bugfix",
            "selected_workflow": "bugfix",
            "risk_level": "medium",
        },
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
                    "status": sensor_status,
                    "exit_code": 1 if sensor_status == "failed" else 0,
                    "duration_seconds": 3.2,
                    "summary": "pytest failed" if sensor_status == "failed" else "pytest passed",
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
            "status": "completed_with_sensor_failures" if sensor_status == "failed" else "completed",
            "sensor_status": sensor_status,
            "repair_attempts": 1,
            "unresolved_sensor_count": 1 if sensor_status == "failed" else 0,
            "risk_count": 1,
            "summary": "Runtime captured sensor outcome.",
        },
    )
    (run / "decision-log.md").write_text("# Decision Log\n\nInvestigated pytest result.\n", encoding="utf-8")
    (run / "handoff-summary.md").write_text("# Handoff Summary\n\nPytest still fails.\n", encoding="utf-8")
    return run


def test_load_runtime_task_run_summarizes_sensor_outcomes(tmp_path: Path):
    ai = tmp_path / ".ai"
    run = _write_task_run(ai)

    summary = load_runtime_task_run(run)

    assert summary.task_id == "task-1"
    assert summary.source_path == ".ai/task-runs/task-1/"
    assert summary.failed_sensor_count == 1
    assert summary.skipped_sensor_count == 0
    assert summary.repair_attempts == 1


def test_summarize_runtime_task_runs_aggregates_valid_runs(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_task_run(ai, "task-1", "failed")
    _write_task_run(ai, "task-2", "passed")

    summary = summarize_runtime_task_runs(ai)

    assert summary.task_run_count == 2
    assert summary.failed_sensor_count == 1
    assert summary.passed_sensor_count == 1
    assert summary.source_paths == [".ai/task-runs/task-1/", ".ai/task-runs/task-2/"]


def test_runtime_task_run_rejects_inconsistent_sensor_status(tmp_path: Path):
    ai = tmp_path / ".ai"
    run = _write_task_run(ai, "task-1", "failed")
    payload = yaml.safe_load((run / "runtime-summary.yaml").read_text(encoding="utf-8"))
    payload["sensor_status"] = "passed"
    _write_yaml(run / "runtime-summary.yaml", payload)

    with pytest.raises(RuntimeTaskRunError, match="sensor_status_mismatch"):
        load_runtime_task_run(run)


def test_runtime_task_run_requires_runtime_summary(tmp_path: Path):
    ai = tmp_path / ".ai"
    run = _write_task_run(ai, "task-1", "passed")
    (run / "runtime-summary.yaml").unlink()

    with pytest.raises(RuntimeTaskRunError, match="missing_runtime_summary"):
        load_runtime_task_run(run)
