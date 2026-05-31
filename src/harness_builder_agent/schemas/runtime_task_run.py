from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RuntimeSummary(BaseModel):
    schema_version: str = "1.0"
    task_id: str
    selected_workflow: Literal["bugfix", "lightweight", "standard"]
    status: str
    sensor_status: Literal["passed", "failed", "skipped", "degraded", "unresolved"]
    repair_attempts: int = 0
    unresolved_sensor_count: int = 0
    risk_count: int = 0
    summary: str = ""


class RuntimeTaskRunSummary(BaseModel):
    task_id: str
    source_path: str
    selected_workflow: Literal["bugfix", "lightweight", "standard"]
    sensor_status: Literal["passed", "failed", "skipped", "unresolved"]
    passed_sensor_count: int = 0
    failed_sensor_count: int = 0
    skipped_sensor_count: int = 0
    unresolved_sensor_count: int = 0
    repair_attempts: int = 0
    risk_count: int = 0
    decision_log_path: str
    handoff_summary_path: str
    sensor_summaries: list[str] = Field(default_factory=list)


class RuntimeTaskRunCollectionSummary(BaseModel):
    task_run_count: int = 0
    passed_sensor_count: int = 0
    failed_sensor_count: int = 0
    skipped_sensor_count: int = 0
    unresolved_sensor_count: int = 0
    repair_attempt_count: int = 0
    risk_count: int = 0
    source_paths: list[str] = Field(default_factory=list)
    task_runs: list[RuntimeTaskRunSummary] = Field(default_factory=list)
