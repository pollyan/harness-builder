from __future__ import annotations

from pathlib import Path

from harness_builder_agent.tools.scan_repo import scan_repository

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_real_deepseek_scans_java_fixture():
    inventory, commands = scan_repository(FIXTURES / "mini-spring-boot")

    assert inventory.primary_stack == "java-spring"
    assert inventory.stack_extensions["scan_metadata"]["llm_status"] == "succeeded"
    assert inventory.stack_extensions["llm_scan_proposal"]["primary_stack"] == "java-spring"
    assert commands.commands
