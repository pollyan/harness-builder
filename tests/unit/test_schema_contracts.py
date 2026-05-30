from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory


def test_project_inventory_records_stack_modules_and_evidence():
    inventory = ProjectInventory(
        repo_name="mini-spring-boot",
        root_path="/tmp/mini-spring-boot",
        primary_stack="java-spring",
        stacks=["java", "spring-boot"],
        modules=[{"name": "app", "path": ".", "kind": "backend"}],
        evidence=[{"path": "pom.xml", "reason": "maven build file"}],
    )

    payload = inventory.model_dump()

    assert payload["schema_version"] == "1.0"
    assert payload["primary_stack"] == "java-spring"
    assert payload["modules"][0]["kind"] == "backend"
    assert payload["evidence"][0]["path"] == "pom.xml"


def test_command_catalog_requires_source_and_gate_metadata():
    catalog = CommandCatalog(
        commands=[
            {
                "id": "unit_test",
                "command": "mvn test",
                "type": "test",
                "gate": "hard",
                "source": "pom.xml",
                "confidence": "medium",
            }
        ]
    )

    payload = catalog.model_dump()

    assert payload["schema_version"] == "1.0"
    assert payload["commands"][0]["id"] == "unit_test"
    assert payload["commands"][0]["gate"] == "hard"


def test_harness_config_has_lightweight_and_bugfix_workflows():
    config = HarnessConfig.default()

    workflow_names = set(config.workflows.keys())

    assert {"lightweight", "bugfix"}.issubset(workflow_names)
    assert config.workflows["lightweight"].skill_path == ".ai/skills/lightweight/SKILL.md"
    assert config.workflows["bugfix"].skill_path == ".ai/skills/bugfix/SKILL.md"
    assert config.runtime.default_workflow == "lightweight"
    assert config.sensors.max_repair_attempts == 1
