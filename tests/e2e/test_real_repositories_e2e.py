from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BENCHMARKS = ROOT / ".benchmarks"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "harness_builder_agent.cli", *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )


def _assert_task_run_outputs(repo: Path, expected_workflow: str) -> None:
    task_dir = repo / ".ai" / "task-runs" / "demo-task-001"
    assert (task_dir / "harness-map.yaml").exists()
    assert (task_dir / "sensor-report.yaml").exists()
    assert (task_dir / "decision-log.md").exists()
    assert (task_dir / "handoff-summary.md").exists()
    assert (task_dir / "experience-candidates.md").exists()

    harness_map = yaml.safe_load((task_dir / "harness-map.yaml").read_text())
    assert harness_map["selected_workflow"] == expected_workflow
    assert harness_map["workflow_skill"]["path"] == f".ai/skills/{expected_workflow}/SKILL.md"
    sensor_report = yaml.safe_load((task_dir / "sensor-report.yaml").read_text())
    assert sensor_report["sensor_results"]


def _assert_real_repo(repo_name: str, profile: str, task: str, expected_workflow: str) -> None:
    repo = BENCHMARKS / repo_name
    assert repo.exists(), f"Missing real benchmark repository: {repo}"

    init_result = _run_cli("init", "--repo", str(repo))
    assert init_result.returncode == 0, init_result.stderr + init_result.stdout

    run_result = _run_cli("run", "--repo", str(repo), task)
    assert run_result.returncode == 0, run_result.stderr + run_result.stdout

    assess_result = _run_cli("assess", "--repo", str(repo))
    assert assess_result.returncode == 0, assess_result.stderr + assess_result.stdout

    improve_result = _run_cli("improve", "--repo", str(repo))
    assert improve_result.returncode == 0, improve_result.stderr + improve_result.stdout

    benchmark_result = _run_cli("benchmark", "--repo", str(repo), "--profile", profile)
    assert benchmark_result.returncode == 0, benchmark_result.stderr + benchmark_result.stdout

    ai = repo / ".ai"
    assert (ai / "project-inventory.json").exists()
    assert (ai / "command-catalog.yaml").exists()
    assert (ai / "harness-config.yaml").exists()
    assert (ai / "skills" / "lightweight" / "SKILL.md").exists()
    assert (ai / "skills" / "bugfix" / "SKILL.md").exists()
    assert (ai / "maturity-score.yaml").exists()
    assert (ai / "improvement-candidates.yaml").exists()
    report = yaml.safe_load((ai / "benchmark-report.yaml").read_text())
    assert report["status"] == "passed"
    assert report["profile"] == profile
    check_ids = {check["id"] for check in report["checks"]}
    assert "content:workflow-skills" in check_ids
    assert "content:harness-map-workflow-skill" in check_ids
    assert "content:guides-quality" in check_ids
    assert "content:sensors-quality" in check_ids
    _assert_task_run_outputs(repo, expected_workflow)


def test_real_repositories_init_run_and_benchmark_end_to_end():
    _assert_real_repo("RuoYi-Vue", "java-spring", "修复登录接口错误提示不一致的问题", "bugfix")
    _assert_real_repo("eShopOnWeb", "dotnet-aspnet", "调整 Catalog 相关低风险文案", "lightweight")
