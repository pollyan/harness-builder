from __future__ import annotations

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibraryEntry
from harness_builder_agent.tools.interactive_init import (
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
