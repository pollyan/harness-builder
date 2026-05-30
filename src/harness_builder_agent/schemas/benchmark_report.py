from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class BenchmarkCheck(BaseModel):
    id: str
    passed: bool
    path: str | None = None
    expected: Any = None
    actual: Any = None
    error: str | None = None


class BenchmarkReport(BaseModel):
    schema_version: str = "1.0"
    repo_name: str
    profile: str
    status: Literal["passed", "failed"]
    checks: list[BenchmarkCheck] = Field(default_factory=list)
