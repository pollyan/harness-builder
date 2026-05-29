from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SensorResult(BaseModel):
    id: str
    command: str | None = None
    status: Literal["passed", "failed", "skipped"]
    exit_code: int | None = None
    duration_seconds: float
    summary: str
    stdout_tail: str = ""
    stderr_tail: str = ""


class SensorReport(BaseModel):
    schema_version: str = "1.0"
    task_id: str
    task: str
    sensor_results: list[SensorResult] = Field(default_factory=list)
