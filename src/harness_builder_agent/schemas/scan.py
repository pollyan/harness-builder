from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from harness_builder_agent.schemas.common import Confidence, Gate

PrimaryStack = Literal["java-spring", "dotnet-aspnet", "node", "unknown"]
EvidencePriority = Literal["critical", "high", "medium", "low"]


class EvidenceBucketCoverage(BaseModel):
    bucket: str
    total_count: int
    selected_count: int
    skipped_count: int
    selected_paths: list[str] = Field(default_factory=list)


class EvidenceCoverage(BaseModel):
    schema_version: str = "1.0"
    detected_file_count: int
    selected_evidence_count: int
    bucket_coverage: list[EvidenceBucketCoverage] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)


class EvidenceFile(BaseModel):
    path: str
    kind: str
    size_bytes: int | None = None
    summary: str | None = None
    truncated: bool = False
    priority: EvidencePriority = "medium"
    reason: str | None = None
    bucket: str | None = None


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
    priority_files: list[EvidenceFile] = Field(default_factory=list)
    test_files: list[EvidenceFile] = Field(default_factory=list)
    api_entrypoints: list[EvidenceFile] = Field(default_factory=list)
    risk_files: list[EvidenceFile] = Field(default_factory=list)
    llm_requested_files: list[EvidenceFile] = Field(default_factory=list)
    coverage: EvidenceCoverage | None = None
    extension_counts: dict[str, int] = Field(default_factory=dict)
    detected_file_count: int = 0
    truncations: list[dict[str, Any]] = Field(default_factory=list)


class LLMEvidencePlan(BaseModel):
    schema_version: str = "1.0"
    requested_paths: list[str] = Field(default_factory=list, max_length=8)
    risk_focus: list[str] = Field(default_factory=list, max_length=8)
    rationale: str
    confidence: Confidence = "medium"


class LLMCommandCandidate(BaseModel):
    id: str
    command: str
    type: Literal["build", "test", "lint", "typecheck", "other"]
    gate: Gate
    source: str
    confidence: Confidence = "medium"


class LLMScanProposal(BaseModel):
    schema_version: str = "1.0"
    primary_stack: PrimaryStack
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
    coverage: dict[str, Any] | None = None
    reasoning_summary: str | None = None
