from __future__ import annotations

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    default_workflow: str = "lightweight"
    allow_workflow_upgrade: bool = True
    require_user_confirmation_for_high_risk: bool = True


class WorkflowDefinition(BaseModel):
    stages: list[str]


class SensorRuntimeConfig(BaseModel):
    max_repair_attempts: int = 1
    rerun_failed_only: bool = True


class HarnessConfig(BaseModel):
    version: int = 1
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    workflows: dict[str, WorkflowDefinition]
    sensors: SensorRuntimeConfig = Field(default_factory=SensorRuntimeConfig)

    @classmethod
    def default(cls) -> "HarnessConfig":
        return cls(
            workflows={
                "lightweight": WorkflowDefinition(
                    stages=[
                        "requirement_brief",
                        "harness_mapping",
                        "implementation_or_advice",
                        "sensor_check",
                        "handoff",
                    ]
                ),
                "bugfix": WorkflowDefinition(
                    stages=[
                        "observe",
                        "root_cause_investigation",
                        "harness_mapping",
                        "minimal_fix_or_advice",
                        "targeted_sensors",
                        "handoff",
                    ]
                ),
            }
        )
