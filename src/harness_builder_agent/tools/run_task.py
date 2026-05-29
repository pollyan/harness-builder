from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_map import HarnessMap
from harness_builder_agent.tools.run_sensor import run_sensor
from harness_builder_agent.tools.scan_repo import scan_repository
from harness_builder_agent.tools.write_assets import write_initial_assets

BUGFIX_TERMS = ("修复", "错误", "bug", "fix", "error", "failed", "failure")


def run_task(repo: Path, task: str, task_id: str = "demo-task-001") -> Path:
    root = repo.resolve()
    ai = root / ".ai"
    if not (ai / "project-inventory.json").exists() or not (ai / "command-catalog.yaml").exists():
        inventory, commands = scan_repository(root)
        write_initial_assets(root, inventory, commands)

    commands = CommandCatalog.model_validate(yaml.safe_load((ai / "command-catalog.yaml").read_text(encoding="utf-8")))
    task_type = _task_type(task)
    hard_gates = [command.id for command in commands.commands if command.gate == "hard"]
    harness_map = HarnessMap(
        task_id=task_id,
        task_type=task_type,
        selected_workflow="bugfix" if task_type == "bugfix" else "lightweight",
        risk_level="low",
        confidence={
            "requirement_clarity": "medium",
            "code_mapping": "medium",
            "sensor_coverage": "medium" if hard_gates else "low",
        },
        relevant_modules=["."],
        guide_policy={
            "required": [
                ".ai/guides/project-context.md",
                ".ai/guides/architecture.md",
                f".ai/guides/task-templates/{'bugfix' if task_type == 'bugfix' else 'lightweight-feature'}.md",
            ]
        },
        sensor_policy={"hard_gates": hard_gates[:1], "soft_signals": [command.id for command in commands.commands if command.gate == "soft"]},
        human_confirmation={"required": False, "reasons": []},
    )

    task_dir = ai / "task-runs" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    _write_yaml(task_dir / "harness-map.yaml", harness_map.model_dump(mode="json"))

    selected_commands = [command for command in commands.commands if command.id in harness_map.sensor_policy.get("hard_gates", [])]
    sensor_results = [run_sensor(root, command) for command in selected_commands]
    if not sensor_results:
        sensor_results = [
            {
                "id": "missing_sensor",
                "command": None,
                "status": "skipped",
                "exit_code": None,
                "duration_seconds": 0.0,
                "summary": "No hard gate sensor was detected for this repository.",
            }
        ]
    sensor_report = {"schema_version": "1.0", "task_id": task_id, "task": task, "sensor_results": sensor_results}
    _write_yaml(task_dir / "sensor-report.yaml", sensor_report)
    _write_text(task_dir / "decision-log.md", _decision_log(task, harness_map, sensor_results))
    _write_text(task_dir / "handoff-summary.md", _handoff_summary(task, harness_map, sensor_results))
    _write_text(task_dir / "experience-candidates.md", _experience_candidates(sensor_results))
    _append_pending_improvements(ai / "experience" / "pending-improvements.md", task_id)
    return task_dir


def _task_type(task: str) -> str:
    lowered = task.lower()
    return "bugfix" if any(term in lowered for term in BUGFIX_TERMS) else "lightweight"


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    _write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))


def _decision_log(task: str, harness_map: HarnessMap, sensor_results: list[dict[str, Any]]) -> str:
    statuses = ", ".join(f"{item['id']}={item['status']}" for item in sensor_results)
    return (
        "# Decision Log\n\n"
        f"Task: {task}\n\n"
        f"Selected workflow: `{harness_map.selected_workflow}`\n\n"
        f"Risk level: `{harness_map.risk_level}`\n\n"
        f"Sensor outcomes: {statuses}\n"
    )


def _handoff_summary(task: str, harness_map: HarnessMap, sensor_results: list[dict[str, Any]]) -> str:
    unresolved = [item for item in sensor_results if item["status"] != "passed"]
    risk_text = "No unresolved sensor risk." if not unresolved else "One or more sensors did not pass; review sensor-report.yaml."
    return (
        "# Handoff Summary\n\n"
        f"Task: {task}\n\n"
        f"Workflow: `{harness_map.selected_workflow}`\n\n"
        "## Verification\n\n"
        f"{risk_text}\n\n"
        "## Remaining Risk\n\n"
        "Generated control assets only; no business code patch was applied in this POC run.\n"
    )


def _experience_candidates(sensor_results: list[dict[str, Any]]) -> str:
    failed_or_skipped = [item for item in sensor_results if item["status"] != "passed"]
    lines = [f"- Review `{item['id']}`: {item['summary']}" for item in failed_or_skipped]
    if not lines:
        lines = ["- Current sensor selection appears sufficient for this low-risk task."]
    return "# Experience Candidates\n\n" + "\n".join(lines) + "\n"


def _append_pending_improvements(path: Path, task_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Pending Improvements\n\n"
    addition = f"\n- Review experience candidates from `{task_id}` before promotion.\n"
    if addition.strip() not in existing:
        path.write_text(existing.rstrip() + addition, encoding="utf-8")
