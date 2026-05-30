from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

InteractionMode = Literal["interactive", "non_interactive"]
ScanConfirmationStatus = Literal["accepted", "amended", "needs_review", "not_confirmed"]
ContextConfirmationStatus = Literal["confirmed", "partially_confirmed", "not_provided", "not_confirmed"]
CandidateDecisionStatus = Literal["accepted", "rejected", "kept"]
FinalConfirmationStatus = Literal["confirmed", "cancelled", "not_confirmed"]


class RepoConfirmation(BaseModel):
    path: str
    confirmed: bool = False


class ScanConfirmation(BaseModel):
    status: ScanConfirmationStatus = "not_confirmed"
    primary_stack_override: str | None = None
    notes: list[str] = Field(default_factory=list)


class ContextConfirmation(BaseModel):
    status: ContextConfirmationStatus = "not_provided"
    confirmed_paths: list[str] = Field(default_factory=list)
    rejected_paths: list[str] = Field(default_factory=list)
    inline_contexts: list[str] = Field(default_factory=list)


class CandidateDecision(BaseModel):
    candidate_id: str
    decision: CandidateDecisionStatus = "kept"
    notes: str = ""


class FinalConfirmation(BaseModel):
    status: FinalConfirmationStatus = "not_confirmed"


class InteractionDecisions(BaseModel):
    schema_version: str = "1.0"
    mode: InteractionMode
    repo: RepoConfirmation
    scan_confirmation: ScanConfirmation = Field(default_factory=ScanConfirmation)
    context_confirmation: ContextConfirmation = Field(default_factory=ContextConfirmation)
    candidate_decisions: list[CandidateDecision] = Field(default_factory=list)
    final_confirmation: FinalConfirmation = Field(default_factory=FinalConfirmation)
