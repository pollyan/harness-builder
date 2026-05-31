from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class MaturityCandidateReview(BaseModel):
    candidate_id: str
    decision: Literal["support", "revise", "defer"]
    rationale: str
    risks: list[str] = Field(default_factory=list)
    suggested_acceptance_checks: list[str] = Field(default_factory=list)
    evidence_sources: list[str] = Field(default_factory=list)


class MaturityReviewReport(BaseModel):
    schema_version: str = "1.0"
    summary: str
    reviewer_model: str | None = None
    review_status: Literal["pending_harness_maintainer_review"] = "pending_harness_maintainer_review"
    candidate_reviews: list[MaturityCandidateReview] = Field(default_factory=list)
    missing_candidates: list[str] = Field(default_factory=list)
    global_risks: list[str] = Field(default_factory=list)
