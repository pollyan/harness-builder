from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

HumanInputDecision = Literal["resolved", "reopened"]
HumanInputResponseStatus = Literal[
    "unaddressed",
    "partially_addressed_by_current_scan_supplement",
    "reviewed_resolved_by_harness_maintainer",
]


class HumanInputGovernanceDecision(BaseModel):
    interaction_id: str
    interaction_type: Literal["scan_followup_confirmation"]
    source_report: str = ".ai/questionnaire.yaml"
    decision: HumanInputDecision
    previous_response_status: HumanInputResponseStatus
    new_response_status: HumanInputResponseStatus
    rationale: str
    reviewer: str = "harness-maintainer"
    decided_at: str
    response_sources: list[str] = Field(default_factory=list)


class HumanInputGovernanceLog(BaseModel):
    schema_version: str = "1.0"
    decisions: list[HumanInputGovernanceDecision] = Field(default_factory=list)
