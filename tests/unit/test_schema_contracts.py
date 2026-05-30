import pytest
from pydantic import ValidationError

from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.harness_map import HarnessMap
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.sensor_report import SensorReport
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection


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


def test_harness_map_accepts_workflow_and_policy_contract():
    harness_map = HarnessMap.model_validate(
        {
            "task_id": "demo-task-001",
            "task_type": "bugfix",
            "selected_workflow": "bugfix",
            "risk_level": "low",
            "guide_policy": {"required": [".ai/guides/project-context.md"]},
            "workflow_skill": {"path": ".ai/skills/bugfix/SKILL.md"},
            "sensor_policy": {"hard_gates": ["unit_test"]},
        }
    )

    assert harness_map.selected_workflow == "bugfix"
    assert harness_map.workflow_skill["path"] == ".ai/skills/bugfix/SKILL.md"


def test_harness_map_rejects_unknown_workflow():
    with pytest.raises(ValidationError):
        HarnessMap.model_validate(
            {
                "task_id": "demo-task-001",
                "task_type": "large-feature",
                "selected_workflow": "large-feature",
            }
        )


def test_sensor_report_requires_known_sensor_status():
    report = SensorReport.model_validate(
        {
            "task_id": "demo-task-001",
            "task": "修复登录接口错误提示不一致的问题",
            "sensor_results": [
                {"id": "unit_test", "command": "mvn test", "status": "passed", "duration_seconds": 0.1, "summary": "passed"}
            ],
        }
    )

    assert report.sensor_results[0].status == "passed"


def test_sensor_report_rejects_unknown_sensor_status():
    with pytest.raises(ValidationError):
        SensorReport.model_validate(
            {
                "task_id": "demo-task-001",
                "task": "修复登录接口错误提示不一致的问题",
                "sensor_results": [
                    {"id": "unit_test", "command": "mvn test", "status": "maybe", "duration_seconds": 0.1, "summary": "unknown"}
                ],
            }
        )


def test_benchmark_report_rejects_unknown_status():
    report = BenchmarkReport.model_validate(
        {"repo_name": "demo", "profile": "java-spring", "status": "passed", "checks": [{"id": "schema:demo", "passed": True}]}
    )

    assert report.status == "passed"
    assert report.checks[0].passed is True

    with pytest.raises(ValidationError):
        BenchmarkReport.model_validate({"repo_name": "demo", "profile": "java-spring", "status": "unknown", "checks": []})


def test_weapon_library_selection_validates_nested_weapon_entries():
    selection = WeaponLibrarySelection.model_validate(
        {
            "primary_stack": "java-spring",
            "selected_stacks": ["common", "java-spring"],
            "guide_weapon_ids": ["common.guide.project-context"],
            "sensor_weapon_ids": ["common.sensor.test-command"],
            "guide_weapons": [
                {
                    "id": "common.guide.project-context",
                    "stack": "common",
                    "kind": "guide",
                    "title": "Project Context",
                    "guidance": "Record project facts.",
                    "recommended_action": "Write a guide.",
                }
            ],
            "sensor_weapons": [
                {
                    "id": "common.sensor.test-command",
                    "stack": "common",
                    "kind": "sensor",
                    "title": "Test Command",
                    "guidance": "Run tests.",
                    "recommended_action": "Keep a hard gate.",
                    "gate": "hard",
                }
            ],
        }
    )

    assert selection.source == "built_in_weapon_library"
    assert selection.guide_weapons[0].kind == "guide"
    assert selection.sensor_weapons[0].gate == "hard"


def test_weapon_library_selection_rejects_invalid_weapon_kind():
    with pytest.raises(ValidationError):
        WeaponLibrarySelection.model_validate(
            {
                "primary_stack": "java-spring",
                "guide_weapons": [
                    {
                        "id": "bad",
                        "stack": "common",
                        "kind": "policy",
                        "title": "Bad",
                        "guidance": "Bad",
                        "recommended_action": "Bad",
                    }
                ],
            }
        )


def test_maturity_report_records_scores_evidence_and_next_steps():
    report = MaturityReport.model_validate(
        {
            "overall_level": "L2",
            "dimension_scores": {"guides": "L1", "sensors": "L2"},
            "evidence": ["识别到主技术栈：java-spring"],
            "blocking_reasons": ["候选规则尚未确认"],
            "recommended_next_steps": ["确认候选规则"],
        }
    )

    assert report.overall_level == "L2"
    assert report.dimension_scores["sensors"] == "L2"


def test_improvement_candidate_report_requires_reviewable_candidates():
    report = ImprovementCandidateReport.model_validate(
        {
            "candidates": [
                {
                    "id": "candidate-1",
                    "candidate_type": "guide_update",
                    "suggested_target": ".ai/guides/project-context.md",
                    "rationale": "Add missing team rule.",
                    "evidence": ["human confirmation"],
                    "human_confirmation_required": True,
                }
            ]
        }
    )

    assert report.candidates[0].suggested_target.startswith(".ai/")
    assert report.candidates[0].human_confirmation_required is True


def test_improvement_candidate_report_rejects_unknown_candidate_type():
    with pytest.raises(ValidationError):
        ImprovementCandidateReport.model_validate(
            {
                "candidates": [
                    {
                        "id": "candidate-1",
                        "candidate_type": "unknown",
                        "suggested_target": ".ai/guides/project-context.md",
                        "rationale": "Bad type.",
                    }
                ]
            }
        )
