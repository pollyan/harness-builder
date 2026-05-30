from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app
from harness_builder_agent.tools.scan_repo import scan_repository

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _fake_scan(repo: Path, primary_stack: str):
    if primary_stack == "java-spring":
        response = {
            "primary_stack": "java-spring",
            "stacks": ["java", "maven", "spring-boot"],
            "modules": [{"name": "app", "path": ".", "kind": "backend"}],
            "architecture_signals": [],
            "risk_areas": [],
            "command_candidates": [
                {"id": "unit_test", "command": "mvn test", "type": "test", "gate": "hard", "source": "pom.xml", "confidence": "high"}
            ],
            "configs": [],
            "ci_files": [],
            "confidence": "high",
            "needs_human_confirmation": False,
            "reasoning_summary": "Java Spring project.",
        }
    else:
        response = {
            "primary_stack": "dotnet-aspnet",
            "stacks": ["dotnet", "aspnet-core"],
            "modules": [{"name": "MiniApi", "path": "src", "kind": "backend"}],
            "architecture_signals": [],
            "risk_areas": [],
            "command_candidates": [
                {
                    "id": "unit_test",
                    "command": "dotnet test",
                    "type": "test",
                    "gate": "hard",
                    "source": "mini-dotnet-webapi.sln",
                    "confidence": "high",
                }
            ],
            "configs": [],
            "ci_files": [],
            "confidence": "high",
            "needs_human_confirmation": False,
            "reasoning_summary": ".NET ASP.NET project.",
        }
    return scan_repository(repo, llm_caller=lambda _messages: json.dumps(response))


def _passed_sensor(_repo, command):
    return {
        "id": command.id,
        "command": command.command,
        "status": "passed",
        "exit_code": 0,
        "duration_seconds": 0.01,
        "summary": "Sensor completed.",
    }


def _skipped_sensor(_repo, command):
    return {
        "id": command.id,
        "command": command.command,
        "status": "skipped",
        "exit_code": None,
        "duration_seconds": 0.0,
        "summary": "Executable is not available.",
    }


def _latest_trace(repo: Path) -> dict:
    runs = sorted((repo / ".ai" / "runs").iterdir())
    assert runs
    return yaml.safe_load((runs[-1] / "trace.yaml").read_text(encoding="utf-8"))


def test_benchmark_generates_report_for_java_fixture(tmp_path: Path, monkeypatch):
    repo = tmp_path / "mini-spring-boot"
    shutil.copytree(FIXTURES / "mini-spring-boot", repo)
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    monkeypatch.setattr("harness_builder_agent.tools.run_task.run_sensor", _passed_sensor)

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    assert report["profile"] == "java-spring"
    assert report["status"] == "passed"
    assert report["checks"]
    assert all(check["passed"] for check in report["checks"])
    check_ids = {check["id"] for check in report["checks"]}
    assert "exists:scan-metadata.yaml" in check_ids
    assert "exists:llm-scan-proposal.json" in check_ids
    assert "content:workflow-skills" in check_ids
    assert "content:harness-map-workflow-skill" in check_ids
    assert "content:guides-quality" in check_ids
    assert "content:stack-specific-guides" in check_ids
    assert "content:sensors-quality" in check_ids
    assert "content:weapon-library-selection" in check_ids
    assert "content:hard-gate-sensors-passed" in check_ids
    assert "schema:harness-map" in check_ids
    assert "schema:sensor-report" in check_ids
    assert "schema:scan-metadata" in check_ids
    assert "schema:llm-scan-proposal" in check_ids
    assert "schema:weapon-library-selection" in check_ids
    assert "schema:benchmark-report" in check_ids
    assert "schema:maturity-score" in check_ids
    assert "schema:improvement-candidates" in check_ids
    assert "exists:runs-trace" in check_ids
    assert "schema:generation-trace" in check_ids
    assert "content:generation-trace" in check_ids
    assert "schema:runtime-summary" in check_ids
    assert "content:runtime-workflow-trace" in check_ids
    assert "schema:questionnaire" in check_ids
    assert "content:human-confirmation" in check_ids
    assert (repo / ".ai" / "task-runs" / "demo-task-001" / "harness-map.yaml").exists()
    trace = _latest_trace(repo)
    assert trace["command"] == "benchmark"
    assert trace["status"] == "completed"
    assert "benchmark" in trace["stages"]


def test_benchmark_generates_report_for_dotnet_fixture(tmp_path: Path, monkeypatch):
    repo = tmp_path / "mini-dotnet-webapi"
    shutil.copytree(FIXTURES / "mini-dotnet-webapi", repo)
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, "dotnet-aspnet"))
    monkeypatch.setattr("harness_builder_agent.tools.run_task.run_sensor", _passed_sensor)

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "dotnet-aspnet"])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    assert report["profile"] == "dotnet-aspnet"
    assert report["status"] == "passed"
    check_ids = {check["id"] for check in report["checks"]}
    assert "content:hard-gate-sensors-passed" in check_ids
    assert "schema:benchmark-report" in check_ids


def test_benchmark_fails_when_hard_gate_sensor_is_skipped(tmp_path: Path, monkeypatch):
    repo = tmp_path / "mini-spring-boot"
    shutil.copytree(FIXTURES / "mini-spring-boot", repo)
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    monkeypatch.setattr("harness_builder_agent.tools.run_task.run_sensor", _skipped_sensor)

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])

    assert result.exit_code == 1, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    assert report["status"] == "failed"
    hard_gate_check = next(check for check in report["checks"] if check["id"] == "content:hard-gate-sensors-passed")
    assert hard_gate_check["passed"] is False
