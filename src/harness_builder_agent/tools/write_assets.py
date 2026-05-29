from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def write_initial_assets(repo: Path, inventory: ProjectInventory, commands: CommandCatalog) -> Path:
    ai = repo / ".ai"
    config = HarnessConfig.default()

    _write_json(ai / "project-inventory.json", inventory.model_dump(mode="json"))
    _write_yaml(ai / "command-catalog.yaml", commands.model_dump(mode="json"))
    _write_yaml(ai / "harness-config.yaml", config.model_dump(mode="json"))

    _write_text(ai / "scan-report.md", _scan_report(inventory, commands))
    _write_text(ai / "maturity-report.md", _maturity_report(inventory, commands))
    _write_text(ai / "evolution-plan.md", _evolution_plan())

    _write_text(ai / "guides" / "project-context.md", _guide("project-context", inventory))
    _write_text(ai / "guides" / "coding-rules.md", _guide("coding-rules", inventory))
    _write_text(ai / "guides" / "architecture.md", _guide("architecture", inventory))
    _write_text(ai / "guides" / "task-templates" / "bugfix.md", _task_template("bugfix"))
    _write_text(ai / "guides" / "task-templates" / "lightweight-feature.md", _task_template("lightweight"))

    _write_text(ai / "sensors" / "verification.md", _sensor_doc(commands))
    _write_text(ai / "sensors" / "test-strategy.md", _test_strategy(commands))
    _write_text(ai / "experience" / "pending-improvements.md", "# Pending Improvements\n\nNo reviewed improvements yet.\n")
    return ai


def _frontmatter(asset_type: str) -> str:
    return (
        "---\n"
        f"asset_type: {asset_type}\n"
        "status: candidate\n"
        "source: inferred_from_codebase\n"
        "confidence: medium\n"
        "needs_human_confirmation: true\n"
        "---\n\n"
    )


def _scan_report(inventory: ProjectInventory, commands: CommandCatalog) -> str:
    command_lines = "\n".join(f"- `{command.command}` from `{command.source}`" for command in commands.commands) or "- No commands detected"
    evidence_lines = "\n".join(f"- `{item['path']}`: {item['reason']}" for item in inventory.evidence) or "- No evidence detected"
    return (
        "# Scan Report\n\n"
        f"Repository: `{inventory.repo_name}`\n\n"
        f"Primary stack: `{inventory.primary_stack}`\n\n"
        "## Evidence\n\n"
        f"{evidence_lines}\n\n"
        "## Command Candidates\n\n"
        f"{command_lines}\n"
    )


def _maturity_report(inventory: ProjectInventory, commands: CommandCatalog) -> str:
    level = "L2" if commands.commands else "L1"
    return (
        "# Maturity Report\n\n"
        f"Overall level: `{level}`\n\n"
        "## Dimension Scores\n\n"
        "- Guides: L1\n"
        f"- Sensors: {'L2' if commands.commands else 'L0'}\n"
        "- Workflow: L1\n"
        "- Risk Control: L0\n"
        "- Observability: L1\n"
        "- Experience: L0\n\n"
        "## Recommended Next Steps\n\n"
        "- Confirm risk zones with a human maintainer.\n"
        "- Promote reliable unit tests to hard gate sensors.\n"
        "- Review generated guides before using them as active rules.\n"
    )


def _evolution_plan() -> str:
    return (
        "# Evolution Plan\n\n"
        "1. Confirm generated project context and architecture guides.\n"
        "2. Verify command candidates on a developer machine.\n"
        "3. Add task-specific sensors for repeated work patterns.\n"
    )


def _guide(name: str, inventory: ProjectInventory) -> str:
    module_lines = "\n".join(f"- `{module['path']}` ({module['kind']})" for module in inventory.modules) or "- No modules detected"
    return (
        _frontmatter("guide")
        + f"# {name}\n\n"
        + f"Repository `{inventory.repo_name}` is detected as `{inventory.primary_stack}`.\n\n"
        + "## Applicable Scope\n\n"
        + "Whole repository, pending maintainer review.\n\n"
        + "## Modules\n\n"
        + f"{module_lines}\n\n"
        + "## Uncertainty\n\n"
        + "Generated from shallow scan only. Human confirmation is required.\n"
    )


def _task_template(kind: str) -> str:
    title = "Bugfix Task Template" if kind == "bugfix" else "Lightweight Feature Task Template"
    return (
        _frontmatter("task_template")
        + f"# {title}\n\n"
        + "1. Restate the task and expected outcome.\n"
        + "2. Map affected modules and relevant guides.\n"
        + "3. Run selected hard gate sensors.\n"
        + "4. Produce decision log and handoff summary.\n"
    )


def _sensor_doc(commands: CommandCatalog) -> str:
    lines = "\n".join(f"- `{command.id}`: `{command.command}` ({command.gate})" for command in commands.commands) or "- No executable sensors detected"
    return "# Verification Sensors\n\n" + lines + "\n"


def _test_strategy(commands: CommandCatalog) -> str:
    hard_gates = [command for command in commands.commands if command.gate == "hard"]
    lines = "\n".join(f"- `{command.command}`" for command in hard_gates) or "- Confirm test strategy with maintainer"
    return "# Test Strategy\n\n## Hard Gates\n\n" + lines + "\n"
