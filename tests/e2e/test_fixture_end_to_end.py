from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
ROOT = Path(__file__).resolve().parents[2]


def _run_cli(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "harness_builder_agent.cli", *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
        check=False,
    )


def test_fixture_cli_end_to_end_for_java_and_dotnet(tmp_path: Path):
    cases = [
        ("mini-spring-boot", "java-spring", "修复登录接口错误提示不一致的问题"),
        ("mini-dotnet-webapi", "dotnet-aspnet", "调整 Catalog 相关低风险文案"),
    ]

    for fixture_name, profile, task in cases:
        repo = tmp_path / fixture_name
        shutil.copytree(FIXTURES / fixture_name, repo)

        init_result = _run_cli(repo, "init", "--repo", str(repo))
        assert init_result.returncode == 0, init_result.stderr + init_result.stdout

        run_result = _run_cli(repo, "run", "--repo", str(repo), task)
        assert run_result.returncode == 0, run_result.stderr + run_result.stdout

        assess_result = _run_cli(repo, "assess", "--repo", str(repo))
        assert assess_result.returncode == 0, assess_result.stderr + assess_result.stdout

        improve_result = _run_cli(repo, "improve", "--repo", str(repo))
        assert improve_result.returncode == 0, improve_result.stderr + improve_result.stdout

        benchmark_result = _run_cli(repo, "benchmark", "--repo", str(repo), "--profile", profile)
        assert benchmark_result.returncode == 0, benchmark_result.stderr + benchmark_result.stdout

        task_dir = repo / ".ai" / "task-runs" / "demo-task-001"
        assert (task_dir / "harness-map.yaml").exists()
        assert (task_dir / "sensor-report.yaml").exists()
        assert (repo / ".ai" / "skills" / "lightweight" / "SKILL.md").exists()
        assert (repo / ".ai" / "skills" / "bugfix" / "SKILL.md").exists()
        assert (repo / ".ai" / "maturity-score.yaml").exists()
        assert (repo / ".ai" / "improvement-candidates.yaml").exists()
        report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
        assert report["status"] == "passed"
        check_ids = {check["id"] for check in report["checks"]}
        assert "content:workflow-skills" in check_ids
        assert "content:guides-quality" in check_ids
        assert "content:sensors-quality" in check_ids
