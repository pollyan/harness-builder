from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import yaml

from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools import existing_harness_entry
from harness_builder_agent.tools import interactive_init
from harness_builder_agent.tools.existing_harness_entry import (
    ExistingHarnessStateLoadError,
    load_existing_harness_state,
)


def _write_minimal_harness(ai: Path) -> None:
    ai.mkdir(parents=True)
    (ai / "project-inventory.json").write_text(
        ProjectInventory(
            repo_name="demo",
            root_path="/tmp/demo",
            primary_stack="java-spring",
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )
    (ai / "harness-config.yaml").write_text(
        yaml.safe_dump(HarnessConfig.default().model_dump(mode="json"), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def test_existing_harness_entry_module_loads_valid_core_state(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_minimal_harness(ai)

    inventory, config, score = load_existing_harness_state(ai)

    assert inventory.repo_name == "demo"
    assert config.workflow_routing.default_workflow == "lightweight"
    assert score is None
    assert hasattr(existing_harness_entry, "handle_existing_harness_entry")


def test_existing_harness_entry_module_reports_invalid_config_source(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_minimal_harness(ai)
    (ai / "harness-config.yaml").write_text("workflows: [", encoding="utf-8")

    with pytest.raises(ExistingHarnessStateLoadError) as exc_info:
        load_existing_harness_state(ai)

    assert exc_info.value.source == ".ai/harness-config.yaml"
    assert exc_info.value.error_type
    assert exc_info.value.message


def test_interactive_init_delegates_existing_harness_entry_to_dedicated_module():
    source = inspect.getsource(interactive_init)

    assert "handle_existing_harness_entry as _handle_existing_harness_entry" in source
    assert "def _handle_existing_harness_entry" not in source
    assert interactive_init._handle_existing_harness_entry is existing_harness_entry.handle_existing_harness_entry
