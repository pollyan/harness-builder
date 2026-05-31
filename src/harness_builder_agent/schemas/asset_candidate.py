from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from harness_builder_agent.schemas.workflow_policy_patch import WorkflowPolicyPatch


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
    workflow_policy_patch: WorkflowPolicyPatch | None = None

    @model_validator(mode="after")
    def validate_kind_specific_payload(self) -> "AssetCandidateDraft":
        if self.kind == "workflow_policy" and self.workflow_policy_patch is None:
            raise ValueError("workflow_policy_patch is required for workflow_policy candidates")
        if self.kind != "workflow_policy" and self.workflow_policy_patch is not None:
            raise ValueError("workflow_policy_patch is only valid for workflow_policy candidates")
        return self


class AssetCandidateReport(BaseModel):
    schema_version: str = "1.0"
    source: str = "llm_maturity_review"
    candidates: list[AssetCandidateDraft] = Field(default_factory=list)
