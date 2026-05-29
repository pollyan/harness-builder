from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_benchmark_generates_report_for_java_fixture(tmp_path: Path):
    repo = tmp_path / "mini-spring-boot"
    shutil.copytree(FIXTURES / "mini-spring-boot", repo)

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    assert report["profile"] == "java-spring"
    assert report["status"] == "passed"
    assert report["checks"]
    assert all(check["passed"] for check in report["checks"])


def test_benchmark_generates_report_for_dotnet_fixture(tmp_path: Path):
    repo = tmp_path / "mini-dotnet-webapi"
    shutil.copytree(FIXTURES / "mini-dotnet-webapi", repo)

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "dotnet-aspnet"])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    assert report["profile"] == "dotnet-aspnet"
    assert report["status"] == "passed"
