from __future__ import annotations

from pydantic import BaseModel, Field


class MaturityReport(BaseModel):
    schema_version: str = "1.0"
    overall_level: str = "L1"
    dimension_scores: dict[str, str] = Field(default_factory=dict)
    blocking_reasons: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
