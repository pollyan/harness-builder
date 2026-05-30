from __future__ import annotations

from pathlib import Path
from typing import Any

from harness_builder_agent.schemas.interaction_decision import InteractionDecisions
from harness_builder_agent.tools.asset_writers.shared import record_artifact, write_text, write_yaml
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.human_confirmation import human_input_markdown
from harness_builder_agent.tools.interaction_decisions import default_non_interactive_decisions, interaction_decisions_markdown


def write_human_confirmation_assets(
    ai: Path,
    context_inputs: dict[str, Any],
    questionnaire: dict[str, Any],
    trace: GenerationTrace | None = None,
    interaction_decisions: InteractionDecisions | None = None,
) -> None:
    decisions = interaction_decisions or default_non_interactive_decisions(str(ai.parent))
    write_yaml(ai / "context-inputs.yaml", context_inputs)
    record_artifact(trace, ai / "context-inputs.yaml", "context_inputs")
    write_yaml(ai / "questionnaire.yaml", questionnaire)
    record_artifact(trace, ai / "questionnaire.yaml", "questionnaire")
    write_yaml(ai / "interaction-decisions.yaml", decisions.model_dump(mode="json"))
    record_artifact(trace, ai / "interaction-decisions.yaml", "interaction_decisions")
    if trace:
        trace.decision(
            "interaction-decisions",
            "Human interaction decisions recorded.",
            decisions.model_dump(mode="json"),
        )
    write_text(
        ai / "human-input-needed.md",
        human_input_markdown(context_inputs, questionnaire, interaction_decisions_markdown(decisions)),
    )
    record_artifact(trace, ai / "human-input-needed.md", "human_confirmation")
