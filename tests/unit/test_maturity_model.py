from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.maturity_model import build_maturity_report


def _inventory() -> ProjectInventory:
    return ProjectInventory(repo_name="demo", root_path="/tmp/demo", primary_stack="java-spring", modules=[], evidence=[])


def _commands() -> CommandCatalog:
    return CommandCatalog(commands=[])


def _hard_gate_commands() -> CommandCatalog:
    return CommandCatalog(
        commands=[
            CommandDefinition(
                id="test",
                command="pytest",
                type="test",
                gate="hard",
                source="package",
                confidence="high",
            )
        ]
    )


def _write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _write_workflow_assets(ai: Path) -> None:
    (ai / "guides").mkdir(parents=True, exist_ok=True)
    (ai / "guides" / "project-context.md").write_text(
        "# Project Context\n\n## 当前项目事实\n\nReady.\n",
        encoding="utf-8",
    )
    for skill in ("lightweight", "bugfix", "standard"):
        (ai / "skills" / skill).mkdir(parents=True, exist_ok=True)
        (ai / "skills" / skill / "SKILL.md").write_text(f"# {skill}\n", encoding="utf-8")
    (ai / "runs" / "init-1").mkdir(parents=True, exist_ok=True)


def _write_runtime_task_run(
    ai: Path,
    task_id: str = "task-1",
    sensor_status: str = "passed",
    repair_attempts: int = 0,
) -> None:
    run = ai / "task-runs" / task_id
    _write_yaml(
        run / "harness-map.yaml",
        {"schema_version": "1.0", "task_id": task_id, "task_type": "bugfix", "selected_workflow": "bugfix"},
    )
    _write_yaml(
        run / "sensor-report.yaml",
        {
            "schema_version": "1.0",
            "task_id": task_id,
            "task": "Fix checkout bug",
            "sensor_results": [
                {
                    "id": "pytest",
                    "command": "pytest",
                    "status": sensor_status,
                    "exit_code": 0 if sensor_status == "passed" else 1,
                    "duration_seconds": 1.0,
                    "summary": f"pytest {sensor_status}",
                }
            ],
        },
    )
    _write_yaml(
        run / "runtime-summary.yaml",
        {
            "schema_version": "1.0",
            "task_id": task_id,
            "selected_workflow": "bugfix",
            "status": "completed" if sensor_status == "passed" else "completed_with_sensor_failures",
            "sensor_status": sensor_status,
            "repair_attempts": repair_attempts,
            "unresolved_sensor_count": 0 if sensor_status == "passed" else 1,
            "risk_count": 1,
            "summary": "Runtime captured outcome.",
        },
    )
    (run / "decision-log.md").write_text("# Decision Log\n\nReviewed routing and sensor outcome.\n", encoding="utf-8")
    (run / "handoff-summary.md").write_text("# Handoff Summary\n\nTask completed with runtime evidence.\n", encoding="utf-8")


def test_runtime_passed_task_run_lifts_workflow_observability_and_overall_to_l3(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_workflow_assets(ai)
    _write_runtime_task_run(ai, sensor_status="passed", repair_attempts=1)

    report = build_maturity_report(
        ai=ai,
        inventory=_inventory(),
        commands=_hard_gate_commands(),
        config=HarnessConfig.default(),
    )

    assert report.overall_level == "L3"
    assert report.dimensions["workflow"].level == "L3"
    assert report.dimensions["observability"].level == "L2"
    assert report.dimensions["governance_auditability"].level == "L2"
    assert report.dimensions["repair_loop"].level == "L2"
    assert any(".ai/task-runs/task-1/" == item.source for item in report.dimensions["workflow"].evidence)
    assert any(".ai/task-runs/task-1/" == item.source for item in report.dimensions["governance_auditability"].evidence)


def test_runtime_failed_sensor_keeps_overall_below_l3(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_workflow_assets(ai)
    _write_runtime_task_run(ai, sensor_status="failed", repair_attempts=1)

    report = build_maturity_report(
        ai=ai,
        inventory=_inventory(),
        commands=_hard_gate_commands(),
        config=HarnessConfig.default(),
    )

    assert report.overall_level == "L2"
    assert report.dimensions["workflow"].level == "L2"
    assert any(blocker.id == "runtime-sensors-unresolved" for blocker in report.dimensions["workflow"].blockers)
    assert any("Runtime Sensor 结果尚未全部 resolved" in reason for reason in report.blocking_reasons)


def test_maturity_report_uses_chinese_user_facing_narrative():
    report = build_maturity_report(
        ai=None,
        inventory=_inventory(),
        commands=_hard_gate_commands(),
        config=HarnessConfig.default(),
    )

    text = "\n".join(report.blocking_reasons + report.recommended_next_steps)

    assert "Guides are structured" not in text
    assert "Workflow routing policy exists" not in text
    assert "Bind guides to workflow" not in text
    assert "Validate workflow routing" not in text
    assert "Guides 已结构化" in text
    assert "绑定 Guides 到 Workflow routing 和任务风险上下文" in text
    assert "用全部 resolved 的 Runtime task-run 证据验证 Workflow routing" in text


def test_experience_dimension_uses_workflow_recommendation_review_count(tmp_path: Path):
    ai = tmp_path / ".ai"
    _write_yaml(
        ai / "experience" / "experience-index.yaml",
        {
            "schema_version": "1.0",
            "experience_files": {"pending-improvements.md": True},
            "sources": [
                {"path": ".ai/review/workflow-routing-recommendation.yaml", "kind": "workflow_recommendation", "item_count": 1}
            ],
            "pending_improvement_count": 0,
            "asset_candidate_count": 0,
            "maturity_review_count": 0,
            "workflow_recommendation_count": 1,
            "runtime_task_run_count": 0,
            "warnings": [],
        },
    )

    report = build_maturity_report(ai=ai, inventory=_inventory(), commands=_commands(), config=HarnessConfig.default())

    experience = report.dimensions["experience"]
    assert experience.level == "L2"
    assert any("Workflow recommendation reviews 数量：1" in item.summary for item in experience.evidence)
    assert any(blocker.id == "experience-not-runtime-derived" for blocker in experience.blockers)


def test_experience_dimension_keeps_legacy_pending_file_behavior(tmp_path: Path):
    ai = tmp_path / ".ai"
    (ai / "experience").mkdir(parents=True)
    (ai / "experience" / "pending-improvements.md").write_text("# Pending Improvements\n", encoding="utf-8")

    report = build_maturity_report(ai=ai, inventory=_inventory(), commands=_commands(), config=HarnessConfig.default())

    assert report.dimensions["experience"].level == "L1"


def test_repair_loop_absent_runtime_uses_ai_contract_evidence_source(tmp_path: Path):
    ai = tmp_path / ".ai"

    report = build_maturity_report(ai=ai, inventory=_inventory(), commands=_commands(), config=HarnessConfig.default())

    repair_loop = report.dimensions["repair_loop"]
    assert repair_loop.level == "L0"
    assert any(item.source == ".ai/task-runs/" for item in repair_loop.evidence)
    assert all(item.source.startswith(".ai/") for item in repair_loop.evidence)
