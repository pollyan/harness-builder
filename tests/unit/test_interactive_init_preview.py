from __future__ import annotations

from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibraryEntry
from harness_builder_agent.tools.interactive_init import (
    _human_input_needed_status_lines,
    _normalize_existing_harness_action,
    _weapon_blocker_summary,
    _weapon_maturity_dimension_keys,
    _weapon_next_lift_summary,
)
from harness_builder_agent.tools.maturity_model import build_maturity_report


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
    assert _normalize_existing_harness_action("7") == "self-improve"
    assert _normalize_existing_harness_action("8") == "reinit"
    assert _normalize_existing_harness_action("quit") == "exit"
    assert _normalize_existing_harness_action("质量") == "benchmark"
    assert _normalize_existing_harness_action("治理") == "review-candidate"
    assert _normalize_existing_harness_action("重新生成") == "reinit"
    assert _normalize_existing_harness_action("unknown") == "unknown"


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
                        "interaction_id": "confirm:scan-followup:test-evidence",
                        "question": "测试入口在哪里？",
                        "options": ["补充 command"],
                        "confidence": "low",
                        "reason": "扫描未找到测试 evidence。",
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
        "human_input_confirmations=4",
        "human_input_scan_confirmations=3",
        "human_input_first=confirm:scan-warning:test_evidence_not_found",
        "human_input_first=confirm:high-risk:src-main-resources-application-yml",
        "human_input_first=confirm:team-context",
        "human_input_omitted=1",
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
