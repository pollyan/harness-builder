from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ScanContext:
    repo_root: Path
    out_dir: Path
    inventory: dict[str, Any] = field(default_factory=dict)
    commands: dict[str, Any] = field(default_factory=dict)
