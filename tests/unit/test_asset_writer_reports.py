from pathlib import Path

import yaml

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.tools.asset_writers.reports import write_report_assets
from harness_builder_agent.tools.generation_trace import GenerationTrace


def _inventory(repo: Path) -> ProjectInventory:
    return ProjectInventory(
        repo_name=repo.name,
        root_path=str(repo),
        primary_stack="java-spring",
        stacks=["java", "maven", "spring-boot"],
        modules=[{"name": "app", "path": ".", "kind": "backend"}],
        evidence=[{"path": "pom.xml", "reason": "maven build file"}],
        documents=[{"path": "README.md", "kind": "document", "reason": "Repository documentation entrypoint"}],
        configs=[{"path": "src/main/resources/application.yml", "kind": "config", "reason": "Spring runtime configuration"}],
        ci_files=[{"path": ".github/workflows/ci.yml", "kind": "ci", "reason": "GitHub Actions CI definition"}],
        stack_extensions={
            "scan_metadata": {
                "schema_version": "1.0",
                "llm_status": "succeeded",
                "prompt_version": "test",
                "evidence_file_count": 12,
                "coverage": {
                    "schema_version": "1.0",
                    "detected_file_count": 12,
                    "selected_evidence_count": 4,
                    "bucket_coverage": [
                        {
                            "bucket": "test",
                            "total_count": 2,
                            "selected_count": 1,
                            "skipped_count": 1,
                            "selected_paths": ["src/test/java/com/example/demo/DemoControllerTest.java"],
                        },
                        {
                            "bucket": "api_entrypoint",
                            "total_count": 1,
                            "selected_count": 1,
                            "skipped_count": 0,
                            "selected_paths": ["src/main/java/com/example/demo/DemoController.java"],
                        },
                    ],
                    "warnings": [],
                },
                "evidence_expansion": {
                    "schema_version": "1.0",
                    "planner_prompt_version": "llm-evidence-planner-v1",
                    "requested_paths": ["src/main/java/com/example/demo/DemoController.java"],
                    "risk_focus": ["controller routing"],
                    "rationale": "Controller route ownership needed deeper inspection.",
                    "confidence": "medium",
                    "read_paths": ["src/main/java/com/example/demo/DemoController.java"],
                    "read_file_count": 1,
                },
                "warnings": [
                    {
                        "code": "test_evidence_not_found",
                        "message": "Some test evidence needs confirmation.",
                        "severity": "warning",
                        "evidence": ["test"],
                    }
                ],
            },
            "scan_validation": {
                "checked_claims": ["java-spring", "maven"],
                "supported_claims": ["java-spring"],
                "unsupported_claims": [{"stack": "maven", "reason": "Wrapper not found."}],
            },
            "scan_warnings": [
                {
                    "code": "test_evidence_not_found",
                    "message": "Some test evidence needs confirmation.",
                    "severity": "warning",
                    "evidence": ["test"],
                }
            ],
            "risk_areas": [{"path": "src/main/resources/application.yml", "reason": "database config risk"}],
        },
    )


def _commands() -> CommandCatalog:
    return CommandCatalog(
        commands=[
            CommandDefinition(
                id="unit_test",
                command="mvn test",
                type="test",
                gate="hard",
                source="pom.xml",
                confidence="high",
            )
        ]
    )


def _weapon_selection() -> WeaponLibrarySelection:
    return WeaponLibrarySelection(
        primary_stack="java-spring",
        selected_stacks=["common", "java-spring"],
        guide_weapon_ids=["java-spring.guide.layering"],
        sensor_weapon_ids=["common.sensor.tests"],
    )


