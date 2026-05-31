from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class BenchmarkWeakCommand(BaseModel):
    id: str
    source: str | None = None
    confidence: str | None = None
    reason: str | None = None


class BenchmarkCheck(BaseModel):
    id: str
    passed: bool
    path: str | None = None
    expected: Any = None
    actual: Any = None
    error: str | None = None
    errors: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    weak_commands: list[BenchmarkWeakCommand] = Field(default_factory=list)


class QualityScoreItem(BaseModel):
    score: int
    max_score: int = 5
    passed: bool
    reasons: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class QualitySummary(BaseModel):
    total_score: int
    minimum_score: int
    degraded_items: list[str] = Field(default_factory=list)
    failed_items: list[str] = Field(default_factory=list)


class BenchmarkReport(BaseModel):
    schema_version: str = "1.0"
    repo_name: str
    profile: str
    status: Literal["passed", "failed"]
    checks: list[BenchmarkCheck] = Field(default_factory=list)
    quality_status: Literal["passed", "degraded", "failed"] = "failed"
    quality_scores: dict[str, dict[str, QualityScoreItem]] = Field(default_factory=dict)
    quality_summary: QualitySummary | None = None
