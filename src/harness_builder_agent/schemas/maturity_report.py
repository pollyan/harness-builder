from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from harness_builder_agent.schemas.common import Confidence

MaturityLevel = Literal["L0", "L1", "L2", "L3", "L4"]


class MaturityEvidence(BaseModel):
    source: str
    summary: str


class MaturityBlocker(BaseModel):
    id: str
    reason: str
    prevents_level: MaturityLevel | None = None


class MaturityNextStep(BaseModel):
    id: str
    target_dimension: str
    action: str
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    expected_lift: str | None = None


class MaturityDimensionReport(BaseModel):
    level: MaturityLevel
    evidence: list[MaturityEvidence] = Field(default_factory=list)
    blockers: list[MaturityBlocker] = Field(default_factory=list)
    next_level_requirements: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"


class MaturityBlockingCap(BaseModel):
    id: str
    reason: str
    max_level: MaturityLevel
    active: bool = True
    evidence: list[str] = Field(default_factory=list)


class MaturityReport(BaseModel):
    schema_version: str = "1.0"
    overall_level: MaturityLevel = "L1"
    target_next_level: MaturityLevel | None = None
    dimension_scores: dict[str, MaturityLevel] = Field(default_factory=dict)
    dimensions: dict[str, MaturityDimensionReport] = Field(default_factory=dict)
    blocking_caps: list[MaturityBlockingCap] = Field(default_factory=list)
    next_steps: list[MaturityNextStep] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    last_assessed_at: str | None = None
