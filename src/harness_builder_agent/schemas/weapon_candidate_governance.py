from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from harness_builder_agent.schemas.weapon_library_candidate import MaturityDimension


WeaponCandidateDecision = Literal["accepted", "rejected", "kept"]
WeaponCandidateStatus = Literal["candidate", "confirmed", "rejected"]


class WeaponCandidateGovernanceDecision(BaseModel):
    candidate_id: str
    candidate_type: Literal["guide", "sensor"]
    source_report: Literal[".ai/experience/weapon-library-candidates.yaml"] = ".ai/experience/weapon-library-candidates.yaml"
    decision: WeaponCandidateDecision
    rationale: str
    reviewer: str
    decided_at: str
    previous_status: WeaponCandidateStatus
    new_status: WeaponCandidateStatus
    maturity_dimensions: list[MaturityDimension] = Field(default_factory=list)
    review_boundary: Literal["review_only_no_formal_asset_change"] = "review_only_no_formal_asset_change"


class WeaponCandidateGovernanceLog(BaseModel):
    schema_version: str = "1.0"
    decisions: list[WeaponCandidateGovernanceDecision] = Field(default_factory=list)
