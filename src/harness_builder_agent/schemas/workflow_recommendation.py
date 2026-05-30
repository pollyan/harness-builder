from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from harness_builder_agent.schemas.common import Confidence


class WorkflowRecommendationReport(BaseModel):
    schema_version: str = "1.0"
    task_id: str
    task_brief: str
    recommended_workflow: str
    matched_rule_ids: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "medium"
    confidence: Confidence = "medium"
    rationale: str
    required_guides: list[str] = Field(default_factory=list)
    required_sensors: list[str] = Field(default_factory=list)
    human_confirmation_required: bool = False
    review_status: Literal["pending_harness_maintainer_review"] = "pending_harness_maintainer_review"
    evidence_sources: list[str] = Field(default_factory=list)
