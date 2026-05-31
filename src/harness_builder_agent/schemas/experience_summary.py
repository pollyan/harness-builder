from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ExperienceFinding(BaseModel):
    id: str
    kind: Literal["repair_pattern", "sensor_feedback", "team_preference", "workflow_gap", "risk_signal", "improvement_signal"]
    title: str
    summary: str
    evidence_sources: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    suggested_follow_up: str | None = None


class ExperienceSummaryReport(BaseModel):
    schema_version: str = "1.0"
    source: str = "llm_experience_summary"
    review_status: Literal["pending_harness_maintainer_review"] = "pending_harness_maintainer_review"
    summary: str
    findings: list[ExperienceFinding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
