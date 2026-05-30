from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from harness_builder_agent.schemas.common import Confidence


class ImprovementCandidate(BaseModel):
    id: str
    candidate_type: Literal["guide_update", "sensor_update", "workflow_policy_update", "maturity_action"]
    suggested_target: str
    rationale: str
    evidence: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"
    human_confirmation_required: bool = True
    priority: Literal["high", "medium", "low"] = "medium"


class ImprovementCandidateReport(BaseModel):
    schema_version: str = "1.0"
    candidates: list[ImprovementCandidate] = Field(default_factory=list)
