from __future__ import annotations

from importlib import resources
from pathlib import Path

from harness_builder_agent.prompts.loader import load_prompt_sections
from harness_builder_agent.prompts.registry import MACHINE_PROMPTS, build_machine_prompt_messages


def _prompt_assets() -> set[str]:
    prompt_dir = resources.files("harness_builder_agent").joinpath("prompts")
    return {
        path.name
        for path in prompt_dir.iterdir()
        if path.name.endswith(".md")
    }


def test_all_llm_prompt_assets_are_loadable():
    prompt_dir = resources.files("harness_builder_agent").joinpath("prompts")

    for filename in _prompt_assets():
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
    prompt_assets = _prompt_assets()
    assert {asset.filename for asset in MACHINE_PROMPTS.values()} == prompt_assets

    for key, asset in MACHINE_PROMPTS.items():
        assert key
        assert asset.version
        assert asset.input_heading.endswith("JSON")
        assert asset.filename in prompt_assets


def test_build_machine_prompt_messages_loads_registered_asset():
    messages = build_machine_prompt_messages(
        "llm-first-scan-v2",
        {"schema_version": "1.0", "evidence": {"repo": "demo"}},
    )

    assert [message["role"] for message in messages] == ["system", "user"]
    assert "Evidence JSON" in messages[1]["content"]
    assert '"schema_version": "1.0"' in messages[1]["content"]
