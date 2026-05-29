from typer.testing import CliRunner

from harness_builder_agent.cli import app


def test_cli_exposes_three_required_commands():
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "init" in result.output
    assert "run" in result.output
    assert "benchmark" in result.output
