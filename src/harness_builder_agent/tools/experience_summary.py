from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport


def load_experience_summary(ai: Path) -> ExperienceSummaryReport | None:
    path = ai / "experience" / "experience-summary.yaml"
    if not path.exists():
        return None
    return ExperienceSummaryReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
