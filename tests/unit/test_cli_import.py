from typer.testing import CliRunner

from harness_builder_agent.cli import app


def test_cli_exposes_required_commands():
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in ("init", "run", "benchmark", "assess", "improve"):
        assert command in result.output
