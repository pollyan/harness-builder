from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InventoryEvidenceSummary(BaseModel):
    module_count: int = 0
    evidence_count: int = 0
    risk_area_count: int = 0


class CommandEvidenceSummary(BaseModel):
    total_count: int = 0
    hard_gate_count: int = 0
    soft_gate_count: int = 0
    command_ids: list[str] = Field(default_factory=list)


class HarnessAssetEvidence(BaseModel):
    guide_count: int = 0
    sensor_count: int = 0
    workflow_skill_count: int = 0
    has_harness_config: bool = False
    has_weapon_library_selection: bool = False


class ObservabilityEvidence(BaseModel):
    generation_run_count: int = 0
    has_runtime_task_runs: bool = False
    latest_generation_status: str | None = None


class ExperienceEvidence(BaseModel):
    has_pending_improvements: bool = False
    pending_improvement_count: int = 0


class BenchmarkEvidence(BaseModel):
    has_report: bool = False
    status: Literal["passed", "failed", "missing", "unknown"] = "unknown"


class MaturityEvidencePack(BaseModel):
    schema_version: str = "1.0"
    repo_name: str
    primary_stack: str
    generated_at: str | None = None
    inventory_summary: InventoryEvidenceSummary = Field(default_factory=InventoryEvidenceSummary)
    command_summary: CommandEvidenceSummary = Field(default_factory=CommandEvidenceSummary)
    harness_assets: HarnessAssetEvidence = Field(default_factory=HarnessAssetEvidence)
    observability: ObservabilityEvidence = Field(default_factory=ObservabilityEvidence)
    experience: ExperienceEvidence = Field(default_factory=ExperienceEvidence)
    benchmark: BenchmarkEvidence | None = None
    maturity_inputs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
