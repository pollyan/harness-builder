from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProjectInventory(BaseModel):
    schema_version: str = "1.0"
    repo_name: str
    root_path: str
    primary_stack: str
    stacks: list[str] = Field(default_factory=list)
    modules: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    configs: list[dict[str, Any]] = Field(default_factory=list)
    ci_files: list[dict[str, Any]] = Field(default_factory=list)
    stack_extensions: dict[str, Any] = Field(default_factory=dict)
