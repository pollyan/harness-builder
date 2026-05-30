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
    env.setdefault("HARNESS_BUILDER_SENSOR_TIMEOUT_SECONDS", "20")
    env.setdefault("HARNESS_BUILDER_LLM_TIMEOUT_SECONDS", "180")
    return subprocess.run(
        [sys.executable, "-m", "harness_builder_agent.cli", *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
        check=False,
    )


def _assert_real_repo(repo_name: str, profile: str, task: str, expected_workflow: str) -> None:
    repo = BENCHMARKS / repo_name
    assert repo.exists(), f"Missing real benchmark repository: {repo}"
    report_path = repo / ".ai" / "benchmark-report.yaml"
    report_path.unlink(missing_ok=True)

    init_result = _run_cli("init", "--repo", str(repo))
    assert init_result.returncode == 0, init_result.stderr + init_result.stdout

    run_result = _run_cli("run", "--repo", str(repo), task)
    assert run_result.returncode == 0, run_result.stderr + run_result.stdout

    assess_result = _run_cli("assess", "--repo", str(repo))
    assert assess_result.returncode == 0, assess_result.stderr + assess_result.stdout

    improve_result = _run_cli("improve", "--repo", str(repo))
    assert improve_result.returncode == 0, improve_result.stderr + improve_result.stdout

    benchmark_result = _run_cli("benchmark", "--repo", str(repo), "--profile", profile)
    assert benchmark_result.returncode in (0, 1), benchmark_result.stderr + benchmark_result.stdout

    ai = repo / ".ai"
    assert (ai / "scan-metadata.yaml").exists()
    assert (ai / "llm-scan-proposal.json").exists()
    assert report_path.exists(), benchmark_result.stderr + benchmark_result.stdout
    report = yaml.safe_load(report_path.read_text())
    assert report["profile"] == profile
    check_ids = {check["id"] for check in report["checks"]}
    assert "schema:scan-metadata" in check_ids
    assert "schema:llm-scan-proposal" in check_ids
    assert "schema:generation-trace" in check_ids
    assert "content:generation-trace" in check_ids
    if benchmark_result.returncode == 0:
        assert report["status"] == "passed"
    else:
        assert report["status"] == "failed"
        hard_gate_check = next(check for check in report["checks"] if check["id"] == "content:hard-gate-sensors-passed")
        assert hard_gate_check["passed"] is False
        assert hard_gate_check["failed_or_skipped"]
        assert hard_gate_check["failed_or_skipped"][0]["summary"]
    runs = sorted((ai / "runs").iterdir())
    assert runs
    trace = yaml.safe_load((runs[-1] / "trace.yaml").read_text())
    assert trace["command"] == "benchmark"
    assert trace["status"] in {"completed", "failed"}
    assert "benchmark" in trace["stages"]
    harness_map = yaml.safe_load((ai / "task-runs" / "demo-task-001" / "harness-map.yaml").read_text())
    assert harness_map["selected_workflow"] == expected_workflow


def test_real_repositories_init_run_and_benchmark_end_to_end():
    _assert_real_repo("RuoYi-Vue", "java-spring", "修复登录接口错误提示不一致的问题", "bugfix")
    _assert_real_repo("eShopOnWeb", "dotnet-aspnet", "调整 Catalog 相关低风险文案", "lightweight")
