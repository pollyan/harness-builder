from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_text
from harness_builder_agent.tools.generation_trace import GenerationTrace


def write_skill_assets(ai: Path, trace: GenerationTrace | None = None) -> None:
    template_root = files("harness_builder_agent").joinpath("templates", "skills")
    for name in ("lightweight", "bugfix"):
        path = ai / "skills" / name / "SKILL.md"
        content = template_root.joinpath(name, "SKILL.md").read_text(encoding="utf-8")
        write_text(path, content)
        record_artifact(trace, path, "skill")
