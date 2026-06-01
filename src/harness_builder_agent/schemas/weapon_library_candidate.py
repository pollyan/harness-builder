from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


MaturityDimension = Literal["guides", "risk_control", "sensors", "verification_sophistication"]


class WeaponLibraryCandidate(BaseModel):
    id: str
    candidate_type: Literal["guide", "sensor"]
    status: Literal["candidate", "confirmed", "rejected"]
    title: str
    rationale: str
    evidence: list[str] = Field(min_length=1)
    source: Literal["llm_scan_proposal"] = "llm_scan_proposal"
    human_confirmation_required: bool
    decision_notes: str | None = None
    maturity_dimensions: list[MaturityDimension] = Field(default_factory=list)
    maturity_impact_summary: str = ""
    next_stage_contribution: str = ""
    review_boundary: Literal["review_only_no_formal_asset_change"] = "review_only_no_formal_asset_change"


class WeaponLibraryCandidateReport(BaseModel):
    schema_version: str = "1.0"
    source: Literal["llm_scan_proposal"] = "llm_scan_proposal"
    candidates: list[WeaponLibraryCandidate] = Field(min_length=1)
