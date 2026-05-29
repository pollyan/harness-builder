from pathlib import Path

from harness_builder_agent.tools.scan_repo import scan_repository

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_scan_repository_detects_java_spring_fixture():
    inventory, commands = scan_repository(FIXTURES / "mini-spring-boot")

    assert inventory.repo_name == "mini-spring-boot"
    assert inventory.primary_stack == "java-spring"
    assert "java" in inventory.stacks
    assert any(item["path"] == "pom.xml" for item in inventory.evidence)
    assert any(module["kind"] == "backend" for module in inventory.modules)
    assert any(command.id == "unit_test" and command.command == "mvn test" for command in commands.commands)
    assert any(command.id == "build" and command.command == "mvn package" for command in commands.commands)


def test_scan_repository_detects_dotnet_fixture():
    inventory, commands = scan_repository(FIXTURES / "mini-dotnet-webapi")

    assert inventory.repo_name == "mini-dotnet-webapi"
    assert inventory.primary_stack == "dotnet-aspnet"
    assert "dotnet" in inventory.stacks
    assert any(item["path"].endswith(".sln") for item in inventory.evidence)
    assert any(module["kind"] == "test" for module in inventory.modules)
    assert any(command.id == "unit_test" and command.command == "dotnet test" for command in commands.commands)
    assert any(command.id == "build" and command.command == "dotnet build" for command in commands.commands)