def test_write_report_assets_writes_reports_scores_plan_and_records_trace(tmp_path: Path):
    ai = tmp_path / ".ai"
    trace = GenerationTrace.start(tmp_path, "init", run_id="20260530-120000-init")

    write_report_assets(ai, _inventory(tmp_path), _commands(), HarnessConfig.default(), _weapon_selection(), trace=trace)
    trace.finish("completed", {"primary_stack": "java-spring"})

    assert (ai / "scan-report.md").exists()
    assert (ai / "maturity-report.md").exists()
    assert (ai / "maturity-score.yaml").exists()
    assert (ai / "maturity-evidence.yaml").exists()
    assert (ai / "evolution-plan.md").exists()
    scan_report = (ai / "scan-report.md").read_text(encoding="utf-8")
    assert "## Evidence" in scan_report
    assert "README.md" in scan_report
    assert "Repository documentation entrypoint" in scan_report
    assert ".github/workflows/ci.yml" in scan_report
    assert "GitHub Actions CI definition" in scan_report
    assert "## LLM Evidence Expansion" in scan_report
    assert "requested_paths=`src/main/java/com/example/demo/DemoController.java`" in scan_report
    assert "read_paths=`src/main/java/com/example/demo/DemoController.java`" in scan_report
    assert "risk_focus=`controller routing`" in scan_report
    assert "confidence=`medium`" in scan_report
    assert "read_file_count=1" in scan_report
    assert "Controller route ownership needed deeper inspection." in scan_report
    assert "## Evidence Coverage" in scan_report
    assert "evidence_selected=4/12" in scan_report
    assert "selected_paths=`src/test/java/com/example/demo/DemoControllerTest.java`" in scan_report
    assert "selected_paths=`src/main/java/com/example/demo/DemoController.java`" in scan_report
    assert "## Stack Evidence Validation" in scan_report
    assert "checked_claims=`java-spring`, `maven`" in scan_report
    assert "unsupported_claim=`maven`: Wrapper not found." in scan_report
    assert "## Scan Warnings" in scan_report
    assert "`warning` `test_evidence_not_found`: Some test evidence needs confirmation." in scan_report
    assert "## Risk Areas" in scan_report
    assert "src/main/resources/application.yml" in scan_report
    assert "## Command Candidates" in scan_report
    assert "confidence=`high`" in scan_report
    maturity_report = (ai / "maturity-report.md").read_text(encoding="utf-8")
    assert "## 证据" in maturity_report
    assert "evidence:" not in maturity_report
    assert "blockers:" not in maturity_report
    assert "Guides 上下文" in maturity_report
    assert "证据：" in maturity_report
    assert "阻断：" in maturity_report
    maturity = yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8"))
    assert maturity["schema_version"] == "1.0"
    assert "dimensions" in maturity
    assert "guides" in maturity["dimensions"]
    assert maturity["dimensions"]["workflow"]["level"] == "L2"
    maturity_text = yaml.safe_dump(maturity, allow_unicode=True)
    assert "Workflow routing rules configured" not in maturity_text
    assert "Validate workflow routing" not in maturity_text
    assert any("Workflow routing 规则数量：3" in item["summary"] for item in maturity["dimensions"]["workflow"]["evidence"])
    assert "用全部 resolved 的 Runtime task-run 证据验证 Workflow routing。" in maturity["dimensions"]["workflow"]["next_level_requirements"]
    assert any(blocker["id"] == "runtime-workflow-not-observed" for blocker in maturity["dimensions"]["workflow"]["blockers"])
    assert "next_steps" in maturity
    evidence = yaml.safe_load((ai / "maturity-evidence.yaml").read_text(encoding="utf-8"))
    assert evidence["schema_version"] == "1.0"
    assert evidence["repo_name"] == tmp_path.name
    assert evidence["command_summary"]["hard_gate_count"] == 1
    assert ".ai/project-inventory.json" in evidence["maturity_inputs"]

    artifacts = yaml.safe_load((ai / "runs" / "20260530-120000-init" / "artifacts.yaml").read_text(encoding="utf-8"))
    assert {"path": ".ai/scan-report.md", "kind": "report"} in artifacts["artifacts"]
    assert {"path": ".ai/maturity-report.md", "kind": "report"} in artifacts["artifacts"]
    assert {"path": ".ai/maturity-score.yaml", "kind": "maturity_score"} in artifacts["artifacts"]
    assert {"path": ".ai/maturity-evidence.yaml", "kind": "maturity_evidence"} in artifacts["artifacts"]
    assert {"path": ".ai/evolution-plan.md", "kind": "plan"} in artifacts["artifacts"]
