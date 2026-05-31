from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from harness_builder_agent.schemas.harness_config import WorkflowRoutingRule


class WorkflowPolicyPatch(BaseModel):
    schema_version: str = "1.0"
    operation: Literal["upsert_routing_rule"]
    target: Literal["workflow_routing.rules"]
    rule: WorkflowRoutingRule
