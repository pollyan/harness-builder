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


def _assert_real_repo(repo_name: str, profile: str) -> None:
    repo = BENCHMARKS / repo_name
    assert repo.exists(), f"Missing real benchmark repository: {repo}"

    init_result = _run_cli("init", "--repo", str(repo))
    assert init_result.returncode == 0, init_result.stderr + init_result.stdout

    benchmark_result = _run_cli("benchmark", "--repo", str(repo), "--profile", profile)
    assert benchmark_result.returncode == 0, benchmark_result.stderr + benchmark_result.stdout

    ai = repo / ".ai"
    assert (ai / "project-inventory.json").exists()
    assert (ai / "command-catalog.yaml").exists()
    assert (ai / "harness-config.yaml").exists()
    report = yaml.safe_load((ai / "benchmark-report.yaml").read_text())
    assert report["status"] == "passed"
    assert report["profile"] == profile


def test_real_repositories_init_and_benchmark_end_to_end():
    _assert_real_repo("RuoYi-Vue", "java-spring")
    _assert_real_repo("eShopOnWeb", "dotnet-aspnet")
