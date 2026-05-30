from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app
from harness_builder_agent.schemas.harness_map import HarnessMap
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


def _failed_sensor(_repo, command):
    return {
        "id": command.id,
        "command": command.command,
        "status": "failed",
        "exit_code": 1,
        "duration_seconds": 0.01,
        "summary": "Sensor failed.",
    }


def _skipped_sensor(_repo, command):
    return {
        "id": command.id,
        "command": command.command,
        "status": "skipped",
        "exit_code": None,
        "duration_seconds": 0.0,
        "summary": "Executable missing.",
    }


def _prepared_repo(tmp_path: Path, fixture_name: str, primary_stack: str, monkeypatch) -> Path:
    repo = tmp_path / fixture_name
    shutil.copytree(FIXTURES / fixture_name, repo)
    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", lambda repo_path: _fake_scan(repo_path, primary_stack))
    monkeypatch.setattr("harness_builder_agent.tools.run_task.run_sensor", _passed_sensor)
    runner = CliRunner()
    init_result = runner.invoke(app, ["init", "--repo", str(repo), "--non-interactive"])
    assert init_result.exit_code == 0, init_result.output
    return repo


def _assert_task_outputs(repo: Path, expected_workflow: str) -> None:
    task_dir = repo / ".ai" / "task-runs" / "demo-task-001"
    assert (task_dir / "harness-map.yaml").exists()
    assert (task_dir / "sensor-report.yaml").exists()
    assert (task_dir / "decision-log.md").exists()
    assert (task_dir / "handoff-summary.md").exists()
    assert (task_dir / "experience-candidates.md").exists()

    harness_map = HarnessMap.model_validate(yaml.safe_load((task_dir / "harness-map.yaml").read_text()))
    assert harness_map.selected_workflow == expected_workflow
    assert harness_map.risk_level == "low"
    assert harness_map.guide_policy["required"]
    assert harness_map.sensor_policy["hard_gates"]
    assert harness_map.workflow_skill["path"] == f".ai/skills/{expected_workflow}/SKILL.md"
    assert (repo / harness_map.workflow_skill["path"]).exists()

    sensor_report = yaml.safe_load((task_dir / "sensor-report.yaml").read_text())
    assert sensor_report["task_id"] == "demo-task-001"
    assert sensor_report["sensor_results"]
    assert sensor_report["sensor_results"][0]["status"] in {"passed", "failed", "skipped"}

    assert (task_dir / "workflow-events.jsonl").exists()
    assert (task_dir / "used-guides.yaml").exists()
    assert (task_dir / "runtime-summary.yaml").exists()

    events = [json.loads(line) for line in (task_dir / "workflow-events.jsonl").read_text(encoding="utf-8").splitlines()]
    stages = {event["stage"] for event in events}
    assert {
        "task-classification",
        "guide-selection",
        "workflow-selection",
        "sensor-selection",
        "sensor-execution",
        "handoff",
        "experience-candidate",
    }.issubset(stages)

    used_guides = yaml.safe_load((task_dir / "used-guides.yaml").read_text(encoding="utf-8"))
    assert used_guides["workflow_skill"]["path"] == f".ai/skills/{expected_workflow}/SKILL.md"
    assert all(item["path"].startswith(".ai/guides/") for item in used_guides["required_guides"])
    assert all(item["exists"] is True for item in used_guides["required_guides"])

    runtime = yaml.safe_load((task_dir / "runtime-summary.yaml").read_text(encoding="utf-8"))
    assert runtime["selected_workflow"] == expected_workflow
    assert runtime["used_guide_count"] == len(used_guides["required_guides"])
    assert runtime["sensor_statuses"]


def test_run_generates_bugfix_control_loop_outputs(tmp_path: Path, monkeypatch):
    repo = _prepared_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    result = CliRunner().invoke(app, ["run", "--repo", str(repo), "修复登录接口错误提示不一致的问题"])

    assert result.exit_code == 0, result.output
    _assert_task_outputs(repo, "bugfix")


def test_run_generates_lightweight_control_loop_outputs(tmp_path: Path, monkeypatch):
    repo = _prepared_repo(tmp_path, "mini-dotnet-webapi", "dotnet-aspnet", monkeypatch)
    result = CliRunner().invoke(app, ["run", "--repo", str(repo), "调整 Catalog 相关低风险文案"])

    assert result.exit_code == 0, result.output
    _assert_task_outputs(repo, "lightweight")


def test_run_records_failed_sensor_status(tmp_path: Path, monkeypatch):
    repo = _prepared_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    monkeypatch.setattr("harness_builder_agent.tools.run_task.run_sensor", _failed_sensor)

    result = CliRunner().invoke(app, ["run", "--repo", str(repo), "修复登录接口错误提示不一致的问题"])

    assert result.exit_code == 0, result.output
    task_dir = repo / ".ai" / "task-runs" / "demo-task-001"
    report = yaml.safe_load((task_dir / "sensor-report.yaml").read_text(encoding="utf-8"))
    runtime = yaml.safe_load((task_dir / "runtime-summary.yaml").read_text(encoding="utf-8"))
    assert report["sensor_results"][0]["status"] == "failed"
    assert runtime["sensor_statuses"]["unit_test"] == "failed"
    assert runtime["unresolved_sensor_count"] == 1


def test_run_records_skipped_sensor_status(tmp_path: Path, monkeypatch):
    repo = _prepared_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    monkeypatch.setattr("harness_builder_agent.tools.run_task.run_sensor", _skipped_sensor)

    result = CliRunner().invoke(app, ["run", "--repo", str(repo), "修复登录接口错误提示不一致的问题"])

    assert result.exit_code == 0, result.output
    task_dir = repo / ".ai" / "task-runs" / "demo-task-001"
    report = yaml.safe_load((task_dir / "sensor-report.yaml").read_text(encoding="utf-8"))
    runtime = yaml.safe_load((task_dir / "runtime-summary.yaml").read_text(encoding="utf-8"))
    assert report["sensor_results"][0]["status"] == "skipped"
    assert runtime["sensor_statuses"]["unit_test"] == "skipped"
    assert runtime["unresolved_sensor_count"] == 1


def test_run_marks_missing_guide_in_used_guides(tmp_path: Path, monkeypatch):
    repo = _prepared_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    (repo / ".ai" / "guides" / "architecture.md").unlink()

    result = CliRunner().invoke(app, ["run", "--repo", str(repo), "修复登录接口错误提示不一致的问题"])

    assert result.exit_code == 0, result.output
    used_guides = yaml.safe_load((repo / ".ai" / "task-runs" / "demo-task-001" / "used-guides.yaml").read_text(encoding="utf-8"))
    assert any(item["path"] == ".ai/guides/architecture.md" and item["exists"] is False for item in used_guides["required_guides"])
