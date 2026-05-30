from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class WeaponLibraryEntry(BaseModel):
    id: str
    stack: str
    kind: Literal["guide", "sensor"]
    title: str
    guidance: str
    recommended_action: str
    gate: Literal["hard", "soft", "manual"] = "manual"
    evidence_hints: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class WeaponLibrarySelection(BaseModel):
    schema_version: str = "1.0"
    source: str = "built_in_weapon_library"
    primary_stack: str
    selected_stacks: list[str] = Field(default_factory=list)
    guide_weapon_ids: list[str] = Field(default_factory=list)
    sensor_weapon_ids: list[str] = Field(default_factory=list)
    guide_weapons: list[WeaponLibraryEntry] = Field(default_factory=list)
    sensor_weapons: list[WeaponLibraryEntry] = Field(default_factory=list)
