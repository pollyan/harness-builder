from __future__ import annotations

from importlib import resources
from pathlib import Path

from harness_builder_agent.prompts.loader import load_prompt_sections


PROMPT_ASSETS = {
    "llm_first_scan_v2.md",
    "llm_maturity_review_v2.md",
    "llm_asset_candidate_v2.md",
    "llm_experience_summary_v1.md",
    "llm_workflow_router_v1.md",
}


def test_all_llm_prompt_assets_are_loadable():
    prompt_dir = resources.files("harness_builder_agent").joinpath("prompts")

    for filename in PROMPT_ASSETS:
        prompt = prompt_dir.joinpath(filename)
        assert prompt.is_file(), filename
        system, user = load_prompt_sections(filename)
        assert system
        assert user
        assert "JSON" in user or "JSON" in system


def test_llm_tool_modules_do_not_embed_machine_prompt_contracts():
    tools_dir = Path(__file__).resolve().parents[2] / "src" / "harness_builder_agent" / "tools"
    offenders = []

    for path in tools_dir.glob("llm_*.py"):
        source = path.read_text(encoding="utf-8")
        if "Return one JSON object only" in source or "Field contract:" in source:
            offenders.append(path.name)

    assert offenders == []
