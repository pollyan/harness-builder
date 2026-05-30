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


def _assert_real_repo(repo_name: str, profile: str) -> None:
    repo = BENCHMARKS / repo_name
    assert repo.exists(), f"Missing real benchmark repository: {repo}"
    report_path = repo / ".ai" / "benchmark-report.yaml"
    report_path.unlink(missing_ok=True)

    init_result = _run_cli("init", "--repo", str(repo), "--non-interactive")
    assert init_result.returncode == 0, init_result.stderr + init_result.stdout

    assess_result = _run_cli("assess", "--repo", str(repo))
    assert assess_result.returncode == 0, assess_result.stderr + assess_result.stdout

    improve_result = _run_cli("improve", "--repo", str(repo))
    assert improve_result.returncode == 0, improve_result.stderr + improve_result.stdout

    benchmark_result = _run_cli("benchmark", "--repo", str(repo), "--profile", profile)
    assert benchmark_result.returncode in (0, 1), benchmark_result.stderr + benchmark_result.stdout

    ai = repo / ".ai"
    assert (ai / "scan-metadata.yaml").exists()
    assert (ai / "llm-scan-proposal.json").exists()
    assert (ai / "skills" / "lightweight" / "SKILL.md").exists()
    assert (ai / "skills" / "bugfix" / "SKILL.md").exists()
    assert not (ai / "task-runs").exists()
    assert report_path.exists(), benchmark_result.stderr + benchmark_result.stdout
    report = yaml.safe_load(report_path.read_text())
    assert report["profile"] == profile
    check_ids = {check["id"] for check in report["checks"]}
    assert "schema:scan-metadata" in check_ids
    assert "schema:llm-scan-proposal" in check_ids
    assert "schema:generation-trace" in check_ids
    assert "content:generation-trace" in check_ids
    assert "content:hard-gate-command-evidence" in check_ids
    assert "content:runtime-workflow-trace" not in check_ids
    if benchmark_result.returncode == 0:
        assert report["status"] == "passed"
    else:
        assert report["status"] == "failed"
        hard_gate_check = next(check for check in report["checks"] if check["id"] == "content:hard-gate-command-evidence")
        assert hard_gate_check["passed"] is False
        assert hard_gate_check["weak_commands"] or hard_gate_check["hard_gate_count"] == 0
    runs = sorted((ai / "runs").iterdir())
    assert runs
    trace = yaml.safe_load((runs[-1] / "trace.yaml").read_text())
    assert trace["command"] == "benchmark"
    assert trace["status"] in {"completed", "failed"}
    assert "benchmark" in trace["stages"]


def test_real_repositories_init_and_benchmark_end_to_end():
    _assert_real_repo("RuoYi-Vue", "java-spring")
    _assert_real_repo("eShopOnWeb", "dotnet-aspnet")
