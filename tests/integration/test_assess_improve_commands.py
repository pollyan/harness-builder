from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _prepared_task_repo(tmp_path: Path, fixture_name: str) -> Path:
    repo = tmp_path / fixture_name
    shutil.copytree(FIXTURES / fixture_name, repo)
    runner = CliRunner()
    init_result = runner.invoke(app, ["init", "--repo", str(repo)])
    assert init_result.exit_code == 0, init_result.output
    run_result = runner.invoke(app, ["run", "--repo", str(repo), "修复登录接口错误提示不一致的问题"])
    assert run_result.exit_code == 0, run_result.output
    return repo


def test_assess_generates_maturity_score_from_current_harness(tmp_path: Path):
    repo = _prepared_task_repo(tmp_path, "mini-spring-boot")

    result = CliRunner().invoke(app, ["assess", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    score = yaml.safe_load((repo / ".ai" / "maturity-score.yaml").read_text(encoding="utf-8"))
    report = (repo / ".ai" / "maturity-report.md").read_text(encoding="utf-8")
    assert score["schema_version"] == "1.0"
    assert score["overall_level"].startswith("L")
    assert "workflow" in score["dimension_scores"]
    assert score["evidence"]
    assert score["blocking_reasons"]
    assert score["recommended_next_steps"]
    assert "## 证据" in report


def test_improve_generates_reviewable_improvement_candidates(tmp_path: Path):
    repo = _prepared_task_repo(tmp_path, "mini-dotnet-webapi")
    runner = CliRunner()
    assess_result = runner.invoke(app, ["assess", "--repo", str(repo)])
    assert assess_result.exit_code == 0, assess_result.output

    result = runner.invoke(app, ["improve", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    candidates = yaml.safe_load((repo / ".ai" / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    pending = (repo / ".ai" / "experience" / "pending-improvements.md").read_text(encoding="utf-8")
    evolution = (repo / ".ai" / "evolution-plan.md").read_text(encoding="utf-8")
    assert candidates["schema_version"] == "1.0"
    assert candidates["candidates"]
    first = candidates["candidates"][0]
    assert first["candidate_type"] in {"guide_update", "sensor_update", "workflow_policy_update", "maturity_action"}
    assert first["suggested_target"].startswith(".ai/")
    assert first["human_confirmation_required"] is True
    assert "## 待确认改进候选" in pending
    assert "## 优先级路线图" in evolution
