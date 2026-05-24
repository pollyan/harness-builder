from pathlib import Path

from harness_builder.scanner.core import scan_repository


def test_command_catalog_contains_dotnet_build_and_test(tmp_path):
    repo = Path("tests/fixtures/minimal-dotnet")
    out = tmp_path / ".harness"

    result = scan_repository(repo, out)

    build_commands = [cmd["command"] for cmd in result.commands["commands"]["build"]]
    test_commands = [cmd["command"] for cmd in result.commands["commands"]["test"]]

    assert "dotnet build" in build_commands
    assert "dotnet test" in test_commands
    assert result.inventory["stackExtensions"]["dotnet"]["detected"] is True
