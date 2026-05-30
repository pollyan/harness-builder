from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from harness_builder_agent.schemas.common import Confidence, Gate


class EvidenceFile(BaseModel):
    path: str
    kind: str
    size_bytes: int | None = None
    summary: str | None = None
    truncated: bool = False


class EvidenceBundle(BaseModel):
    schema_version: str = "1.0"
    repo_name: str
    root_path: str
    files: list[EvidenceFile] = Field(default_factory=list)
    key_files: list[EvidenceFile] = Field(default_factory=list)
    config_files: list[EvidenceFile] = Field(default_factory=list)
    ci_files: list[EvidenceFile] = Field(default_factory=list)
    documents: list[EvidenceFile] = Field(default_factory=list)
    source_samples: list[EvidenceFile] = Field(default_factory=list)
    extension_counts: dict[str, int] = Field(default_factory=dict)
    detected_file_count: int = 0
    truncations: list[dict[str, Any]] = Field(default_factory=list)


class LLMCommandCandidate(BaseModel):
    id: str
    command: str
    type: Literal["build", "test", "lint", "typecheck", "other"]
    gate: Gate
    source: str
    confidence: Confidence = "medium"


class LLMScanProposal(BaseModel):
    schema_version: str = "1.0"
    primary_stack: str
    stacks: list[str] = Field(default_factory=list)
    modules: list[dict[str, Any]] = Field(default_factory=list)
    architecture_signals: list[str] = Field(default_factory=list)
    risk_areas: list[dict[str, Any]] = Field(default_factory=list)
    command_candidates: list[LLMCommandCandidate] = Field(default_factory=list)
    configs: list[dict[str, Any]] = Field(default_factory=list)
    ci_files: list[dict[str, Any]] = Field(default_factory=list)
    confidence: Confidence = "medium"
    needs_human_confirmation: bool = True
    reasoning_summary: str


class ScanWarning(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "error"] = "warning"
    evidence: list[str] = Field(default_factory=list)


class ScanMetadata(BaseModel):
    schema_version: str = "1.0"
    llm_status: Literal["succeeded", "failed"] = "succeeded"
    model: str | None = None
    base_url: str | None = None
    prompt_version: str
    evidence_file_count: int
    truncated_files: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[ScanWarning] = Field(default_factory=list)
    reasoning_summary: str | None = None
