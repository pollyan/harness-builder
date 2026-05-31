from typer.testing import CliRunner

from harness_builder_agent.cli import app


def test_cli_exposes_harness_builder_commands_without_run():
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("init", "benchmark", "assess", "improve"):
        assert command in result.output
    assert " run " not in result.output


def test_cli_run_command_is_not_available():
    runner = CliRunner()

    result = runner.invoke(app, ["run", "--repo", ".", "demo task"])

    assert result.exit_code != 0
    assert "No such command" in result.output
