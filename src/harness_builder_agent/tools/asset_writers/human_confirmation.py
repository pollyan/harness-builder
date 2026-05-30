from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_text, write_yaml
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.human_confirmation import human_input_markdown


def write_human_confirmation_assets(
    ai: Path,
    context_inputs: dict[str, Any],
    questionnaire: dict[str, Any],
    trace: GenerationTrace | None = None,
) -> None:
    write_yaml(ai / "context-inputs.yaml", context_inputs)
    record_artifact(trace, ai / "context-inputs.yaml", "context_inputs")
    write_yaml(ai / "questionnaire.yaml", questionnaire)
    record_artifact(trace, ai / "questionnaire.yaml", "questionnaire")
    write_text(ai / "human-input-needed.md", human_input_markdown(context_inputs, questionnaire))
    record_artifact(trace, ai / "human-input-needed.md", "human_confirmation")
