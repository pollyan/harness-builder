from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from harness_builder_agent.prompts.loader import load_prompt_sections


@dataclass(frozen=True)
class MachinePromptAsset:
    key: str
    version: str
    filename: str
    input_heading: str


LLM_FIRST_SCAN_V2 = MachinePromptAsset(
    key="llm-first-scan-v2",
    version="llm-first-scan-v2",
    filename="llm_first_scan_v2.md",
    input_heading="Evidence JSON",
)
LLM_MATURITY_REVIEW_V2 = MachinePromptAsset(
    key="llm-maturity-review-v2",
    version="llm-maturity-review-v2",
    filename="llm_maturity_review_v2.md",
    input_heading="Review input JSON",
)
LLM_ASSET_CANDIDATE_V2 = MachinePromptAsset(
    key="llm-asset-candidate-v2",
    version="llm-asset-candidate-v2",
    filename="llm_asset_candidate_v2.md",
    input_heading="Candidate generation input JSON",
)
LLM_EXPERIENCE_SUMMARY_V1 = MachinePromptAsset(
    key="llm-experience-summary-v1",
    version="llm-experience-summary-v1",
    filename="llm_experience_summary_v1.md",
    input_heading="Experience input JSON",
)
LLM_WORKFLOW_ROUTER_V1 = MachinePromptAsset(
    key="llm-workflow-router-v1",
    version="llm-workflow-router-v1",
    filename="llm_workflow_router_v1.md",
    input_heading="Workflow routing input JSON",
)

MACHINE_PROMPTS: dict[str, MachinePromptAsset] = {
    asset.key: asset
    for asset in (
        LLM_FIRST_SCAN_V2,
        LLM_MATURITY_REVIEW_V2,
        LLM_ASSET_CANDIDATE_V2,
        LLM_EXPERIENCE_SUMMARY_V1,
        LLM_WORKFLOW_ROUTER_V1,
    )
}


def get_machine_prompt(key: str) -> MachinePromptAsset:
    try:
        return MACHINE_PROMPTS[key]
    except KeyError as exc:
        raise ValueError(f"Unknown machine prompt asset: {key}") from exc


def build_machine_prompt_messages(key: str, payload: dict[str, Any]) -> list[dict[str, str]]:
    asset = get_machine_prompt(key)
    system_prompt, user_prompt = load_prompt_sections(asset.filename)
    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": (
                f"{user_prompt}\n\n"
                f"{asset.input_heading}:\n"
                f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
            ),
        },
    ]
