from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.benchmark import _content_checks, _schema_checks
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


def _prepare_passed_benchmark_repo(tmp_path: Path, monkeypatch, fixture_name: str = "mini-spring-boot", profile: str = "java-spring") -> Path:
    repo = tmp_path / fixture_name
    shutil.copytree(FIXTURES / fixture_name, repo)
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, profile))
    monkeypatch.setattr("harness_builder_agent.tools.run_task.run_sensor", _passed_sensor)
    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", profile])
    assert result.exit_code == 0, result.output
    return repo


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
    assert "exists:review/llm-enhancement-candidates.md" in check_ids
    assert "schema:weapon-library-candidates" in check_ids
    assert "content:llm-enhancement-candidates" in check_ids
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


def test_benchmark_schema_checks_fail_when_project_inventory_is_invalid(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    (ai / "project-inventory.json").write_text("{not valid json", encoding="utf-8")

    checks = _schema_checks(ai)

    project_inventory = next(check for check in checks if check["id"] == "schema:project-inventory")
    assert project_inventory["passed"] is False
    assert project_inventory["error"]


def test_benchmark_content_checks_fail_when_guide_required_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    (ai / "guides" / "project-context.md").write_text("# Project Context\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    guide_check = next(check for check in checks if check["id"] == "content:guides-quality")
    stack_check = next(check for check in checks if check["id"] == "content:stack-specific-guides")
    assert guide_check["passed"] is False
    assert stack_check["passed"] is False


def test_benchmark_content_checks_fail_when_workflow_skill_file_is_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    (ai / "skills" / "bugfix" / "SKILL.md").unlink()
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    workflow_skill = next(check for check in checks if check["id"] == "content:workflow-skills")
    harness_map_skill = next(check for check in checks if check["id"] == "content:harness-map-workflow-skill")
    assert workflow_skill["passed"] is False
    assert harness_map_skill["passed"] is False
