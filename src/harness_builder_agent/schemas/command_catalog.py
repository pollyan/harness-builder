from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from harness_builder_agent.schemas.common import Confidence, Gate


class CommandDefinition(BaseModel):
    id: str
    command: str
    type: Literal["build", "test", "lint", "typecheck", "other"]
    gate: Gate
    source: str
    confidence: Confidence = "medium"
    verified: bool = False


class CommandCatalog(BaseModel):
    schema_version: str = "1.0"
    commands: list[CommandDefinition] = Field(default_factory=list)
