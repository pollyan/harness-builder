from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AssetCandidateDraft(BaseModel):
    id: str
    kind: Literal["guide", "sensor", "workflow_policy"]
    source_candidate_id: str | None = None
    source_review_decision: Literal["support", "revise", "defer", "missing"]
    suggested_path: str
    title: str
    rationale: str
    draft_content: str
    evidence_sources: list[str] = Field(default_factory=list)
    acceptance_checks: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high"] = "medium"
    review_status: Literal["pending_harness_maintainer_review"] = "pending_harness_maintainer_review"


class AssetCandidateReport(BaseModel):
    schema_version: str = "1.0"
    source: str = "llm_maturity_review"
    candidates: list[AssetCandidateDraft] = Field(default_factory=list)
