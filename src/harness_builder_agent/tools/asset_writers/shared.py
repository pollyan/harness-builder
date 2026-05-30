from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.tools.generation_trace import GenerationTrace


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def record_artifact(trace: GenerationTrace | None, path: Path, kind: str) -> None:
    if trace:
        trace.artifact(path, kind)
