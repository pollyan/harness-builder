from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    default_workflow: str = "lightweight"
    allow_workflow_upgrade: bool = True
    require_user_confirmation_for_high_risk: bool = True


class WorkflowDefinition(BaseModel):
    skill_path: str
    stages: list[str]


class SensorRuntimeConfig(BaseModel):
    max_repair_attempts: int = 1
    rerun_failed_only: bool = True


class WorkflowRoutingRule(BaseModel):
    id: str
    selected_workflow: Literal["lightweight", "bugfix", "standard"]
    rationale: str
    task_type_hints: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    required_guides: list[str] = Field(default_factory=list)
    required_sensors: list[str] = Field(default_factory=list)
    human_confirmation_required: bool = False


class WorkflowRoutingPolicy(BaseModel):
    default_workflow: Literal["lightweight", "bugfix", "standard"] = "lightweight"
    rules: list[WorkflowRoutingRule] = Field(default_factory=list)


class HarnessConfig(BaseModel):
    version: int = 1
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    workflows: dict[str, WorkflowDefinition]
    sensors: SensorRuntimeConfig = Field(default_factory=SensorRuntimeConfig)
    workflow_routing: WorkflowRoutingPolicy = Field(default_factory=WorkflowRoutingPolicy)

    @classmethod
    def default(cls) -> "HarnessConfig":
        return cls(
            workflows={
                "lightweight": WorkflowDefinition(
                    skill_path=".ai/skills/lightweight/SKILL.md",
                    stages=[
                        "requirement_brief",
                        "harness_mapping",
                        "implementation_or_advice",
                        "sensor_check",
                        "handoff",
                    ]
                ),
                "bugfix": WorkflowDefinition(
                    skill_path=".ai/skills/bugfix/SKILL.md",
                    stages=[
                        "observe",
                        "root_cause_investigation",
                        "harness_mapping",
                        "minimal_fix_or_advice",
                        "targeted_sensors",
                        "handoff",
                    ]
                ),
                "standard": WorkflowDefinition(
                    skill_path=".ai/skills/standard/SKILL.md",
                    stages=[
                        "requirement_alignment",
                        "harness_mapping",
                        "solution_design",
                        "implementation_plan",
                        "test_first_build_verify",
                        "review_handoff",
                    ],
                ),
            },
            workflow_routing=WorkflowRoutingPolicy(
                default_workflow="lightweight",
                rules=[
                    WorkflowRoutingRule(
                        id="bugfix-intent",
                        selected_workflow="bugfix",
                        rationale="Use the bugfix workflow when task intent is defect repair, regression, failure, error handling, or incident response.",
                        task_type_hints=["bugfix", "regression", "failure", "error", "incident"],
                        triggers=["bug_or_regression_intent", "targeted_reproduction_needed"],
                        required_guides=[".ai/guides/task-templates/bugfix.md"],
                        required_sensors=[".ai/sensors/verification.md"],
                    ),
                    WorkflowRoutingRule(
                        id="low-risk-lightweight",
                        selected_workflow="lightweight",
                        rationale="Use the lightweight workflow when scope is clear, impact is narrow, and risk remains low.",
                        task_type_hints=["documentation", "configuration", "small_feature", "copy_change"],
                        triggers=["clear_scope", "low_risk", "single_module_or_documentation_change"],
                        required_guides=[".ai/guides/project-context.md", ".ai/guides/coding-rules.md"],
                        required_sensors=[".ai/sensors/verification.md"],
                    ),
                    WorkflowRoutingRule(
                        id="standard-escalation",
                        selected_workflow="standard",
                        rationale="Escalate to the standard workflow for unclear impact, high-risk areas, cross-module design, security/data/money concerns, weak sensor coverage, or required business decisions.",
                        task_type_hints=["feature", "refactor", "migration", "architecture", "security"],
                        triggers=[
                            "unclear_impact_scope",
                            "high_risk_module",
                            "cross_module_design",
                            "security_or_permission",
                            "money_or_core_state",
                            "data_migration",
                            "low_code_mapping_confidence",
                            "insufficient_sensor_coverage",
                            "human_business_decision_required",
                        ],
                        required_guides=[".ai/guides/project-context.md", ".ai/guides/architecture.md", ".ai/guides/coding-rules.md"],
                        required_sensors=[".ai/sensors/verification.md", ".ai/sensors/test-strategy.md"],
                        human_confirmation_required=True,
                    ),
                ],
            ),
        )
