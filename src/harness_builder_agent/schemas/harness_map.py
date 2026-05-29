from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HarnessMap(BaseModel):
    schema_version: str = "1.0"
    task_id: str
    task_type: Literal["bugfix", "lightweight"]
    selected_workflow: Literal["bugfix", "lightweight"]
    risk_level: Literal["low", "medium", "high"] = "low"
    confidence: dict[str, str] = Field(default_factory=dict)
    relevant_modules: list[str] = Field(default_factory=list)
    guide_policy: dict[str, list[str]] = Field(default_factory=dict)
    sensor_policy: dict[str, list[str]] = Field(default_factory=dict)
    human_confirmation: dict[str, Any] = Field(default_factory=lambda: {"required": False, "reasons": []})
