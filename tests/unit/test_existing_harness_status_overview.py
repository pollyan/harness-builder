from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.tools.existing_harness_status import render_existing_harness_status_overview_lines
from harness_builder_agent.tools.maintenance_triage import MaintenanceAction


def _score() -> MaturityReport:
    return MaturityReport(
        overall_level="L2",
        target_next_level="L3",
        dimension_scores={"Experience": "L1"},
        blocking_reasons=["缺少运行证据闭环。"],
        recommended_next_steps=["运行 benchmark。"],
    )


def _benchmark_action() -> MaintenanceAction:
    return MaintenanceAction(
        priority=10,
        action="benchmark",
        reason="benchmark_not_run",
        source=".ai/benchmark-report.yaml",
        next_action="benchmark",
    )


def _write_benchmark(ai: Path, *, status: str = "passed", failed_count: int = 0) -> None:
    checks = [{"id": "schema:project-inventory", "passed": True}]
    for index in range(failed_count):
        checks.append({"id": f"content:guides-quality-{index}", "passed": False})
    (ai / "benchmark-report.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "repo_name": "demo",
                "profile": "java-spring",
                "status": status,
                "quality_status": "failed" if status == "failed" else "passed",
                "checks": checks,
                "quality_scores": {},
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_experience_index(
    ai: Path,
    *,
    pending: int = 0,
    asset_candidates: int = 0,
    governance: int = 0,
    workflow_recommendations: int = 0,
    runtime_task_runs: int = 0,
) -> None:
    experience = ai / "experience"
    experience.mkdir(parents=True, exist_ok=True)
    (experience / "experience-index.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "experience_files": {},
                "sources": [],
                "pending_improvement_count": pending,
                "asset_candidate_count": asset_candidates,
                "maturity_review_count": 0,
                "candidate_governance_decision_count": governance,
                "workflow_recommendation_count": workflow_recommendations,
                "runtime_task_run_count": runtime_task_runs,
                "warnings": [],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_questionnaire(ai: Path, count: int) -> None:
    (ai / "human-input-needed.md").write_text("# Human Input\n", encoding="utf-8")
    questions = []
    for index in range(count):
        questions.append(
            {
                "interaction_type": "scan_followup_confirmation",
                "interaction_id": f"confirm:scan-followup:item-{index}",
                "question": "真实测试入口是什么？",
                "options": ["补充", "保持待确认"],
                "confidence": "low",
                "reason": "缺少测试 evidence。",
                "response_status": "unaddressed",
                "response_sources": [],
            }
        )
    (ai / "questionnaire.yaml").write_text(
        yaml.safe_dump({"schema_version": "1.0", "questions": questions}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def test_existing_harness_status_overview_explains_not_run_benchmark_and_top_action(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()

    lines = render_existing_harness_status_overview_lines(ai, HarnessConfig.default(), _score(), [_benchmark_action()])

    assert "质量门禁：尚未运行 benchmark；建议先运行菜单 `4` 的 `benchmark` 建立质量基线。" in lines
    assert "Workflow 路由：default=`lightweight`，standard escalation 已启用，risk triggers=0，missing_hard_gate=absent。" in lines
    assert "Experience / review：experience-index 缺失；建议运行 `assess` 或 `improve` 刷新维护证据。" in lines
    assert "优先动作：输入 `4` 运行 `benchmark`（reason=benchmark_not_run，source=.ai/benchmark-report.yaml）。" in lines


def test_existing_harness_status_overview_summarizes_failed_benchmark_and_review_backlog(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_benchmark(ai, status="failed", failed_count=2)
    _write_experience_index(ai, pending=1, asset_candidates=3, governance=1, workflow_recommendations=2, runtime_task_runs=1)
    _write_questionnaire(ai, 2)

    lines = render_existing_harness_status_overview_lines(
        ai,
        HarnessConfig.default(),
        _score(),
        [
            MaintenanceAction(
                priority=20,
                action="review-candidate",
                reason="asset_candidates_pending",
                source=".ai/review/asset-candidates.yaml",
                next_action="review-candidate",
                count=2,
            )
        ],
    )

    assert "质量门禁：未通过，failed checks=2；先查看 `.ai/benchmark-report.yaml`。" in lines
    assert "Experience / review：2 个 asset candidates 待治理；1 个 pending improvement；2 条 workflow recommendation；human-input 待确认 2 项；runtime task-run 证据 1 条。" in lines
    assert "优先动作：输入 `6` 运行 `review-candidate`（reason=asset_candidates_pending，source=.ai/review/asset-candidates.yaml，count=2）。" in lines


def test_existing_harness_status_overview_explains_healthy_state_without_pending_work(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_benchmark(ai, status="passed")
    _write_experience_index(ai)

    lines = render_existing_harness_status_overview_lines(
        ai,
        HarnessConfig.default(),
        _score(),
        [
            MaintenanceAction(
                priority=90,
                action="recommend-workflow",
                reason="no_pending_maintenance_signal",
                source=".ai/harness-config.yaml",
                next_action="recommend-workflow",
            )
        ],
    )

    assert "质量门禁：已通过，quality=passed。" in lines
    assert "Experience / review：暂无待治理候选或 pending improvement；可按任务运行 `recommend-workflow` 收集路由证据。" in lines
    assert "优先动作：输入 `5` 运行 `recommend-workflow`（reason=no_pending_maintenance_signal，source=.ai/harness-config.yaml）。" in lines
