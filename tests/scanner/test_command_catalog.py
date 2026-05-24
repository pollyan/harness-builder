from pathlib import Path

from harness_builder.scanner.core import scan_repository


def test_command_catalog_contains_maven_and_frontend_commands(tmp_path):
    repo = Path("tests/fixtures/minimal-java-maven")
    out = tmp_path / ".harness"

    result = scan_repository(repo, out)

    commands = result.commands
    build_commands = [cmd["command"] for cmd in commands["commands"]["build"]]
    frontend_commands = [cmd["command"] for cmd in commands["commands"]["frontend"]]

    assert "mvn clean package -DskipTests" in build_commands
    assert "npm run build" in frontend_commands
