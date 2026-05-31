from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SelfImproveGeneratedArtifact(BaseModel):
    path: str
    kind: str


class SelfImproveCandidateCounts(BaseModel):
    improvement_candidates: int = 0
    maturity_reviews: int = 0
    asset_candidates: int = 0
    guide_candidates: int = 0
    sensor_candidates: int = 0
    workflow_policy_candidates: int = 0


class SelfImproveMaturitySnapshot(BaseModel):
    overall_level: str
    target_next_level: str | None = None
    dimension_scores: dict[str, str] = Field(default_factory=dict)


class SelfImprovePackageManifest(BaseModel):
    schema_version: str = "1.0"
    package_id: str
    review_status: Literal["pending_harness_maintainer_review"] = "pending_harness_maintainer_review"
    generated_artifacts: list[SelfImproveGeneratedArtifact] = Field(default_factory=list)
    candidate_counts: SelfImproveCandidateCounts = Field(default_factory=SelfImproveCandidateCounts)
    maturity: SelfImproveMaturitySnapshot
    next_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
