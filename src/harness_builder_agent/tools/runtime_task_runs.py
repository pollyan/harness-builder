from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.harness_map import HarnessMap
from harness_builder_agent.schemas.runtime_task_run import (
    RuntimeSummary,
    RuntimeTaskRunCollectionSummary,
    RuntimeTaskRunSummary,
)
from harness_builder_agent.schemas.sensor_report import SensorReport


class RuntimeTaskRunError(ValueError):
    pass


def iter_runtime_task_runs(ai: Path) -> list[Path]:
    task_runs = ai / "task-runs"
    if not task_runs.exists():
        return []
    return sorted(path for path in task_runs.iterdir() if path.is_dir())


def summarize_runtime_task_runs(ai: Path) -> RuntimeTaskRunCollectionSummary:
    task_runs = [load_runtime_task_run(path) for path in iter_runtime_task_runs(ai)]
    return RuntimeTaskRunCollectionSummary(
        task_run_count=len(task_runs),
        passed_sensor_count=sum(item.passed_sensor_count for item in task_runs),
        failed_sensor_count=sum(item.failed_sensor_count for item in task_runs),
        skipped_sensor_count=sum(item.skipped_sensor_count for item in task_runs),
        unresolved_sensor_count=sum(item.unresolved_sensor_count for item in task_runs),
        repair_attempt_count=sum(item.repair_attempts for item in task_runs),
        risk_count=sum(item.risk_count for item in task_runs),
        source_paths=[item.source_path for item in task_runs],
        task_runs=task_runs,
    )


def load_runtime_task_run(run_dir: Path) -> RuntimeTaskRunSummary:
    harness_map_path = run_dir / "harness-map.yaml"
    sensor_report_path = run_dir / "sensor-report.yaml"
    runtime_summary_path = run_dir / "runtime-summary.yaml"
    decision_log_path = run_dir / "decision-log.md"
    handoff_summary_path = run_dir / "handoff-summary.md"

    harness_map = HarnessMap.model_validate(_read_yaml(harness_map_path, "missing_harness_map"))
    sensor_report = SensorReport.model_validate(_read_yaml(sensor_report_path, "missing_sensor_report"))
    runtime_summary = RuntimeSummary.model_validate(_read_yaml(runtime_summary_path, "missing_runtime_summary"))
    _require_non_empty_markdown(decision_log_path, "missing_decision_log")
    _require_non_empty_markdown(handoff_summary_path, "missing_handoff_summary")

    task_id = run_dir.name
    task_ids = {task_id, harness_map.task_id, sensor_report.task_id, runtime_summary.task_id}
    if len(task_ids) != 1:
        raise RuntimeTaskRunError("task_id_mismatch")
    if runtime_summary.selected_workflow != harness_map.selected_workflow:
        raise RuntimeTaskRunError("selected_workflow_mismatch")

    passed = sum(1 for result in sensor_report.sensor_results if result.status == "passed")
    failed = sum(1 for result in sensor_report.sensor_results if result.status == "failed")
    skipped = sum(1 for result in sensor_report.sensor_results if result.status == "skipped")
    unresolved = failed + skipped
    derived_status = _sensor_status(passed=passed, failed=failed, skipped=skipped)
    if runtime_summary.sensor_status != derived_status:
        raise RuntimeTaskRunError("sensor_status_mismatch")
    if runtime_summary.unresolved_sensor_count != unresolved:
        raise RuntimeTaskRunError("unresolved_sensor_count_mismatch")
    if any(result.status in {"failed", "skipped"} and not result.summary.strip() for result in sensor_report.sensor_results):
        raise RuntimeTaskRunError("unresolved_sensor_missing_summary")

    return RuntimeTaskRunSummary(
        task_id=task_id,
        source_path=f".ai/task-runs/{task_id}/",
        selected_workflow=harness_map.selected_workflow,
        sensor_status=derived_status,
        passed_sensor_count=passed,
        failed_sensor_count=failed,
        skipped_sensor_count=skipped,
        unresolved_sensor_count=unresolved,
        repair_attempts=runtime_summary.repair_attempts,
        risk_count=runtime_summary.risk_count,
        decision_log_path=f".ai/task-runs/{task_id}/decision-log.md",
        handoff_summary_path=f".ai/task-runs/{task_id}/handoff-summary.md",
        sensor_summaries=[f"{result.id}: {result.status} - {result.summary}" for result in sensor_report.sensor_results],
    )


def render_runtime_task_run_source(run_dir: Path) -> str:
    summary = load_runtime_task_run(run_dir)
    handoff = (run_dir / "handoff-summary.md").read_text(encoding="utf-8").strip()
    decision = (run_dir / "decision-log.md").read_text(encoding="utf-8").strip()
    sensors = "\n".join(f"- {item}" for item in summary.sensor_summaries) or "- no sensor results"
    return (
        f"task_id: {summary.task_id}\n"
        f"source: {summary.source_path}\n"
        f"selected_workflow: {summary.selected_workflow}\n"
        f"sensor_status: sensor {summary.sensor_status}\n"
        f"failed_sensor_count: {summary.failed_sensor_count}\n"
        f"skipped_sensor_count: {summary.skipped_sensor_count}\n"
        f"repair_attempts: {summary.repair_attempts}\n"
        f"risk_count: {summary.risk_count}\n"
        "sensor_results:\n"
        f"{sensors}\n\n"
        "handoff_summary:\n"
        f"{handoff[:4000]}\n\n"
        "decision_log:\n"
        f"{decision[:4000]}\n"
    )


def _read_yaml(path: Path, missing_code: str) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeTaskRunError(missing_code)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeTaskRunError(f"invalid_yaml:{path.name}")
    return payload


def _require_non_empty_markdown(path: Path, missing_code: str) -> None:
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        raise RuntimeTaskRunError(missing_code)


def _sensor_status(*, passed: int, failed: int, skipped: int) -> str:
    if failed:
        return "failed"
    if skipped:
        return "skipped"
    if passed:
        return "passed"
    return "unresolved"
