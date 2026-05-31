from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibraryEntry, WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.sensors import write_sensor_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace


def _inventory(repo: Path) -> ProjectInventory:
    return ProjectInventory(
        repo_name=repo.name,
        root_path=str(repo),
        primary_stack="java-spring",
        stacks=["java", "maven"],
        modules=[{"name": "app", "path": "src/main/java", "kind": "backend"}],
        evidence=[{"path": "pom.xml", "reason": "maven build file"}],
        stack_extensions={
            "risk_areas": [
                {"path": "src/main/resources/application.yml", "reason": "数据库配置需要人工确认"}
            ]
        },
    )


def _commands() -> CommandCatalog:
    return CommandCatalog(
        commands=[
            CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml"),
        ]
    )


def _weapon_selection() -> WeaponLibrarySelection:
    sensor = WeaponLibraryEntry(
        id="common.sensor.unit-tests",
        stack="common",
        kind="sensor",
        title="Unit test gate",
        guidance="Run the stable unit test command before handoff.",
        recommended_action="Keep unit tests as a hard gate.",
        gate="hard",
    )
    return WeaponLibrarySelection(
        primary_stack="java-spring",
        selected_stacks=["common", "java-spring"],
        guide_weapon_ids=[],
        sensor_weapon_ids=[sensor.id],
        guide_weapons=[],
        sensor_weapons=[sensor],
    )


def test_write_sensor_assets_writes_sensor_docs_and_records_trace(tmp_path: Path):
    ai = tmp_path / ".ai"
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    write_sensor_assets(ai, _commands(), _weapon_selection(), inventory=_inventory(tmp_path), trace=trace)
    trace.finish("completed", {"primary_stack": "java-spring"})

    verification = (ai / "sensors" / "verification.md").read_text(encoding="utf-8")
    test_strategy = (ai / "sensors" / "test-strategy.md").read_text(encoding="utf-8")

    assert "## 已发现的验证命令" in verification
    assert "## 风险与验证映射" in verification
    assert "## 成熟度缺口关联" in verification
    assert "## 缺失验证能力" in verification
    assert "## 推荐验证活动" in verification
    assert "## 失败处理策略" in verification
    assert "src/main/resources/application.yml" in verification
    assert "数据库配置需要人工确认" in verification
    assert "mvn test" in verification
    assert "mvn test" in test_strategy

    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    assert {"path": ".ai/sensors/verification.md", "kind": "sensor"} in artifacts["artifacts"]
    assert {"path": ".ai/sensors/test-strategy.md", "kind": "sensor"} in artifacts["artifacts"]
