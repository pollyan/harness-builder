from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CandidateGovernanceDecision(BaseModel):
    candidate_id: str
    candidate_kind: Literal["guide", "sensor", "workflow_policy"]
    source_report: str = ".ai/review/asset-candidates.yaml"
    source_candidate_id: str | None = None
    suggested_path: str
    decision: Literal["accepted", "deferred", "rejected", "applied"]
    rationale: str
    reviewer: str = "harness-maintainer"
    decided_at: str
    applied_paths: list[str] = Field(default_factory=list)
    acceptance_checks: list[str] = Field(default_factory=list)
    evidence_sources: list[str] = Field(default_factory=list)


class CandidateGovernanceLog(BaseModel):
    schema_version: str = "1.0"
    decisions: list[CandidateGovernanceDecision] = Field(default_factory=list)
