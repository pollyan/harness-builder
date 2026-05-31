from __future__ import annotations

from importlib import resources
from pathlib import Path

from harness_builder_agent.prompts.loader import load_prompt_sections
from harness_builder_agent.prompts.registry import MACHINE_PROMPTS, build_machine_prompt_messages


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
        if (
            "Return one JSON object only" in source
            or "Field contract:" in source
            or "PROMPT_RESOURCE" in source
            or "load_prompt_sections" in source
        ):
            offenders.append(path.name)

    assert offenders == []


def test_machine_prompt_registry_is_the_single_prompt_inventory():
    assert {asset.filename for asset in MACHINE_PROMPTS.values()} == PROMPT_ASSETS

    for key, asset in MACHINE_PROMPTS.items():
        assert key
        assert asset.version
        assert asset.input_heading.endswith("JSON")
        assert asset.filename in PROMPT_ASSETS


def test_build_machine_prompt_messages_loads_registered_asset():
    messages = build_machine_prompt_messages(
        "llm-first-scan-v2",
        {"schema_version": "1.0", "evidence": {"repo": "demo"}},
    )

    assert [message["role"] for message in messages] == ["system", "user"]
    assert "Evidence JSON" in messages[1]["content"]
    assert '"schema_version": "1.0"' in messages[1]["content"]
