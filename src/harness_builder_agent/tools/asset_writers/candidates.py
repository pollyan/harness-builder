from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_text, write_yaml
from harness_builder_agent.tools.experience_index import ensure_experience_files, write_experience_index
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.llm_enhancement_candidates import (
    candidate_guides_markdown,
    candidate_sensors_markdown,
    enhancement_summary_markdown,
)


def write_candidate_assets(
    ai: Path,
    enhancement_candidates: dict[str, Any],
    trace: GenerationTrace | None = None,
) -> None:
    ensure_experience_files(ai)
    pending_improvements = ai / "experience" / "pending-improvements.md"
    if not pending_improvements.exists():
        write_text(pending_improvements, "# Pending Improvements\n\nNo reviewed improvements yet.\n")
    record_artifact(trace, pending_improvements, "experience")

    weapon_candidates = ai / "experience" / "weapon-library-candidates.yaml"
    write_yaml(weapon_candidates, enhancement_candidates)
    record_artifact(trace, weapon_candidates, "weapon_library_candidates")

    llm_candidates = ai / "review" / "llm-enhancement-candidates.md"
    write_text(llm_candidates, enhancement_summary_markdown(enhancement_candidates))
    record_artifact(trace, llm_candidates, "review")

    candidate_guides = ai / "review" / "candidate-guides.md"
    write_text(candidate_guides, candidate_guides_markdown(enhancement_candidates))
    record_artifact(trace, candidate_guides, "review")

    candidate_sensors = ai / "review" / "candidate-sensors.md"
    write_text(candidate_sensors, candidate_sensors_markdown(enhancement_candidates))
    record_artifact(trace, candidate_sensors, "review")
    write_experience_index(ai, trace=trace)
