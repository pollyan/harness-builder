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
    ]
    interaction_id: str
    question: str
    options: list[str] = Field(min_length=1)
    confidence: Confidence
    reason: str


class Questionnaire(BaseModel):
    schema_version: str = "1.0"
    questions: list[QuestionnaireQuestion] = Field(min_length=1)
