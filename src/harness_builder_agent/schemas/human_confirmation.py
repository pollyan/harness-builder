from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from harness_builder_agent.schemas.common import Confidence


class ContextInput(BaseModel):
    path: str
    size_bytes: int = Field(ge=0)
    summary: str
    truncated: bool


class ContextInputs(BaseModel):
    schema_version: str = "1.0"
    contexts: list[ContextInput] = Field(default_factory=list)


class QuestionnaireQuestion(BaseModel):
    interaction_type: Literal[
        "context_confirmation",
        "candidate_asset_confirmation",
        "sensor_gate_confirmation",
        "risk_area_confirmation",
        "scan_warning_confirmation",
        "evidence_expansion_confirmation",
        "scan_followup_confirmation",
    ]
    interaction_id: str
    question: str
    options: list[str] = Field(min_length=1)
    confidence: Confidence
    reason: str
    response_status: Literal[
        "unaddressed",
        "partially_addressed_by_current_scan_supplement",
        "reviewed_resolved_by_harness_maintainer",
    ] = "unaddressed"
    response_sources: list[str] = Field(default_factory=list)


class Questionnaire(BaseModel):
    schema_version: str = "1.0"
    questions: list[QuestionnaireQuestion] = Field(min_length=1)
