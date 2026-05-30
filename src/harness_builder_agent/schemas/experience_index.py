from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ExperienceSource(BaseModel):
    path: str
    kind: Literal[
        "pending_improvements",
        "maturity_review",
        "asset_candidates",
        "workflow_recommendation",
        "runtime_task_runs",
        "manual_experience",
    ]
    item_count: int = 0


class ExperienceIndex(BaseModel):
    schema_version: str = "1.0"
    experience_files: dict[str, bool] = Field(default_factory=dict)
    sources: list[ExperienceSource] = Field(default_factory=list)
    pending_improvement_count: int = 0
    asset_candidate_count: int = 0
    maturity_review_count: int = 0
    workflow_recommendation_count: int = 0
    runtime_task_run_count: int = 0
    warnings: list[str] = Field(default_factory=list)
