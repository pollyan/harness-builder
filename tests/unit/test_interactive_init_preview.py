from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.interaction_decision import WorkflowConfirmation
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibraryEntry
from harness_builder_agent.tools.prewrite_preview import (
    GuidedScanOverrides,
    show_prewrite_maturity_preview,
)
from harness_builder_agent.tools.interactive_init import (
    _benchmark_signal_lines,
    _human_input_needed_status_lines,
    _normalize_existing_harness_action,
    _workflow_routing_status_lines,
    _weapon_blocker_summary,
    _weapon_maturity_dimension_keys,
    _weapon_next_lift_summary,
)
from harness_builder_agent.tools.maturity_model import build_maturity_report


def test_prewrite_preview_renderer_shows_scan_supplement_constraints(tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    show_prewrite_maturity_preview(
        repo,
        ProjectInventory(repo_name="demo", root_path=str(repo), primary_stack="java-spring"),
        CommandCatalog(commands=[]),
        _weapon_selection(),
        GuidedScanOverrides(
            primary_stack="node",
            notes=["frontend 还包含批处理入口"],
            modules=[{"path": "frontend", "kind": "frontend", "name": "frontend"}],
            commands=[
                CommandDefinition(
                    id="frontend_test",
                    command="npm test",
                    type="test",
                    gate="hard",
                    source="frontend/package.json",
                    confidence="high",
                )
            ],
            risk_areas=[{"path": "frontend/package.json", "reason": "前端依赖需要单独确认"}],
        ),
        inline_contexts=["Controller 只能调用 Service"],
        workflow_confirmation=WorkflowConfirmation(notes=["bugfix 只用于缺陷修复"]),
    )

    output = capsys.readouterr().out

    assert "成熟度叙事主线" in output
    assert "当前等级：L0" in output
    assert "写入后基线：" in output
    assert "下一目标：" in output
    assert "扫描补充已更新本轮 inventory / command catalog / risk hints" in output
    assert "团队规则会进入 Guides 与 human-input-needed" in output
    assert "Workflow 补充会进入 review-only 交互决策" in output
    assert "仍需后续 benchmark 和 Runtime task-run 证据验证" in output
    assert output.index("推荐补齐动作") < output.index("成熟度叙事主线") < output.index("写入前 Harness 设计预览")
    assert "写入前 Harness 设计预览" in output
    assert "扫描补充约束" in output
    assert "技术栈修正：`node`" in output
    assert "自然语言补充：frontend 还包含批处理入口" in output
    assert "结构化模块：`frontend`（frontend，frontend）" in output
    assert "结构化验证命令：`npm test`，gate=hard，source=`frontend/package.json`" in output
    assert "结构化风险区域：`frontend/package.json`，前端依赖需要单独确认" in output
    assert "影响 project inventory、command catalog、risk hints、Guides、Sensors、Workflow 升级和人工确认" in output
    assert "不会被伪装成已验证扫描事实" in output


def test_prewrite_preview_renderer_shows_scan_baseline_when_no_supplement(tmp_path: Path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    show_prewrite_maturity_preview(
        repo,
        ProjectInventory(repo_name="demo", root_path=str(repo), primary_stack="java-spring"),
        CommandCatalog(commands=[]),
        _weapon_selection(),
    )

    output = capsys.readouterr().out

    assert "扫描补充约束" in output
    assert "暂无扫描补充；当前按扫描基线、团队规则和内置 Harness 基线生成" in output
    assert "成熟度叙事主线" in output
    assert "当前没有用户补充改变本轮预览" in output
    assert "自然语言补充" not in output


def _weapon_selection():
    from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection

    return WeaponLibrarySelection(
        primary_stack="common",
        selected_stacks=["common"],
        guide_weapons=[
            WeaponLibraryEntry(
                id="common.guide.change-risk",
                stack="common",
                kind="guide",
                title="变更风险分级",
                guidance="风险 Guide。",
                recommended_action="补充风险说明。",
                tags=["risk", "review"],
            )
        ],
        sensor_weapons=[
            WeaponLibraryEntry(
                id="common.sensor.hard-gate-policy",
                stack="common",
                kind="sensor",
                title="Hard gate 策略",
                guidance="验证 Sensor。",
                recommended_action="补充 hard gate。",
                gate="hard",
                tags=["verification", "hard-gate"],
            )
        ],
    )


def test_guide_weapon_links_to_guides_and_risk_control_blockers():
    weapon = WeaponLibraryEntry(
        id="common.guide.change-risk",
        stack="common",
        kind="guide",
        title="变更风险分级",
        guidance="风险 Guide。",
        recommended_action="补充风险说明。",
        tags=["risk", "review"],
    )
    planned = build_maturity_report(
        ai=None,
        inventory=ProjectInventory(
            repo_name="demo",
            root_path="/tmp/demo",
            primary_stack="java-spring",
            stack_extensions={"risk_areas": [{"path": "src/main/resources/application.yml", "reason": "配置风险"}]},
        ),
        commands=CommandCatalog(commands=[]),
        config=HarnessConfig.default(),
    )

    keys = _weapon_maturity_dimension_keys(weapon)

    assert keys == ["guides", "risk_control"]
    assert "guides-not-risk-routed" in _weapon_blocker_summary(keys, planned)
    assert "risk-zones-not-confirmed" in _weapon_blocker_summary(keys, planned)
    assert "绑定 Guides 到任务风险上下文" in _weapon_next_lift_summary(keys, planned)


def test_sensor_weapon_links_to_sensor_and_verification_blockers():
    weapon = WeaponLibraryEntry(
        id="common.sensor.hard-gate-policy",
        stack="common",
        kind="sensor",
        title="Hard gate 策略",
        guidance="验证 Sensor。",
        recommended_action="补充 hard gate。",
        gate="hard",
        tags=["verification", "hard-gate"],
    )
    planned = build_maturity_report(
        ai=None,
        inventory=ProjectInventory(repo_name="demo", root_path="/tmp/demo", primary_stack="java-spring"),
        commands=CommandCatalog(commands=[]),
        config=HarnessConfig.default(),
    )

    keys = _weapon_maturity_dimension_keys(weapon)

    assert keys == ["sensors", "verification_sophistication"]
    assert "no-executable-sensors" in _weapon_blocker_summary(keys, planned)
    assert "verification-not-mapped-to-task-risk" in _weapon_blocker_summary(keys, planned)
    assert "建立可执行 Sensor 基线" in _weapon_next_lift_summary(keys, planned)


def test_existing_harness_action_normalization_accepts_numbers_and_aliases():
    assert _normalize_existing_harness_action("1") == "exit"
    assert _normalize_existing_harness_action("2") == "assess"
    assert _normalize_existing_harness_action("3") == "improve"
    assert _normalize_existing_harness_action("4") == "benchmark"
    assert _normalize_existing_harness_action("5") == "recommend-workflow"
    assert _normalize_existing_harness_action("6") == "review-candidate"
    assert _normalize_existing_harness_action("7") == "review-human-input"
    assert _normalize_existing_harness_action("8") == "self-improve"
    assert _normalize_existing_harness_action("9") == "reinit"
    assert _normalize_existing_harness_action("quit") == "exit"
    assert _normalize_existing_harness_action("质量") == "benchmark"
    assert _normalize_existing_harness_action("治理") == "review-candidate"
    assert _normalize_existing_harness_action("human-input") == "review-human-input"
    assert _normalize_existing_harness_action("人工输入") == "review-human-input"
    assert _normalize_existing_harness_action("待确认") == "review-human-input"
    assert _normalize_existing_harness_action("重新生成") == "reinit"
    assert _normalize_existing_harness_action("unknown") == "unknown"


def test_workflow_routing_status_lines_show_standard_risk_context():
    config = HarnessConfig.default()
    standard = next(rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation")
    standard.triggers.extend(
        [
            "risk_area:security_or_permission",
            "risk_area:data_or_migration",
            "missing_hard_gate",
        ]
    )
    lines = _workflow_routing_status_lines(config)

    assert "routing_default=lightweight" in lines
    assert "routing_rule_count=3" in lines
    assert "standard_escalation=present" in lines
    assert "standard_human_confirmation=true" in lines
    assert "standard_risk_triggers=2" in lines
    assert "risk_trigger=risk_area:security_or_permission" in lines
    assert "risk_trigger=risk_area:data_or_migration" in lines
    assert "missing_hard_gate_trigger=present" in lines


def test_benchmark_signal_lines_preview_failed_checks_with_action_details(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    (ai / "benchmark-report.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "repo_name": "demo",
                "profile": "java-spring",
                "status": "failed",
                "quality_status": "failed",
                "checks": [
                    {"id": "schema:project-inventory", "passed": True},
                    {
                        "id": "content:hard-gate-command-evidence",
                        "passed": False,
                        "errors": ["hard_gate_without_source"],
                        "missing": ["source_path"],
                        "weak_commands": [
                            {
                                "id": "unit_test",
                                "source": "docs/testing.md",
                                "confidence": "low",
                                "reason": "source_path_missing",
                            }
                        ],
                    },
                    {
                        "id": "content:project-context-evidence-context",
                        "passed": False,
                        "missing": ["llm_requested_evidence_summary"],
                    },
                ],
                "quality_scores": {},
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    lines = _benchmark_signal_lines(ai)

    assert "benchmark_failed_checks=2" in lines
    assert "benchmark_failed_check=content:hard-gate-command-evidence" in lines
    assert (
        "benchmark_failed_check_detail=content:hard-gate-command-evidence|hard gate 命令证据不足"
        in lines
    )
    assert (
        "benchmark_failed_check_error=content:hard-gate-command-evidence|"
        "hard_gate_without_source；source_path；unit_test:source_path_missing:docs/testing.md"
        in lines
    )
    assert (
        "benchmark_failed_check_error=content:project-context-evidence-context|llm_requested_evidence_summary"
        in lines
    )


def test_benchmark_signal_lines_label_scan_evidence_failed_checks(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
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
                        "id": "content:scan-report",
                        "passed": False,
                        "missing": ["missing_coverage_selected_path:src/test/java/AppTest.java"],
                    },
                    {
                        "id": "content:init-summary",
                        "passed": False,
                        "missing": ["missing_summary_expansion_rationale"],
                    },
                ],
                "quality_scores": {},
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    lines = _benchmark_signal_lines(ai)

    assert "benchmark_failed_checks=2" in lines
    assert (
        "benchmark_failed_check_detail=content:scan-report|scan-report 缺少扫描证据审计细节"
        in lines
    )
    assert (
        "benchmark_failed_check_detail=content:init-summary|init-summary 缺少扫描证据审计摘要"
        in lines
    )
    assert (
        "benchmark_failed_check_error=content:scan-report|missing_coverage_selected_path:src/test/java/AppTest.java"
        in lines
    )
    assert "benchmark_failed_check_error=content:init-summary|missing_summary_expansion_rationale" in lines


def test_benchmark_signal_lines_report_missing_when_absent(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()

    assert _benchmark_signal_lines(ai) == ["benchmark_failed_checks=not_available"]


def test_human_input_needed_status_lines_summarize_questionnaire(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()
    (ai / "human-input-needed.md").write_text("# Human Input Needed\n\n## 处理方式\n", encoding="utf-8")
    (ai / "questionnaire.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "questions": [
                    {
                        "interaction_type": "scan_warning_confirmation",
                        "interaction_id": "confirm:scan-warning:test_evidence_not_found",
                        "question": "是否需要处理扫描警告？",
                        "options": ["接受当前降级处理"],
                        "confidence": "low",
                        "reason": "No dedicated test evidence bucket was found.",
                    },
                    {
                        "interaction_type": "risk_area_confirmation",
                        "interaction_id": "confirm:high-risk:src-main-resources-application-yml",
                        "question": "是否确认高风险边界？",
                        "options": ["保持待确认"],
                        "confidence": "low",
                        "reason": "配置变更风险。",
                    },
                    {
                        "interaction_type": "context_confirmation",
                        "interaction_id": "confirm:team-context",
                        "question": "是否补充团队规范？",
                        "options": ["提供 context"],
                        "confidence": "low",
                        "reason": "当前 init 未收到外部团队上下文。",
                    },
                    {
                        "interaction_type": "scan_followup_confirmation",
                        "interaction_id": "confirm:scan-followup:reviewed",
                        "question": "已复核的问题？",
                        "options": ["补充 module"],
                        "confidence": "low",
                        "reason": "已人工复核。",
                        "response_status": "reviewed_resolved_by_harness_maintainer",
                        "response_sources": ["command=unit_test:mvn test"],
                    },
                    {
                        "interaction_type": "scan_followup_confirmation",
                        "interaction_id": "confirm:scan-followup:test-evidence",
                        "question": "测试入口在哪里？",
                        "options": ["补充 command"],
                        "confidence": "low",
                        "reason": "扫描未找到测试 evidence。",
                        "response_status": "partially_addressed_by_current_scan_supplement",
                        "response_sources": ["command=unit_test:mvn test"],
                    },
                    {
                        "interaction_type": "scan_followup_confirmation",
                        "interaction_id": "confirm:scan-followup:module-boundary",
                        "question": "主要模块是什么？",
                        "options": ["补充 module"],
                        "confidence": "low",
                        "reason": "模块边界不清。",
                    },
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    lines = _human_input_needed_status_lines(ai)

    assert lines == [
        "human_input_needed=present",
        "human_input_questionnaire=present",
        "human_input_confirmations=6",
        "human_input_scan_confirmations=5",
        "human_input_scan_followups_resolved=1",
        "human_input_scan_followups_partially_addressed=1",
        "human_input_scan_followups_unaddressed=1",
        "human_input_first=confirm:scan-warning:test_evidence_not_found",
        "human_input_first=confirm:high-risk:src-main-resources-application-yml",
        "human_input_first=confirm:team-context",
        "human_input_omitted=3",
        "human_input_action_entry=.ai/human-input-needed.md#处理方式",
    ]


def test_human_input_needed_status_lines_report_missing_files(tmp_path: Path):
    ai = tmp_path / ".ai"
    ai.mkdir()

    assert _human_input_needed_status_lines(ai) == ["human_input_needed=missing"]

    (ai / "human-input-needed.md").write_text("# Human Input Needed\n", encoding="utf-8")

    assert _human_input_needed_status_lines(ai) == [
        "human_input_needed=present",
        "human_input_questionnaire=missing",
        "human_input_action_entry=.ai/human-input-needed.md#处理方式",
    ]
