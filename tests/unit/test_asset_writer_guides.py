from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibraryEntry, WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.guides import write_guide_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace


def _inventory(repo: Path) -> ProjectInventory:
    return ProjectInventory(
        repo_name=repo.name,
        root_path=str(repo),
        primary_stack="java-spring",
        stacks=["java", "maven", "spring-boot"],
        modules=[{"name": "app", "path": ".", "kind": "backend"}],
        evidence=[{"path": "pom.xml", "reason": "maven build file"}],
        stack_extensions={
            "risk_areas": [
                {"path": "src/main/resources/application.yml", "reason": "数据库配置需要人工确认"}
            ],
            "human_overrides": {"scan_notes": ["配置变更必须说明回滚方式"]},
        },
    )


def _commands() -> CommandCatalog:
    return CommandCatalog(
        commands=[
            CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml"),
        ]
    )


def _weapon_selection() -> WeaponLibrarySelection:
    guide = WeaponLibraryEntry(
        id="java-spring.guide.layering",
        stack="java-spring",
        kind="guide",
        title="Spring layering",
        guidance="Controller should delegate business logic to services.",
        recommended_action="Confirm package boundaries with maintainers.",
    )
    return WeaponLibrarySelection(
        primary_stack="java-spring",
        selected_stacks=["common", "java-spring"],
        guide_weapon_ids=[guide.id],
        sensor_weapon_ids=[],
        guide_weapons=[guide],
        sensor_weapons=[],
    )


def test_write_guide_assets_writes_guides_templates_and_records_trace(tmp_path: Path):
    ai = tmp_path / ".ai"
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    write_guide_assets(ai, _inventory(tmp_path), _commands(), _weapon_selection(), trace=trace)
    trace.finish("completed", {"primary_stack": "java-spring"})

    project_context = (ai / "guides" / "project-context.md").read_text(encoding="utf-8")
    bugfix_template = (ai / "guides" / "task-templates" / "bugfix.md").read_text(encoding="utf-8")
    lightweight_template = (ai / "guides" / "task-templates" / "lightweight-feature.md").read_text(encoding="utf-8")

    assert "## 当前项目事实" in project_context
    assert "## 风险区域" in project_context
    assert "## 验证入口" in project_context
    assert "## 成熟度缺口关联" in project_context
    assert "## 来源证据" in project_context
    assert "java-spring.guide." in project_context
    assert "src/main/resources/application.yml" in project_context
    assert "数据库配置需要人工确认" in project_context
    assert "mvn test" in project_context
    assert "配置变更必须说明回滚方式" in project_context
    assert "缺陷修复任务模板" in bugfix_template
    assert "轻量级任务模板" in lightweight_template

    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    assert {"path": ".ai/guides/project-context.md", "kind": "guide"} in artifacts["artifacts"]
    assert {
        "path": ".ai/guides/task-templates/lightweight-feature.md",
        "kind": "task_template",
    } in artifacts["artifacts"]
