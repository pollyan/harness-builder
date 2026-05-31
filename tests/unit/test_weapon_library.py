from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.weapon_library import select_weapon_library


def _inventory(primary_stack: str) -> ProjectInventory:
    return ProjectInventory(repo_name="demo", root_path="/tmp/demo", primary_stack=primary_stack, stacks=[primary_stack])


def _commands(command: str = "pytest") -> CommandCatalog:
    return CommandCatalog(commands=[CommandDefinition(id="unit_test", command=command, type="test", gate="hard", source="build-file")])


def test_selects_common_and_java_spring_weapons():
    selection = select_weapon_library(_inventory("java-spring"), _commands("mvn test"))

    assert selection.source == "built_in_weapon_library"
    assert {"common", "java-spring"}.issubset(set(selection.selected_stacks))
    assert any(item.startswith("common.guide.") for item in selection.guide_weapon_ids)
    assert any(item.startswith("java-spring.guide.") for item in selection.guide_weapon_ids)
    assert any(item.startswith("common.sensor.") for item in selection.sensor_weapon_ids)
    assert any(item.startswith("java-spring.sensor.") for item in selection.sensor_weapon_ids)
    assert any("已发现 Maven 命令" in weapon.recommended_action for weapon in selection.sensor_weapons)


def test_selects_common_and_dotnet_weapons():
    selection = select_weapon_library(_inventory("dotnet-aspnet"), _commands("dotnet test"))

    assert {"common", "dotnet-aspnet"}.issubset(set(selection.selected_stacks))
    assert any(item.startswith("dotnet-aspnet.guide.") for item in selection.guide_weapon_ids)
    assert any(item.startswith("dotnet-aspnet.sensor.") for item in selection.sensor_weapon_ids)
    assert any("已发现 dotnet test" in weapon.recommended_action for weapon in selection.sensor_weapons)


def test_multistack_python_flask_react_selects_backend_and_frontend_weapons():
    inventory = ProjectInventory(
        repo_name="demo",
        root_path="/tmp/demo",
        primary_stack="python-flask",
        stacks=["python", "flask", "react", "typescript", "vite"],
        modules=[
            {"name": "api", "path": ".", "kind": "backend"},
            {"name": "web", "path": "frontend", "kind": "frontend"},
        ],
    )

    selection = select_weapon_library(inventory, _commands("pytest"))

    assert {"common", "python-flask", "node"}.issubset(set(selection.selected_stacks))
    assert any(item.startswith("python-flask.guide.") for item in selection.guide_weapon_ids)
    assert any(item.startswith("node.guide.") for item in selection.guide_weapon_ids)
    assert any(item.startswith("python-flask.sensor.") for item in selection.sensor_weapon_ids)
    assert any(item.startswith("node.sensor.") for item in selection.sensor_weapon_ids)
    assert any("已发现 pytest" in weapon.recommended_action for weapon in selection.sensor_weapons)


def test_unknown_stack_keeps_common_floor():
    selection = select_weapon_library(_inventory("unknown"), _commands())

    assert selection.primary_stack == "unknown"
    assert selection.selected_stacks == ["common"]
    assert selection.guide_weapon_ids
    assert selection.sensor_weapon_ids
    assert all(item.startswith("common.") for item in selection.guide_weapon_ids + selection.sensor_weapon_ids)
