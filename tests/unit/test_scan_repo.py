from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness_builder_agent.tools.scan_repo import scan_repository

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _llm_response(primary_stack: str) -> str:
    if primary_stack == "java-spring":
        command = {"id": "unit_test", "command": "mvn test", "type": "test", "gate": "hard", "source": "pom.xml", "confidence": "high"}
        stacks = ["java", "maven", "spring-boot"]
        modules = [{"name": "app", "path": ".", "kind": "backend"}]
        summary = "Java Spring project."
    else:
        command = {
            "id": "unit_test",
            "command": "dotnet test",
            "type": "test",
            "gate": "hard",
            "source": "mini-dotnet-webapi.sln",
            "confidence": "high",
        }
        stacks = ["dotnet", "aspnet-core"]
        modules = [{"name": "MiniApi", "path": "src", "kind": "backend"}]
        summary = ".NET ASP.NET project."
    return json.dumps(
        {
            "primary_stack": primary_stack,
            "stacks": stacks,
            "modules": modules,
            "architecture_signals": [],
            "risk_areas": [],
            "command_candidates": [command],
            "configs": [],
            "ci_files": [],
            "confidence": "high",
            "needs_human_confirmation": False,
            "reasoning_summary": summary,
        }
    )


def test_scan_repository_uses_llm_for_java_spring_fixture():
    inventory, commands = scan_repository(FIXTURES / "mini-spring-boot", llm_caller=lambda _messages: _llm_response("java-spring"))

    assert inventory.repo_name == "mini-spring-boot"
    assert inventory.primary_stack == "java-spring"
    assert "spring-boot" in inventory.stacks
    assert inventory.stack_extensions["scan_metadata"]["llm_status"] == "succeeded"
    assert inventory.stack_extensions["llm_scan_proposal"]["primary_stack"] == "java-spring"
    assert any(command.id == "unit_test" and command.command == "mvn test" and command.gate == "hard" for command in commands.commands)


def test_scan_repository_uses_llm_for_dotnet_fixture():
    inventory, commands = scan_repository(FIXTURES / "mini-dotnet-webapi", llm_caller=lambda _messages: _llm_response("dotnet-aspnet"))

    assert inventory.repo_name == "mini-dotnet-webapi"
    assert inventory.primary_stack == "dotnet-aspnet"
    assert "aspnet-core" in inventory.stacks
    assert inventory.stack_extensions["scan_metadata"]["llm_status"] == "succeeded"
    assert any(command.id == "unit_test" and command.command == "dotnet test" and command.gate == "hard" for command in commands.commands)


def test_scan_repository_fails_when_llm_claim_conflicts_with_hard_evidence():
    with pytest.raises(ValueError, match="dotnet"):
        scan_repository(FIXTURES / "mini-spring-boot", llm_caller=lambda _messages: _llm_response("dotnet-aspnet"))
