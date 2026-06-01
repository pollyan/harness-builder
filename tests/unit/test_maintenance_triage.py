from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.tools.maintenance_triage import (
    MaintenanceAction,
    build_maintenance_triage,
    render_maintenance_triage_menu_hint_lines,
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


def _write_questionnaire(ai: Path, questions: list[dict[str, object]]) -> None:
    (ai / "questionnaire.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "questions": questions,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def _write_weapon_library_candidates(ai: Path) -> None:
    (ai / "experience").mkdir(parents=True, exist_ok=True)
    (ai / "experience" / "weapon-library-candidates.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_scan_proposal",
                "candidates": [
                    {
                        "id": "llm-guide-risk-001",
                        "candidate_type": "guide",
                        "status": "candidate",
                        "title": "支付风险 Guide",
                        "rationale": "支付模块需要额外上下文。",
                        "evidence": ["src/payments/CheckoutService.java"],
                        "human_confirmation_required": True,
                        "maturity_dimensions": ["guides", "risk_control"],
                        "maturity_impact_summary": "补齐 Guides 上下文、Risk Control 风险控制。",
                        "next_stage_contribution": "把风险区域留给 Maintainer 审查。",
                        "review_boundary": "review_only_no_formal_asset_change",
                    },
                    {
                        "id": "llm-sensor-command-001",
                        "candidate_type": "sensor",
                        "status": "rejected",
                        "title": "测试命令 Sensor",
                        "rationale": "已有验证命令。",
                        "evidence": ["pom.xml"],
                        "human_confirmation_required": False,
                        "maturity_dimensions": ["sensors", "verification_sophistication"],
                        "maturity_impact_summary": "补齐 Sensors 验证。",
                        "next_stage_contribution": "保留验证审查线索。",
                        "review_boundary": "review_only_no_formal_asset_change",
                    },
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def _scan_followup_question(interaction_id: str, response_status: str) -> dict[str, object]:
    return {
        "interaction_type": "scan_followup_confirmation",
        "interaction_id": interaction_id,
        "question": "真实测试入口是什么？",
        "options": ["补充验证命令", "保持待确认"],
        "confidence": "low",
        "reason": "缺少测试 evidence。",
        "response_status": response_status,
        "response_sources": ["command=unit_test:mvn test"]
        if response_status == "partially_addressed_by_current_scan_supplement"
        else [],
    }


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


def test_maintenance_triage_recommends_human_input_review_for_pending_scan_followups(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_benchmark(ai)
    _write_experience_index(ai)
    _write_questionnaire(
        ai,
        [
            _scan_followup_question(
                "confirm:scan-followup:test-evidence",
                "partially_addressed_by_current_scan_supplement",
            ),
            _scan_followup_question("confirm:scan-followup:module-boundary", "unaddressed"),
            _scan_followup_question(
                "confirm:scan-followup:resolved",
                "reviewed_resolved_by_harness_maintainer",
            ),
        ],
    )

    actions = build_maintenance_triage(ai, score=_score())
    lines = render_maintenance_triage_lines(actions)
    guidance = render_maintenance_triage_guidance_lines(actions)

    assert len(actions) == 1
    assert actions[0].action == "review-human-input"
    assert actions[0].reason == "human_input_scan_followups_pending"
    assert actions[0].source == ".ai/questionnaire.yaml"
    assert actions[0].count == 2
    assert actions[0].detail == "confirm:scan-followup:test-evidence"
    assert "top_action_1=review-human-input" in lines[0]
    assert "reason=human_input_scan_followups_pending" in lines[0]
    assert "source=.ai/questionnaire.yaml" in lines[0]
    assert "count=2" in lines[0]
    assert "detail=confirm:scan-followup:test-evidence" in lines[0]
    assert "运行 `review-human-input`" in guidance[0]
    assert "resolved / reopened" in guidance[0]


def test_maintenance_triage_menu_hints_map_actions_to_existing_harness_numbers():
    actions = [
        MaintenanceAction(
            priority=10,
            action="benchmark",
            reason="benchmark_not_run",
            source=".ai/benchmark-report.yaml",
            next_action="benchmark",
        ),
        MaintenanceAction(
            priority=25,
            action="review-human-input",
            reason="human_input_scan_followups_pending",
            source=".ai/questionnaire.yaml",
            next_action="review-human-input",
            count=2,
            detail="confirm:scan-followup:test-evidence",
        ),
        MaintenanceAction(
            priority=90,
            action="recommend-workflow",
            reason="no_pending_maintenance_signal",
            source=".ai/harness-config.yaml",
            next_action="recommend-workflow",
        ),
    ]

    lines = render_maintenance_triage_menu_hint_lines(actions)

    assert lines == [
        "建议优先选择 1：输入 `4` 运行 `benchmark`（reason=benchmark_not_run，source=.ai/benchmark-report.yaml）。",
        "建议优先选择 2：输入 `7` 运行 `review-human-input`（reason=human_input_scan_followups_pending，source=.ai/questionnaire.yaml，count=2，detail=confirm:scan-followup:test-evidence）。",
        "建议优先选择 3：输入 `5` 运行 `recommend-workflow`（reason=no_pending_maintenance_signal，source=.ai/harness-config.yaml）。",
    ]


def test_maintenance_triage_menu_hints_do_not_invent_numbers_for_unknown_actions():
    lines = render_maintenance_triage_menu_hint_lines(
        [
            MaintenanceAction(
                priority=1,
                action="custom-action",
                reason="custom_reason",
                source=".ai/custom.yaml",
                next_action="custom-action",
            )
        ]
    )

    assert lines == [
        "建议优先选择 1：`custom-action` 当前没有维护菜单编号；请使用对应专家命令处理 `custom_reason`（source=.ai/custom.yaml）。"
    ]


def test_maintenance_triage_keeps_benchmark_before_human_input_review(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_experience_index(ai)
    _write_questionnaire(
        ai,
        [_scan_followup_question("confirm:scan-followup:test-evidence", "unaddressed")],
    )

    actions = build_maintenance_triage(ai, score=_score())

    assert [action.action for action in actions[:2]] == ["benchmark", "review-human-input"]
    assert actions[1].reason == "human_input_scan_followups_pending"


def test_maintenance_triage_keeps_candidate_governance_before_human_input_review(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_benchmark(ai)
    _write_experience_index(ai, asset_candidates=3, governance=1)
    _write_questionnaire(
        ai,
        [_scan_followup_question("confirm:scan-followup:test-evidence", "unaddressed")],
    )

    actions = build_maintenance_triage(ai, score=_score())

    assert [action.action for action in actions[:2]] == ["review-candidate", "review-human-input"]
    assert actions[0].reason == "asset_candidates_pending"
    assert actions[1].reason == "human_input_scan_followups_pending"


def test_maintenance_triage_surfaces_pending_initial_candidate_maturity_impact(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_benchmark(ai)
    _write_experience_index(ai)
    _write_weapon_library_candidates(ai)

    actions = build_maintenance_triage(ai, score=_score())
    lines = render_maintenance_triage_lines(actions)
    guidance = render_maintenance_triage_guidance_lines(actions)
    menu_hints = render_maintenance_triage_menu_hint_lines(actions)

    assert actions[0].action == "manual-review"
    assert actions[0].reason == "weapon_library_candidates_pending"
    assert actions[0].source == ".ai/experience/weapon-library-candidates.yaml"
    assert actions[0].count == 1
    assert actions[0].detail == "llm-guide-risk-001:guides,risk_control"
    assert "reason=weapon_library_candidates_pending" in lines[0]
    assert "detail=llm-guide-risk-001:guides,risk_control" in lines[0]
    assert "查看 `.ai/review/llm-enhancement-candidates.md`" in guidance[0]
    assert "review-only" in guidance[0]
    assert "当前没有维护菜单编号" in menu_hints[0]


def test_maintenance_triage_ignores_resolved_scan_followups(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_benchmark(ai)
    _write_experience_index(ai)
    _write_questionnaire(
        ai,
        [
            _scan_followup_question(
                "confirm:scan-followup:resolved",
                "reviewed_resolved_by_harness_maintainer",
            )
        ],
    )

    actions = build_maintenance_triage(ai, score=_score())

    assert actions[0].action == "recommend-workflow"
    assert actions[0].reason == "no_pending_maintenance_signal"


def test_maintenance_triage_recommends_real_task_when_no_pending_signals(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_benchmark(ai)
    _write_experience_index(ai)

    actions = build_maintenance_triage(ai, score=_score())

    assert len(actions) == 1
    assert actions[0].action == "recommend-workflow"
    assert actions[0].reason == "no_pending_maintenance_signal"


def test_maintenance_triage_prioritizes_hard_gate_command_evidence_detail(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_experience_index(ai, asset_candidates=3, governance=1)
    (ai / "benchmark-report.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "repo_name": "demo",
                "profile": "java-spring",
                "status": "failed",
                "quality_status": "failed",
                "checks": [
                    {
                        "id": "content:hard-gate-command-evidence",
                        "passed": False,
                        "weak_commands": [
                            {
                                "id": "unit_test",
                                "source": "docs/testing.md",
                                "confidence": "low",
                                "reason": "source_path_missing",
                            }
                        ],
                    }
                ],
                "quality_scores": {},
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    actions = build_maintenance_triage(ai, score=_score())
    lines = render_maintenance_triage_lines(actions)
    guidance = render_maintenance_triage_guidance_lines(actions)

    assert actions[0].reason == "hard_gate_command_evidence"
    assert actions[0].detail == "unit_test:source_path_missing:docs/testing.md"
    assert "source=.ai/benchmark-report.yaml#content:hard-gate-command-evidence:unit_test" in lines[0]
    assert "detail=unit_test:source_path_missing:docs/testing.md" in lines[0]
    assert "先修正 hard gate 命令的 source、confidence 或 gate 证据" in guidance[0]


def test_maintenance_triage_prioritizes_project_context_evidence_missing_detail(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_experience_index(ai)
    (ai / "benchmark-report.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "repo_name": "demo",
                "profile": "java-spring",
                "status": "failed",
                "quality_status": "failed",
                "checks": [
                    {
                        "id": "content:project-context-evidence-context",
                        "passed": False,
                        "missing": ["llm_requested_evidence_summary"],
                    }
                ],
                "quality_scores": {},
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    actions = build_maintenance_triage(ai, score=_score())
    lines = render_maintenance_triage_lines(actions)
    guidance = render_maintenance_triage_guidance_lines(actions)

    assert actions[0].reason == "project_context_evidence_incomplete"
    assert actions[0].detail == "llm_requested_evidence_summary"
    assert "source=.ai/benchmark-report.yaml#content:project-context-evidence-context" in lines[0]
    assert "detail=llm_requested_evidence_summary" in lines[0]
    assert "补齐 project-context evidence 后运行 `benchmark`" in guidance[0]


def test_maintenance_triage_prioritizes_scan_evidence_audit_missing_detail(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    _write_experience_index(ai)
    (ai / "benchmark-report.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "repo_name": "demo",
                "profile": "java-spring",
                "status": "failed",
                "quality_status": "failed",
                "checks": [
                    {
                        "id": "content:init-summary",
                        "passed": False,
                        "missing": ["missing_summary_expansion_rationale"],
                    }
                ],
                "quality_scores": {},
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    actions = build_maintenance_triage(ai, score=_score())
    lines = render_maintenance_triage_lines(actions)
    guidance = render_maintenance_triage_guidance_lines(actions)

    assert actions[0].reason == "scan_evidence_audit_incomplete"
    assert actions[0].detail == "missing_summary_expansion_rationale"
    assert "source=.ai/benchmark-report.yaml#content:init-summary" in lines[0]
    assert "detail=missing_summary_expansion_rationale" in lines[0]
    assert "补齐 scan-report / init-summary 的扫描证据审计后运行 `benchmark`" in guidance[0]


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
