from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.tools.maintenance_triage import (
    build_maintenance_triage,
    render_maintenance_triage_guidance_lines,
    render_maintenance_triage_lines,
)


def _score() -> MaturityReport:
    return MaturityReport(
        overall_level="L2",
        target_next_level="L3",
        dimension_scores={"Experience": "L1"},
        blocking_reasons=["缺少经验治理闭环。"],
        recommended_next_steps=["处理候选并运行 benchmark。"],
    )


def _write_experience_index(
    ai: Path,
    *,
    pending: int = 0,
    asset_candidates: int = 0,
    governance: int = 0,
    workflow_recommendations: int = 0,
) -> None:
    experience = ai / "experience"
    experience.mkdir(parents=True, exist_ok=True)
    sources = [{"path": ".ai/experience/pending-improvements.md", "kind": "pending_improvements", "item_count": pending}]
    if asset_candidates:
        sources.append({"path": ".ai/review/asset-candidates.yaml", "kind": "asset_candidates", "item_count": asset_candidates})
    if governance:
        sources.append({"path": ".ai/review/candidate-governance.yaml", "kind": "candidate_governance", "item_count": governance})
    if workflow_recommendations:
        sources.append(
            {
                "path": ".ai/review/workflow-routing-recommendations/index.yaml",
                "kind": "workflow_recommendation",
                "item_count": workflow_recommendations,
            }
        )
    (experience / "experience-index.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "experience_files": {},
                "sources": sources,
                "pending_improvement_count": pending,
                "asset_candidate_count": asset_candidates,
                "maturity_review_count": 0,
                "candidate_governance_decision_count": governance,
                "workflow_recommendation_count": workflow_recommendations,
                "runtime_task_run_count": 0,
                "warnings": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def _write_benchmark(ai: Path, *, status: str = "passed", schema_content_failures: int = 0) -> None:
    checks = [{"id": "schema:project-inventory", "passed": True}]
    for index in range(schema_content_failures):
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
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def test_maintenance_triage_prioritizes_contract_health_before_candidate_work(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_benchmark(ai, status="failed", schema_content_failures=2)
    _write_experience_index(ai, asset_candidates=3, governance=1, workflow_recommendations=2)

    actions = build_maintenance_triage(ai, score=_score())
    lines = render_maintenance_triage_lines(actions)

    assert [action.action for action in actions[:3]] == ["benchmark", "review-candidate", "improve"]
    assert "top_action_1=benchmark" in lines[0]
    assert "reason=schema_content_failed_checks" in lines[0]
    assert "count=2" in lines[0]
    assert "top_action_2=review-candidate" in lines[1]
    assert "reason=asset_candidates_pending" in lines[1]
    assert "top_action_3=improve" in lines[2]
    assert "reason=workflow_recommendations_pending" in lines[2]


def test_maintenance_triage_recommends_benchmark_when_report_missing(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_experience_index(ai)

    actions = build_maintenance_triage(ai, score=_score())

    assert actions[0].action == "benchmark"
    assert actions[0].reason == "benchmark_not_run"
    assert actions[0].source == ".ai/benchmark-report.yaml"


def test_maintenance_triage_recommends_real_task_when_no_pending_signals(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_benchmark(ai)
    _write_experience_index(ai)

    actions = build_maintenance_triage(ai, score=_score())

    assert len(actions) == 1
    assert actions[0].action == "recommend-workflow"
    assert actions[0].reason == "no_pending_maintenance_signal"


def test_maintenance_triage_guidance_explains_next_actions(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_experience_index(ai, asset_candidates=3, governance=1)

    actions = build_maintenance_triage(ai, score=_score())
    lines = render_maintenance_triage_guidance_lines(actions)

    assert lines[0] == "建议处理 1：先运行 `benchmark` 生成质量门禁报告，再回到 guided `init` 查看 Benchmark signals。"
    assert "运行 `review-candidate` 处理 2 个 review-only 候选" in lines[1]

    _write_benchmark(ai)
    _write_experience_index(ai)

    lines = render_maintenance_triage_guidance_lines(build_maintenance_triage(ai, score=_score()))

    assert lines == [
        "建议处理 1：输入一个真实任务说明，运行 `recommend-workflow` 生成 review-only Workflow 推荐；Builder 不执行 Runtime。"
    ]
