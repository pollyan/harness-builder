from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app
from harness_builder_agent.schemas.harness_map import HarnessMap

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _prepared_repo(tmp_path: Path, fixture_name: str) -> Path:
    repo = tmp_path / fixture_name
    shutil.copytree(FIXTURES / fixture_name, repo)
    runner = CliRunner()
    init_result = runner.invoke(app, ["init", "--repo", str(repo)])
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

    sensor_report = yaml.safe_load((task_dir / "sensor-report.yaml").read_text())
    assert sensor_report["task_id"] == "demo-task-001"
    assert sensor_report["sensor_results"]
    assert sensor_report["sensor_results"][0]["status"] in {"passed", "failed", "skipped"}


def test_run_generates_bugfix_control_loop_outputs(tmp_path: Path):
    repo = _prepared_repo(tmp_path, "mini-spring-boot")
    result = CliRunner().invoke(app, ["run", "--repo", str(repo), "修复登录接口错误提示不一致的问题"])

    assert result.exit_code == 0, result.output
    _assert_task_outputs(repo, "bugfix")


def test_run_generates_lightweight_control_loop_outputs(tmp_path: Path):
    repo = _prepared_repo(tmp_path, "mini-dotnet-webapi")
    result = CliRunner().invoke(app, ["run", "--repo", str(repo), "调整 Catalog 相关低风险文案"])

    assert result.exit_code == 0, result.output
    _assert_task_outputs(repo, "lightweight")
