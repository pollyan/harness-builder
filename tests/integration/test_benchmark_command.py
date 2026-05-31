from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml
from typer.testing import CliRunner

from harness_builder_agent.cli import app
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.tools.benchmark import (
    _content_checks,
    _candidate_governance_check,
    _human_confirmation_checks,
    _llm_enhancement_checks,
    _quality_scores,
    _schema_checks,
    run_benchmark,
)
from harness_builder_agent.tools.candidate_governance import review_candidate
from harness_builder_agent.tools.scan_repo import scan_repository

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _fake_scan(repo: Path, primary_stack: str):
    if primary_stack == "java-spring":
        response = {
            "primary_stack": "java-spring",
            "stacks": ["java", "maven", "spring-boot"],
            "modules": [{"name": "app", "path": ".", "kind": "backend"}],
            "architecture_signals": [],
            "risk_areas": [],
            "command_candidates": [
                {"id": "unit_test", "command": "mvn test", "type": "test", "gate": "hard", "source": "pom.xml", "confidence": "high"}
            ],
            "configs": [],
            "ci_files": [],
            "confidence": "high",
            "needs_human_confirmation": False,
            "reasoning_summary": "Java Spring project.",
        }
    else:
        response = {
            "primary_stack": "dotnet-aspnet",
            "stacks": ["dotnet", "aspnet-core"],
            "modules": [{"name": "MiniApi", "path": "src", "kind": "backend"}],
            "architecture_signals": [],
            "risk_areas": [],
            "command_candidates": [
                {
                    "id": "unit_test",
                    "command": "dotnet test",
                    "type": "test",
                    "gate": "hard",
                    "source": "mini-dotnet-webapi.sln",
                    "confidence": "high",
                }
            ],
            "configs": [],
            "ci_files": [],
            "confidence": "high",
            "needs_human_confirmation": False,
            "reasoning_summary": ".NET ASP.NET project.",
        }
    return scan_repository(repo, llm_caller=lambda _messages: json.dumps(response))


def _fake_scan_with_risk(repo: Path, primary_stack: str, risk_path: str, reason: str = "核心控制器变更影响请求路径。"):
    inventory, commands = _fake_scan(repo, primary_stack)
    inventory.stack_extensions["risk_areas"] = [{"path": risk_path, "reason": reason}]
    return inventory, commands


def _latest_trace(repo: Path) -> dict:
    runs = sorted((repo / ".ai" / "runs").iterdir())
    assert runs
    return yaml.safe_load((runs[-1] / "trace.yaml").read_text(encoding="utf-8"))


def _copy_fixture_repo(tmp_path: Path, fixture_name: str) -> Path:
    repo = tmp_path / fixture_name
    shutil.copytree(FIXTURES / fixture_name, repo, ignore=shutil.ignore_patterns(".ai"))
    return repo


def _write_valid_workflow_recommendation(ai: Path) -> None:
    review = ai / "review"
    review.mkdir(parents=True, exist_ok=True)
    (review / "workflow-routing-recommendation.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "task_id": "task-1",
                "task_brief": "Fix a regression in login validation.",
                "recommended_workflow": "bugfix",
                "matched_rule_ids": ["bugfix-intent"],
                "risk_level": "medium",
                "confidence": "high",
                "rationale": "The task is a defect repair and should use the bugfix workflow.",
                "required_guides": [".ai/guides/project-context.md"],
                "required_sensors": [".ai/sensors/verification.md"],
                "human_confirmation_required": False,
                "review_status": "pending_harness_maintainer_review",
                "evidence_sources": [".ai/harness-config.yaml", ".ai/maturity-evidence.yaml"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (review / "workflow-routing-recommendation.md").write_text(
        "# Workflow Routing Recommendation\n\n"
        "## Task\n\nFix a regression in login validation.\n\n"
        "## Recommended Workflow\n\nbugfix\n\n"
        "## Matched Routing Rules\n\n- bugfix-intent\n\n"
        "## Required Harness Assets\n\n- .ai/guides/project-context.md\n\n"
        "## Review Boundary\n\npending_harness_maintainer_review\n",
        encoding="utf-8",
    )


def _write_valid_workflow_recommendation_history(ai: Path) -> None:
    history_dir = ai / "review" / "workflow-routing-recommendations"
    history_dir.mkdir(parents=True, exist_ok=True)
    recommendations = []
    for task_id, workflow, rule_id, created_at in [
        ("task-1", "bugfix", "bugfix-intent", "2026-05-31T11:59:00Z"),
        ("task-2", "standard", "standard-escalation", "2026-05-31T12:00:00Z"),
    ]:
        recommendation_id = f"{task_id}-20260531T120000Z"
        yaml_path = history_dir / f"{recommendation_id}.yaml"
        markdown_path = history_dir / f"{recommendation_id}.md"
        yaml_path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": "1.0",
                    "task_id": task_id,
                    "task_brief": f"Task brief for {task_id}.",
                    "recommended_workflow": workflow,
                    "matched_rule_ids": [rule_id],
                    "risk_level": "medium" if workflow == "bugfix" else "high",
                    "confidence": "high",
                    "rationale": f"{workflow} matches the configured routing policy.",
                    "required_guides": [".ai/guides/project-context.md"],
                    "required_sensors": [".ai/sensors/verification.md"],
                    "human_confirmation_required": workflow == "standard",
                    "review_status": "pending_harness_maintainer_review",
                    "evidence_sources": [".ai/harness-config.yaml", ".ai/maturity-evidence.yaml"],
                },
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        markdown_path.write_text(
            "# Workflow Routing Recommendation\n\n"
            f"## Task\n\nTask brief for {task_id}.\n\n"
            f"## Recommended Workflow\n\n{workflow}\n\n"
            f"## Matched Routing Rules\n\n- {rule_id}\n\n"
            "## Required Harness Assets\n\n- .ai/guides/project-context.md\n\n"
            "## Review Boundary\n\npending_harness_maintainer_review\n",
            encoding="utf-8",
        )
        recommendations.append(
            {
                "recommendation_id": recommendation_id,
                "task_id": task_id,
                "created_at": created_at,
                "yaml_path": f".ai/review/workflow-routing-recommendations/{recommendation_id}.yaml",
                "markdown_path": f".ai/review/workflow-routing-recommendations/{recommendation_id}.md",
                "recommended_workflow": workflow,
                "risk_level": "medium" if workflow == "bugfix" else "high",
                "confidence": "high",
                "review_status": "pending_harness_maintainer_review",
            }
        )
    (history_dir / "index.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "latest_recommendation_id": recommendations[-1]["recommendation_id"],
                "recommendations": recommendations,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (ai / "review" / "workflow-routing-recommendations.md").write_text(
        "# Workflow Routing Recommendation History\n\n"
        "## Latest Recommendation\n\n"
        f"- `{recommendations[-1]['recommendation_id']}`\n\n"
        "## Recommendations\n\n"
        + "\n".join(f"- `{item['recommendation_id']}`: `{item['recommended_workflow']}`" for item in recommendations)
        + "\n\n## Review Boundary\n\npending_harness_maintainer_review\n",
        encoding="utf-8",
    )


def _write_valid_asset_candidates(ai: Path) -> None:
    review = ai / "review"
    review.mkdir(parents=True, exist_ok=True)
    improvements = yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    source_id = improvements["candidates"][0]["id"]
    (review / "asset-candidates.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_maturity_review",
                "candidates": [
                    {
                        "id": "workflow-routing-policy-review",
                        "kind": "workflow_policy",
                        "source_candidate_id": source_id,
                        "source_review_decision": "support",
                        "suggested_path": ".ai/harness-config.yaml",
                        "title": "Review workflow routing policy",
                        "rationale": "Workflow recommendation evidence suggests a routing policy review.",
                        "draft_content": "Structured workflow policy patch.",
                        "workflow_policy_patch": {
                            "schema_version": "1.0",
                            "operation": "upsert_routing_rule",
                            "target": "workflow_routing.rules",
                            "rule": {
                                "id": "standard-escalation",
                                "selected_workflow": "standard",
                                "rationale": "Escalate high-risk and domain policy changes to the standard workflow.",
                                "task_type_hints": ["feature", "policy"],
                                "triggers": [
                                    "unclear_impact_scope",
                                    "high_risk_module",
                                    "cross_module_design",
                                    "security_or_permission",
                                    "insufficient_sensor_coverage",
                                    "domain_policy_change",
                                ],
                                "required_guides": [".ai/guides/project-context.md", ".ai/guides/architecture.md"],
                                "required_sensors": [".ai/sensors/verification.md"],
                                "human_confirmation_required": True,
                            },
                        },
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                        "acceptance_checks": ["Benchmark content:workflow-routing-policy passes."],
                        "risk_level": "medium",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    for filename, title in {
        "asset-candidate-guides.md": "Asset Candidate Guides",
        "asset-candidate-sensors.md": "Asset Candidate Sensors",
        "asset-candidate-workflows.md": "Asset Candidate Workflows",
    }.items():
        (review / filename).write_text(
            f"# {title}\n\n"
            "## Review workflow routing policy\n\n"
            "### Rationale\n\nReview rationale.\n\n"
            "### Draft Content\n\nDraft only.\n\n"
            "### Evidence Sources\n\n- .ai/maturity-evidence.yaml\n\n"
            "### Acceptance Checks\n\n- Benchmark content:workflow-routing-policy passes.\n",
            encoding="utf-8",
        )


def _write_valid_candidate_governance(ai: Path) -> None:
    review = ai / "review"
    review.mkdir(parents=True, exist_ok=True)
    asset_report = yaml.safe_load((review / "asset-candidates.yaml").read_text(encoding="utf-8"))
    source_candidate_id = asset_report["candidates"][0]["source_candidate_id"]
    (review / "candidate-governance.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "decisions": [
                    {
                        "candidate_id": "workflow-routing-policy-review",
                        "candidate_kind": "workflow_policy",
                        "source_report": ".ai/review/asset-candidates.yaml",
                        "source_candidate_id": source_candidate_id,
                        "suggested_path": ".ai/harness-config.yaml",
                        "decision": "accepted",
                        "rationale": "Maintainer accepted the direction but did not apply YAML automatically.",
                        "reviewer": "harness-maintainer",
                        "decided_at": "2026-05-31T00:00:00Z",
                        "applied_paths": [],
                        "acceptance_checks": ["Benchmark content:workflow-routing-policy passes."],
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (review / "candidate-governance.md").write_text(
        "# Candidate Governance\n\n"
        "## Decisions\n\n"
        "### workflow-routing-policy-review\n\n"
        "- decision: `accepted`\n"
        "- suggested path: `.ai/harness-config.yaml`\n\n"
        "## Review Boundary\n\n"
        "- LLM asset candidates remain review-only unless an explicit governance decision applies them.\n",
        encoding="utf-8",
    )


def _write_valid_maturity_review(ai: Path) -> None:
    review = ai / "review"
    review.mkdir(parents=True, exist_ok=True)
    improvements = yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    source_id = improvements["candidates"][0]["id"]
    (review / "maturity-review.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "summary": "Candidates are aligned with maturity evidence.",
                "reviewer_model": "deepseek-test",
                "review_status": "pending_harness_maintainer_review",
                "candidate_reviews": [
                    {
                        "candidate_id": source_id,
                        "decision": "support",
                        "rationale": "Candidate is grounded in maturity evidence.",
                        "risks": [],
                        "suggested_acceptance_checks": ["Run benchmark."],
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                    }
                ],
                "missing_candidates": [],
                "global_risks": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (review / "maturity-review.md").write_text(
        "# Maturity Review\n\n"
        "## Summary\n\nCandidates are aligned.\n\n"
        "## Candidate Reviews\n\n- candidate: support\n\n"
        "## Missing Candidates\n\n- None.\n\n"
        "## Global Risks\n\n- None.\n\n"
        "## Review Boundary\n\n- review status: `pending_harness_maintainer_review`\n",
        encoding="utf-8",
    )


def _write_valid_experience_summary(ai: Path) -> None:
    experience = ai / "experience"
    experience.mkdir(parents=True, exist_ok=True)
    (experience / "experience-summary.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "source": "llm_experience_summary",
                "review_status": "pending_harness_maintainer_review",
                "summary": "Sensor coverage is the main experience signal.",
                "findings": [
                    {
                        "id": "sensor-coverage-gap",
                        "kind": "sensor_feedback",
                        "title": "Sensor coverage gap",
                        "summary": "Pending improvements point to missing sensor coverage.",
                        "evidence_sources": [".ai/experience/pending-improvements.md"],
                        "confidence": "high",
                        "suggested_follow_up": "Draft a reviewed sensor candidate.",
                    }
                ],
                "warnings": ["Runtime task-runs are absent."],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (experience / "experience-summary.md").write_text(
        "# Experience Summary\n\n"
        "## Summary\n\nSensor coverage is the main experience signal.\n\n"
        "## Findings\n\n### Sensor coverage gap\n\n- evidence: `.ai/experience/pending-improvements.md`\n\n"
        "## Warnings\n\n- Runtime task-runs are absent.\n",
        encoding="utf-8",
    )


def _write_valid_self_improve_package(ai: Path) -> None:
    review = ai / "review"
    review.mkdir(parents=True, exist_ok=True)
    (review / "self-improve-package.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "package_id": "self-improve-package",
                "review_status": "pending_harness_maintainer_review",
                "generated_artifacts": [
                    {"path": ".ai/improvement-candidates.yaml", "kind": "improvement_candidates"},
                    {"path": ".ai/review/maturity-review.yaml", "kind": "maturity_review"},
                    {"path": ".ai/review/asset-candidates.yaml", "kind": "asset_candidates"},
                    {"path": ".ai/review/self-improve-package.yaml", "kind": "self_improve_package"},
                ],
                "candidate_counts": {
                    "improvement_candidates": 2,
                    "maturity_reviews": 1,
                    "asset_candidates": 1,
                    "guide_candidates": 1,
                    "sensor_candidates": 0,
                    "workflow_policy_candidates": 0,
                },
                "maturity": {
                    "overall_level": "L2",
                    "target_next_level": "L3",
                    "dimension_scores": {"guides": "L2", "sensors": "L2"},
                },
                "next_actions": ["Review asset candidates before applying formal Harness changes."],
                "warnings": ["runtime task-runs absent"],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (review / "self-improve-package.md").write_text(
        "# Self-Improve Package\n\n"
        "## Maturity Snapshot\n\n- overall level: `L2`\n\n"
        "## Generated Artifacts\n\n- `.ai/improvement-candidates.yaml`\n\n"
        "## Candidate Counts\n\n- asset candidates: 1\n\n"
        "## Next Actions\n\n- Review asset candidates before applying formal Harness changes.\n\n"
        "## Review Boundary\n\n- review status: `pending_harness_maintainer_review`\n",
        encoding="utf-8",
    )


def _write_runtime_task_run(ai: Path, task_id: str = "task-1", sensor_status: str = "failed") -> Path:
    run = ai / "task-runs" / task_id
    run.mkdir(parents=True, exist_ok=True)
    (run / "harness-map.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "task_id": task_id,
                "task_type": "bugfix",
                "selected_workflow": "bugfix",
                "risk_level": "medium",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (run / "sensor-report.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "task_id": task_id,
                "task": "Fix checkout bug",
                "sensor_results": [
                    {
                        "id": "pytest",
                        "command": "pytest",
                        "status": sensor_status,
                        "exit_code": 1 if sensor_status == "failed" else 0,
                        "duration_seconds": 3.2,
                        "summary": "pytest failed" if sensor_status == "failed" else "pytest passed",
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (run / "runtime-summary.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "task_id": task_id,
                "selected_workflow": "bugfix",
                "status": "completed_with_sensor_failures" if sensor_status == "failed" else "completed",
                "sensor_status": sensor_status,
                "repair_attempts": 1,
                "unresolved_sensor_count": 1 if sensor_status == "failed" else 0,
                "risk_count": 1,
                "summary": "Runtime captured sensor outcome.",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (run / "decision-log.md").write_text("# Decision Log\n\nInvestigated pytest result.\n", encoding="utf-8")
    (run / "handoff-summary.md").write_text("# Handoff Summary\n\nPytest still fails.\n", encoding="utf-8")
    return run


def _prepare_passed_benchmark_repo(tmp_path: Path, monkeypatch, fixture_name: str = "mini-spring-boot", profile: str = "java-spring") -> Path:
    repo = _copy_fixture_repo(tmp_path, fixture_name)
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, profile))
    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", profile])
    assert result.exit_code == 0, result.output
    return repo


def _add_consistent_risk_context(ai: Path, risk_path: str, reason: str = "核心控制器变更影响请求路径。") -> ProjectInventory:
    inventory_path = ai / "project-inventory.json"
    inventory_payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory_payload.setdefault("stack_extensions", {})["risk_areas"] = [{"path": risk_path, "reason": reason}]
    inventory_path.write_text(json.dumps(inventory_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    guide_path = ai / "guides" / "project-context.md"
    guide_path.write_text(
        guide_path.read_text(encoding="utf-8") + f"\n\n- 风险路径：`{risk_path}` - {reason}\n",
        encoding="utf-8",
    )

    sensor_path = ai / "sensors" / "verification.md"
    sensor_path.write_text(
        sensor_path.read_text(encoding="utf-8") + f"\n\n- 风险路径：`{risk_path}` - 待确认验证覆盖。\n",
        encoding="utf-8",
    )

    config_path = ai / "harness-config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    standard = next(rule for rule in config["workflow_routing"]["rules"] if rule["id"] == "standard-escalation")
    trigger = f"risk_area:{risk_path}"
    if trigger not in standard["triggers"]:
        standard["triggers"].append(trigger)
    standard["rationale"] = (
        standard["rationale"].rstrip(".")
        + f". Scanned risk area `{risk_path}` requires standard workflow review: {reason}"
    )
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")

    return ProjectInventory.model_validate_json(inventory_path.read_text(encoding="utf-8"))


def _add_consistent_project_context_evidence_context(ai: Path) -> ProjectInventory:
    inventory_path = ai / "project-inventory.json"
    inventory_payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory_payload["documents"] = [{"path": "README.md", "kind": "project documentation"}]
    inventory_payload["configs"] = [{"path": "src/main/resources/application.yml", "kind": "spring configuration"}]
    inventory_payload["ci_files"] = [{"path": ".github/workflows/ci.yml", "kind": "github actions"}]
    inventory_payload.setdefault("stack_extensions", {}).setdefault("scan_metadata", {})["evidence_expansion"] = {
        "schema_version": "1.0",
        "planner_prompt_version": "llm-evidence-planner-v1",
        "requested_paths": ["src/main/java/com/example/demo/DemoController.java"],
        "risk_focus": ["controller routing"],
        "rationale": "Controller route ownership needed deeper inspection.",
        "confidence": "medium",
        "read_paths": ["src/main/java/com/example/demo/DemoController.java"],
        "read_file_count": 1,
    }
    inventory_path.write_text(json.dumps(inventory_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    guide_path = ai / "guides" / "project-context.md"
    guide_text = guide_path.read_text(encoding="utf-8")
    source_lines = (
        "- `README.md`：project documentation\n"
        "- `src/main/resources/application.yml`：spring configuration\n"
        "- `.github/workflows/ci.yml`：github actions\n"
    )
    if "## LLM 证据扩展" in guide_text:
        guide_text = guide_text.replace("## LLM 证据扩展", source_lines + "\n## LLM 证据扩展", 1)
        guide_text = guide_text.replace(
            "- evidence_expansion=not_run",
            "- requested_paths=`src/main/java/com/example/demo/DemoController.java`\n"
            "- read_paths=`src/main/java/com/example/demo/DemoController.java`\n"
            "- risk_focus=`controller routing`\n"
            "- confidence=`medium`\n"
            "- read_file_count=1\n"
            "- rationale=Controller route ownership needed deeper inspection.",
            1,
        )
    else:
        guide_text += (
            "\n\n## 来源证据\n\n"
            + source_lines
            + "\n## LLM 证据扩展\n\n"
            "- requested_paths=`src/main/java/com/example/demo/DemoController.java`\n"
            "- read_paths=`src/main/java/com/example/demo/DemoController.java`\n"
            "- risk_focus=`controller routing`\n"
            "- confidence=`medium`\n"
            "- read_file_count=1\n"
            "- rationale=Controller route ownership needed deeper inspection.\n"
        )
    guide_path.write_text(guide_text, encoding="utf-8")

    return ProjectInventory.model_validate_json(inventory_path.read_text(encoding="utf-8"))


def _add_consistent_scan_report_context(ai: Path) -> ProjectInventory:
    inventory_path = ai / "project-inventory.json"
    inventory_payload = json.loads(inventory_path.read_text(encoding="utf-8"))
    inventory_payload["documents"] = [{"path": "README.md", "kind": "project documentation"}]
    inventory_payload["configs"] = [{"path": "src/main/resources/application.yml", "kind": "spring configuration"}]
    inventory_payload["ci_files"] = [{"path": ".github/workflows/ci.yml", "kind": "github actions"}]
    inventory_payload.setdefault("stack_extensions", {})["risk_areas"] = [
        {"path": "src/main/resources/application.yml", "reason": "database config risk"}
    ]
    inventory_payload["stack_extensions"]["scan_warnings"] = [
        {
            "code": "test_evidence_not_found",
            "message": "Some test evidence needs confirmation.",
            "severity": "warning",
            "evidence": ["test"],
        }
    ]
    inventory_payload["stack_extensions"]["scan_validation"] = {
        "checked_claims": ["java-spring", "maven"],
        "supported_claims": ["java-spring"],
        "unsupported_claims": [{"stack": "maven", "reason": "Wrapper not found."}],
    }
    scan_metadata = inventory_payload["stack_extensions"].setdefault("scan_metadata", {})
    scan_metadata["coverage"] = {
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
    }
    scan_metadata["evidence_expansion"] = {
        "schema_version": "1.0",
        "planner_prompt_version": "llm-evidence-planner-v1",
        "requested_paths": ["src/main/java/com/example/demo/DemoController.java"],
        "risk_focus": ["controller routing"],
        "rationale": "Controller route ownership needed deeper inspection.",
        "confidence": "medium",
        "read_paths": ["src/main/java/com/example/demo/DemoController.java"],
        "read_file_count": 1,
    }
    inventory_path.write_text(json.dumps(inventory_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = ai / "scan-report.md"
    report.write_text(
        "# Scan Report\n\n"
        "Repository: `mini-spring-boot`\n\n"
        "Primary stack: `java-spring`\n\n"
        "## Evidence\n\n"
        "- `pom.xml`: maven build file\n"
        "- `README.md`: project documentation\n"
        "- `src/main/resources/application.yml`: spring configuration\n"
        "- `.github/workflows/ci.yml`: github actions\n\n"
        "## LLM Evidence Expansion\n\n"
        "- requested_paths=`src/main/java/com/example/demo/DemoController.java`\n"
        "- read_paths=`src/main/java/com/example/demo/DemoController.java`\n"
        "- risk_focus=`controller routing`\n"
        "- confidence=`medium`\n"
        "- read_file_count=1\n"
        "- rationale=Controller route ownership needed deeper inspection.\n\n"
        "## Evidence Coverage\n\n"
        "- evidence_selected=4/12\n"
        "- `test`: selected=1 total=2 skipped=1 selected_paths=`src/test/java/com/example/demo/DemoControllerTest.java`\n"
        "- `api_entrypoint`: selected=1 total=1 skipped=0 selected_paths=`src/main/java/com/example/demo/DemoController.java`\n\n"
        "## Stack Evidence Validation\n\n"
        "- checked_claims=`java-spring`, `maven`\n"
        "- supported_claims=`java-spring`\n"
        "- unsupported_claim=`maven`: Wrapper not found.\n\n"
        "## Scan Warnings\n\n"
        "- `warning` `test_evidence_not_found`: Some test evidence needs confirmation. evidence=`test`\n\n"
        "## Risk Areas\n\n"
        "- `src/main/resources/application.yml`: database config risk\n\n"
        "## Command Candidates\n\n"
        "- `hard` `test` `unit_test`: `mvn test` (source=`pom.xml`, confidence=`high`)\n",
        encoding="utf-8",
    )
    return ProjectInventory.model_validate_json(inventory_path.read_text(encoding="utf-8"))


def _add_consistent_init_summary_evidence_audit(ai: Path) -> None:
    summary_path = ai / "init-summary.md"
    text = summary_path.read_text(encoding="utf-8")
    audit_section = (
        "## 扫描证据审计\n\n"
        "- requested_paths=`src/main/java/com/example/demo/DemoController.java`\n"
        "- read_paths=`src/main/java/com/example/demo/DemoController.java`\n"
        "- risk_focus=`controller routing`\n"
        "- confidence=`medium`\n"
        "- read_file_count=1\n"
        "- rationale=Controller route ownership needed deeper inspection.\n"
        "- evidence_selected=4/12\n"
        "- `test`: selected=1 total=2 skipped=1 selected_paths=`src/test/java/com/example/demo/DemoControllerTest.java`\n"
        "- `api_entrypoint`: selected=1 total=1 skipped=0 selected_paths=`src/main/java/com/example/demo/DemoController.java`\n\n"
    )
    summary_path.write_text(text.replace("## 主要阻断项\n\n", audit_section + "## 主要阻断项\n\n", 1), encoding="utf-8")


def test_benchmark_generates_report_for_java_fixture(tmp_path: Path, monkeypatch):
    repo = _copy_fixture_repo(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    assert report["profile"] == "java-spring"
    assert report["status"] == "passed"
    assert report["quality_status"] in {"passed", "degraded"}
    assert "scan_quality" in report["quality_scores"]
    assert "guide_quality" in report["quality_scores"]
    assert "sensor_quality" in report["quality_scores"]
    assert "workflow_quality" in report["quality_scores"]
    assert report["quality_summary"]["total_score"] >= 0
    assert report["checks"]
    assert all(check["passed"] for check in report["checks"])
    check_ids = {check["id"] for check in report["checks"]}
    assert "exists:scan-metadata.yaml" in check_ids
    assert "exists:init-summary.md" in check_ids
    assert "exists:llm-scan-proposal.json" in check_ids
    assert "content:init-summary" in check_ids
    assert "content:workflow-skills" in check_ids
    assert "content:workflow-skill-config-reference" in check_ids
    assert "content:workflow-routing-policy" in check_ids
    assert "content:scan-report" in check_ids
    assert "content:risk-context-consistency" in check_ids
    assert "content:project-context-evidence-context" in check_ids
    assert "content:maturity-routing-evidence" in check_ids
    assert "content:workflow-recommendation-review" in check_ids
    assert "content:maturity-review-artifact" in check_ids
    assert "content:asset-candidate-review" in check_ids
    assert "content:candidate-governance" in check_ids
    assert "content:self-improve-package" in check_ids
    assert "content:experience-summary-artifact" in check_ids
    assert "content:runtime-task-run-artifacts" in check_ids
    assert "content:guides-quality" in check_ids
    assert "content:stack-specific-guides" in check_ids
    assert "content:sensors-quality" in check_ids
    assert "content:weapon-library-selection" in check_ids
    assert "content:hard-gate-command-evidence" in check_ids
    assert "content:harness-map-workflow-skill" not in check_ids
    assert "content:hard-gate-sensors-passed" not in check_ids
    assert "schema:harness-map" not in check_ids
    assert "schema:sensor-report" not in check_ids
    assert "schema:scan-metadata" in check_ids
    assert "schema:llm-scan-proposal" in check_ids
    assert "schema:weapon-library-selection" in check_ids
    assert "schema:benchmark-report" in check_ids
    assert "schema:maturity-score" in check_ids
    assert "schema:maturity-evidence" in check_ids
    assert "schema:improvement-candidates" in check_ids
    assert "schema:experience-index" in check_ids
    assert "exists:runs-trace" in check_ids
    assert "schema:generation-trace" in check_ids
    assert "content:generation-trace" in check_ids
    assert "schema:runtime-summary" not in check_ids
    assert "content:runtime-workflow-trace" not in check_ids
    assert "schema:context-inputs" in check_ids
    assert "schema:questionnaire" in check_ids
    assert "content:human-confirmation" in check_ids
    assert "exists:review/llm-enhancement-candidates.md" in check_ids
    assert "schema:weapon-library-candidates" in check_ids
    assert "content:llm-enhancement-candidates" in check_ids
    assert not (repo / ".ai" / "task-runs").exists()
    trace = _latest_trace(repo)
    assert trace["command"] == "benchmark"
    assert trace["status"] == "completed"
    assert "benchmark" in trace["stages"]


def test_benchmark_generates_consistent_risk_context_for_scan_risk(tmp_path: Path, monkeypatch):
    repo = _copy_fixture_repo(tmp_path, "mini-spring-boot")
    risk_path = "src/main/java/com/example/demo/DemoController.java"
    monkeypatch.setattr(
        "harness_builder_agent.tools.benchmark.scan_repository",
        lambda repo_path: _fake_scan_with_risk(repo_path, "java-spring", risk_path),
    )

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text(encoding="utf-8"))
    check = next(item for item in report["checks"] if item["id"] == "content:risk-context-consistency")
    config = HarnessConfig.model_validate(yaml.safe_load((repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8")))
    standard = next(rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation")
    assert report["status"] == "passed"
    assert check["passed"] is True
    assert check["risk_area_count"] == 1
    assert f"risk_area:{risk_path}" in standard.triggers


def test_benchmark_reports_absent_runtime_task_runs_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)

    report = run_benchmark(repo)
    check = next(item for item in report["checks"] if item["id"] == "content:runtime-task-run-artifacts")

    assert check["passed"] is True
    assert check["present"] is False


def test_benchmark_fails_when_init_summary_missing_confirmation_entry(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    summary_path = repo / ".ai" / "init-summary.md"
    text = summary_path.read_text(encoding="utf-8")
    text = text.replace("## 待人工确认", "## 人工确认")
    text = text.replace(".ai/human-input-needed.md#处理方式", ".ai/human-input-needed.md")
    summary_path.write_text(text, encoding="utf-8")
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.assess_maturity", lambda repo_path: repo_path / ".ai")

    report = run_benchmark(repo)
    check = next(item for item in report["checks"] if item["id"] == "content:init-summary")

    assert check["passed"] is False
    assert report["status"] == "failed"
    assert "## 待人工确认" in check["missing"]
    assert ".ai/human-input-needed.md#处理方式" in check["missing"]


def test_benchmark_passes_when_init_summary_preserves_scan_evidence_audit(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = _add_consistent_scan_report_context(ai)
    _add_consistent_init_summary_evidence_audit(ai)

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:init-summary")
    assert check["passed"] is True


def test_benchmark_fails_when_init_summary_omits_scan_evidence_audit(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = _add_consistent_scan_report_context(ai)
    summary_path = ai / "init-summary.md"
    summary_path.write_text(
        summary_path.read_text(encoding="utf-8").replace("## 扫描证据审计", "## 扫描摘要", 1),
        encoding="utf-8",
    )

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:init-summary")
    assert check["passed"] is False
    assert "## 扫描证据审计" in check["missing"]
    assert "missing_summary_expansion_requested_path:src/main/java/com/example/demo/DemoController.java" in check["missing"]
    assert "missing_summary_coverage_selected_path:src/test/java/com/example/demo/DemoControllerTest.java" in check["missing"]


def test_benchmark_validates_present_runtime_task_runs(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    _write_runtime_task_run(repo / ".ai", task_id="task-1", sensor_status="failed")

    report = run_benchmark(repo)
    check = next(item for item in report["checks"] if item["id"] == "content:runtime-task-run-artifacts")

    assert check["passed"] is True
    assert check["present"] is True
    assert check["task_run_count"] == 1
    assert check["failed_sensor_count"] == 1


def test_benchmark_fails_invalid_runtime_task_run(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    run = _write_runtime_task_run(repo / ".ai", task_id="task-1", sensor_status="failed")
    (run / "runtime-summary.yaml").unlink()

    report = run_benchmark(repo)
    check = next(item for item in report["checks"] if item["id"] == "content:runtime-task-run-artifacts")

    assert check["passed"] is False
    assert "missing_runtime_summary" in check["errors"]
    assert report["status"] == "failed"


def test_benchmark_generates_report_for_dotnet_fixture(tmp_path: Path, monkeypatch):
    repo = _copy_fixture_repo(tmp_path, "mini-dotnet-webapi")
    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, "dotnet-aspnet"))

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "dotnet-aspnet"])

    assert result.exit_code == 0, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text())
    assert report["profile"] == "dotnet-aspnet"
    assert report["status"] == "passed"
    check_ids = {check["id"] for check in report["checks"]}
    assert "content:hard-gate-command-evidence" in check_ids
    assert "schema:benchmark-report" in check_ids


def test_benchmark_fails_when_hard_gate_command_lacks_evidence(tmp_path: Path, monkeypatch):
    repo = _copy_fixture_repo(tmp_path, "mini-spring-boot")

    def fake_scan_without_source(repo_path: Path):
        inventory, commands = _fake_scan(repo_path, "java-spring")
        commands.commands[0].source = ""
        return inventory, commands

    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", fake_scan_without_source)

    result = CliRunner().invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])

    assert result.exit_code == 1, result.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text(encoding="utf-8"))
    assert report["status"] == "failed"
    hard_gate_check = next(check for check in report["checks"] if check["id"] == "content:hard-gate-command-evidence")
    assert hard_gate_check["passed"] is False
    assert hard_gate_check["weak_commands"] == [
        {"id": "unit_test", "source": "", "confidence": "high", "reason": "missing_source"}
    ]


def test_benchmark_fails_when_hard_gate_command_source_path_is_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    catalog_path = repo / ".ai" / "command-catalog.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    catalog["commands"][0]["source"] = "docs/testing.md"
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True), encoding="utf-8")

    report = run_benchmark(repo)
    hard_gate_check = next(check for check in report["checks"] if check["id"] == "content:hard-gate-command-evidence")

    assert report["status"] == "failed"
    assert hard_gate_check["passed"] is False
    assert hard_gate_check["weak_commands"] == [
        {"id": "unit_test", "source": "docs/testing.md", "confidence": "high", "reason": "source_path_missing"}
    ]


def test_benchmark_fails_when_hard_gate_command_source_path_escapes_repo(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    catalog_path = repo / ".ai" / "command-catalog.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    catalog["commands"][0]["source"] = "../outside.md"
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True), encoding="utf-8")

    report = run_benchmark(repo)
    hard_gate_check = next(check for check in report["checks"] if check["id"] == "content:hard-gate-command-evidence")

    assert report["status"] == "failed"
    assert hard_gate_check["passed"] is False
    assert hard_gate_check["weak_commands"] == [
        {"id": "unit_test", "source": "../outside.md", "confidence": "high", "reason": "source_path_outside_repo"}
    ]


def test_benchmark_passes_when_scan_risk_context_is_consistent(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = _add_consistent_risk_context(ai, "src/main/java/com/example/demo/DemoController.java")

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:risk-context-consistency")
    assert check["passed"] is True
    assert check["risk_area_count"] == 1


def test_benchmark_fails_when_project_context_omits_scan_risk_path(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    risk_path = "src/main/java/com/example/demo/DemoController.java"
    inventory = _add_consistent_risk_context(ai, risk_path)
    guide_path = ai / "guides" / "project-context.md"
    guide_path.write_text(
        guide_path.read_text(encoding="utf-8").replace(risk_path, "src/main/java/com/example/demo/OtherController.java"),
        encoding="utf-8",
    )

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:risk-context-consistency")
    assert check["passed"] is False
    assert f"missing_project_context_risk:{risk_path}" in check["errors"]


def test_benchmark_fails_when_verification_sensor_omits_scan_risk_path(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    risk_path = "src/main/java/com/example/demo/DemoController.java"
    inventory = _add_consistent_risk_context(ai, risk_path)
    sensor_path = ai / "sensors" / "verification.md"
    sensor_path.write_text(
        sensor_path.read_text(encoding="utf-8").replace(risk_path, "src/main/java/com/example/demo/OtherController.java"),
        encoding="utf-8",
    )

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:risk-context-consistency")
    assert check["passed"] is False
    assert f"missing_verification_sensor_risk:{risk_path}" in check["errors"]


def test_benchmark_fails_when_routing_policy_omits_scan_risk_path_for_consistency(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    risk_path = "src/main/java/com/example/demo/DemoController.java"
    inventory = _add_consistent_risk_context(ai, risk_path)
    config_path = ai / "harness-config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    standard = next(rule for rule in config["workflow_routing"]["rules"] if rule["id"] == "standard-escalation")
    standard["triggers"] = [trigger for trigger in standard["triggers"] if trigger != f"risk_area:{risk_path}"]
    standard["rationale"] = "Generic standard escalation."
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:risk-context-consistency")
    assert check["passed"] is False
    assert f"missing_routing_risk:{risk_path}" in check["errors"]


def test_benchmark_passes_when_project_context_preserves_evidence_context(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = _add_consistent_project_context_evidence_context(ai)

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:project-context-evidence-context")
    assert check["passed"] is True
    assert check["evidence_path_count"] >= 4


def test_benchmark_fails_when_project_context_omits_evidence_path(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))
    guide_path = ai / "guides" / "project-context.md"
    guide_path.write_text(guide_path.read_text(encoding="utf-8").replace("pom.xml", "pom-hidden.xml"), encoding="utf-8")

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:project-context-evidence-context")
    assert check["passed"] is False
    assert "missing_evidence_path:pom.xml" in check["missing"]


def test_benchmark_fails_when_project_context_omits_llm_evidence_expansion_section(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))
    guide_path = ai / "guides" / "project-context.md"
    guide_path.write_text(guide_path.read_text(encoding="utf-8").replace("## LLM 证据扩展", "## LLM 深扫"), encoding="utf-8")

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:project-context-evidence-context")
    assert check["passed"] is False
    assert "missing_llm_evidence_expansion_section" in check["missing"]


def test_benchmark_fails_when_project_context_omits_llm_evidence_expansion_detail(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = _add_consistent_project_context_evidence_context(ai)
    guide_path = ai / "guides" / "project-context.md"
    guide_path.write_text(
        guide_path.read_text(encoding="utf-8")
        .replace("`src/main/java/com/example/demo/DemoController.java`", "`src/main/java/com/example/demo/OtherController.java`")
        .replace("read_file_count=1", "read_file_count=0")
        .replace("Controller route ownership needed deeper inspection.", "rationale removed."),
        encoding="utf-8",
    )

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:project-context-evidence-context")
    assert check["passed"] is False
    assert "missing_expansion_requested_path:src/main/java/com/example/demo/DemoController.java" in check["missing"]
    assert "missing_expansion_read_path:src/main/java/com/example/demo/DemoController.java" in check["missing"]
    assert "missing_expansion_read_file_count:1" in check["missing"]
    assert "missing_expansion_rationale" in check["missing"]


def test_benchmark_passes_when_scan_report_preserves_evidence_context(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = _add_consistent_scan_report_context(ai)

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:scan-report")
    assert check["passed"] is True


def test_benchmark_scan_report_allows_later_command_confidence_edits(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = _add_consistent_scan_report_context(ai)
    catalog_path = ai / "command-catalog.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    catalog["commands"][0]["confidence"] = "low"
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True), encoding="utf-8")

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:scan-report")
    assert check["passed"] is True


def test_benchmark_fails_when_scan_report_omits_required_audit_section(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))
    report = ai / "scan-report.md"
    report.write_text(report.read_text(encoding="utf-8").replace("## Evidence\n\n", "## Source Evidence\n\n", 1), encoding="utf-8")

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:scan-report")
    assert check["passed"] is False
    assert "## Evidence" in check["missing"]


def test_benchmark_fails_when_scan_report_omits_coverage_selected_path(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = _add_consistent_scan_report_context(ai)
    report = ai / "scan-report.md"
    report.write_text(
        report.read_text(encoding="utf-8").replace(
            "`src/test/java/com/example/demo/DemoControllerTest.java`",
            "`src/test/java/com/example/demo/OtherTest.java`",
        ),
        encoding="utf-8",
    )

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:scan-report")
    assert check["passed"] is False
    assert "missing_coverage_selected_path:src/test/java/com/example/demo/DemoControllerTest.java" in check["missing"]


def test_benchmark_fails_when_scan_report_omits_llm_evidence_expansion_detail(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = _add_consistent_scan_report_context(ai)
    report = ai / "scan-report.md"
    report.write_text(
        report.read_text(encoding="utf-8")
        .replace("`src/main/java/com/example/demo/DemoController.java`", "`src/main/java/com/example/demo/OtherController.java`")
        .replace("read_file_count=1", "read_file_count=0")
        .replace("Controller route ownership needed deeper inspection.", "rationale removed."),
        encoding="utf-8",
    )

    checks = _content_checks(ai, inventory)

    check = next(item for item in checks if item["id"] == "content:scan-report")
    assert check["passed"] is False
    assert "missing_expansion_requested_path:src/main/java/com/example/demo/DemoController.java" in check["missing"]
    assert "missing_expansion_read_path:src/main/java/com/example/demo/DemoController.java" in check["missing"]
    assert "missing_expansion_read_file_count:1" in check["missing"]
    assert "missing_expansion_rationale" in check["missing"]


def test_benchmark_fails_weapon_library_candidates_with_invalid_status(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    path = ai / "experience" / "weapon-library-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["status"] = "applied"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    checks = _llm_enhancement_checks(ai)

    schema = next(check for check in checks if check["id"] == "schema:weapon-library-candidates")
    assert schema["passed"] is False


def test_benchmark_fails_invalid_questionnaire_schema(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    path = ai / "questionnaire.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["questions"][0]["interaction_type"] = "unknown"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    checks = _human_confirmation_checks(ai)

    questionnaire = next(check for check in checks if check["id"] == "schema:questionnaire")
    assert questionnaire["passed"] is False


def test_benchmark_schema_checks_fail_when_project_inventory_is_invalid(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    (ai / "project-inventory.json").write_text("{not valid json", encoding="utf-8")

    checks = _schema_checks(ai)

    project_inventory = next(check for check in checks if check["id"] == "schema:project-inventory")
    assert project_inventory["passed"] is False
    assert project_inventory["error"]


def test_benchmark_content_checks_fail_when_guide_required_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    (ai / "guides" / "project-context.md").write_text("# Project Context\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    guide_check = next(check for check in checks if check["id"] == "content:guides-quality")
    stack_check = next(check for check in checks if check["id"] == "content:stack-specific-guides")
    assert guide_check["passed"] is False
    assert stack_check["passed"] is False


def test_benchmark_quality_degrades_when_guide_lacks_evidence_reference(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    guide = ai / "guides" / "project-context.md"
    guide.write_text(guide.read_text(encoding="utf-8").replace("## 来源证据", "## 来源说明"), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    scores = _quality_scores(ai, inventory)

    item = scores["guide_quality"]["evidence_reference"]
    assert item["score"] < 5
    assert item["passed"] is False
    assert item["reasons"]


def test_benchmark_degrades_command_reliability_for_low_confidence_hard_gate(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    catalog_path = ai / "command-catalog.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    catalog["commands"][0]["confidence"] = "low"
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    scores = _quality_scores(ai, inventory)

    item = scores["scan_quality"]["command_reliability"]
    assert item["score"] < 4
    assert item["passed"] is False
    assert item["reasons"]


def test_benchmark_content_checks_fail_when_workflow_skill_file_is_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    (ai / "skills" / "standard" / "SKILL.md").unlink()
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    workflow_skill = next(check for check in checks if check["id"] == "content:workflow-skills")
    harness_map_skill = next(check for check in checks if check["id"] == "content:workflow-skill-config-reference")
    assert workflow_skill["passed"] is False
    assert harness_map_skill["passed"] is False


def test_benchmark_content_checks_fail_when_standard_routing_rule_is_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    config_path = ai / "harness-config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["workflow_routing"]["rules"] = [
        rule for rule in config["workflow_routing"]["rules"] if rule["id"] != "standard-escalation"
    ]
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    routing_policy = next(check for check in checks if check["id"] == "content:workflow-routing-policy")
    assert routing_policy["passed"] is False
    assert "missing_standard_escalation" in routing_policy["errors"]


def test_benchmark_content_checks_fail_when_maturity_routing_evidence_is_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    evidence_path = ai / "maturity-evidence.yaml"
    evidence = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    evidence["harness_assets"]["workflow_routing_rules"] = []
    evidence_path.write_text(yaml.safe_dump(evidence, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    routing_evidence = next(check for check in checks if check["id"] == "content:maturity-routing-evidence")
    assert routing_evidence["passed"] is False
    assert "missing_routing_evidence_detail" in routing_evidence["errors"]


def test_benchmark_records_absent_workflow_recommendation_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is True
    assert recommendation["present"] is False


def test_benchmark_records_absent_asset_candidates_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is True
    assert asset_candidates["present"] is False


def test_benchmark_records_absent_candidate_governance_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    governance = next(check for check in checks if check["id"] == "content:candidate-governance")
    assert governance["passed"] is True
    assert governance["present"] is False


def test_benchmark_records_absent_maturity_review_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is True
    assert review["present"] is False


def test_benchmark_records_absent_self_improve_package_as_optional(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    package = next(check for check in checks if check["id"] == "content:self-improve-package")
    assert package["passed"] is True
    assert package["present"] is False


def test_benchmark_validates_self_improve_package_artifact(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    _write_valid_asset_candidates(ai)
    _write_valid_self_improve_package(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    package = next(check for check in checks if check["id"] == "content:self-improve-package")
    assert package["passed"] is True
    assert package["present"] is True
    assert package["asset_candidate_count"] == 1


def test_benchmark_accepts_valid_maturity_review_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is True
    assert review["present"] is True
    assert review["candidate_review_count"] == 1


def test_benchmark_fails_maturity_review_with_unknown_candidate(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    path = ai / "review" / "maturity-review.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidate_reviews"][0]["candidate_id"] = "missing-candidate"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is False
    assert "unknown_candidate_id" in review["errors"]


def test_benchmark_fails_maturity_review_with_outside_ai_evidence(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    path = ai / "review" / "maturity-review.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidate_reviews"][0]["evidence_sources"] = ["README.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is False
    assert "evidence_source_outside_ai" in review["errors"]


def test_benchmark_fails_maturity_review_with_unknown_evidence_source(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    path = ai / "review" / "maturity-review.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidate_reviews"][0]["evidence_sources"] = [".ai/review/missing.yaml"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is False
    assert "unknown_evidence_source" in review["errors"]


def test_benchmark_fails_maturity_review_when_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    (ai / "review" / "maturity-review.md").write_text("# Maturity Review\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is False
    assert "missing_markdown_sections" in review["errors"]


def test_benchmark_fails_maturity_review_without_review_boundary(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_maturity_review(ai)
    markdown = (ai / "review" / "maturity-review.md").read_text(encoding="utf-8")
    markdown = markdown.replace("\n## Review Boundary\n\n- review status: `pending_harness_maintainer_review`\n", "")
    (ai / "review" / "maturity-review.md").write_text(markdown, encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    review = next(check for check in checks if check["id"] == "content:maturity-review-artifact")
    assert review["passed"] is False
    assert "missing_markdown_sections" in review["errors"]


def test_benchmark_accepts_valid_asset_candidate_review_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is True
    assert asset_candidates["present"] is True
    assert asset_candidates["candidate_count"] == 1


def test_benchmark_accepts_valid_candidate_governance_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    _write_valid_candidate_governance(ai)

    check = _candidate_governance_check(ai)

    assert check["passed"] is True
    assert check["present"] is True
    assert check["decision_count"] == 1


def test_benchmark_preserves_applied_workflow_policy_candidate(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    review_candidate(
        repo,
        candidate_id="workflow-routing-policy-review",
        decision="applied",
        rationale="Maintainer accepted the routing patch.",
        reviewer="harness-maintainer",
    )

    report = run_benchmark(repo, "java-spring")

    config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
    standard = next(rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation")
    check_by_id = {check["id"]: check for check in report["checks"]}
    assert "domain_policy_change" in standard.triggers
    assert check_by_id["content:workflow-routing-policy"]["passed"] is True
    assert check_by_id["content:maturity-routing-evidence"]["passed"] is True
    assert check_by_id["content:candidate-governance"]["passed"] is True


def test_benchmark_fails_candidate_governance_with_unknown_candidate(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    _write_valid_candidate_governance(ai)
    path = ai / "review" / "candidate-governance.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["decisions"][0]["candidate_id"] = "missing-candidate"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    check = _candidate_governance_check(ai)

    assert check["passed"] is False
    assert "unknown_candidate_id" in check["errors"]


def test_benchmark_fails_candidate_governance_with_mismatched_suggested_path(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    _write_valid_candidate_governance(ai)
    path = ai / "review" / "candidate-governance.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["decisions"][0]["suggested_path"] = ".ai/guides/project-context.md"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    check = _candidate_governance_check(ai)

    assert check["passed"] is False
    assert "suggested_path_mismatch" in check["errors"]


def test_benchmark_fails_candidate_governance_with_outside_ai_applied_path(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    _write_valid_candidate_governance(ai)
    path = ai / "review" / "candidate-governance.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["decisions"][0]["decision"] = "applied"
    payload["decisions"][0]["applied_paths"] = ["README.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    check = _candidate_governance_check(ai)

    assert check["passed"] is False
    assert "applied_path_outside_ai" in check["errors"]


def test_benchmark_fails_candidate_governance_with_path_traversal_applied_path(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    _write_valid_candidate_governance(ai)
    path = ai / "review" / "candidate-governance.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["decisions"][0]["decision"] = "applied"
    payload["decisions"][0]["applied_paths"] = [".ai/../README.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    check = _candidate_governance_check(ai)

    assert check["passed"] is False
    assert "applied_path_outside_ai" in check["errors"]


def test_benchmark_fails_applied_workflow_policy_without_supported_review(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    review_candidate(
        repo,
        candidate_id="workflow-routing-policy-review",
        decision="applied",
        rationale="Maintainer accepted the routing patch.",
        reviewer="harness-maintainer",
    )
    path = ai / "review" / "asset-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["source_review_decision"] = "defer"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    check = _candidate_governance_check(ai)

    assert check["passed"] is False
    assert "workflow_policy_applied_without_supported_review" in check["errors"]


def test_benchmark_fails_asset_candidate_with_unknown_source_candidate(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    path = ai / "review" / "asset-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["source_candidate_id"] = "missing-candidate"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "unknown_source_candidate_id" in asset_candidates["errors"]


def test_benchmark_fails_asset_candidate_with_path_traversal_suggested_path(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    path = ai / "review" / "asset-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["suggested_path"] = ".ai/../README.md"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "suggested_path_outside_ai" in asset_candidates["errors"]


def test_benchmark_fails_workflow_policy_asset_candidate_with_non_config_target(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    path = ai / "review" / "asset-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["suggested_path"] = ".ai/guides/project-context.md"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "workflow_policy_target_not_harness_config" in asset_candidates["errors"]


def test_benchmark_fails_asset_candidate_with_outside_ai_evidence(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    path = ai / "review" / "asset-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["evidence_sources"] = ["README.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "evidence_source_outside_ai" in asset_candidates["errors"]


def test_benchmark_fails_asset_candidate_with_unknown_evidence_source(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    path = ai / "review" / "asset-candidates.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["candidates"][0]["evidence_sources"] = [".ai/review/missing.yaml"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "unknown_evidence_source" in asset_candidates["errors"]


def test_benchmark_fails_asset_candidate_when_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_asset_candidates(ai)
    (ai / "review" / "asset-candidate-workflows.md").write_text("# Asset Candidate Workflows\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    asset_candidates = next(check for check in checks if check["id"] == "content:asset-candidate-review")
    assert asset_candidates["passed"] is False
    assert "missing_markdown_sections" in asset_candidates["errors"]


def test_benchmark_accepts_valid_workflow_recommendation_review_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is True
    assert recommendation["present"] is True
    assert recommendation["recommended_workflow"] == "bugfix"
    assert recommendation["history_count"] == 0


def test_benchmark_fails_workflow_recommendation_history_when_markdown_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    _write_valid_workflow_recommendation_history(ai)
    missing = next((ai / "review" / "workflow-routing-recommendations").glob("task-1-*.md"))
    missing.unlink()
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is False
    assert "incomplete_recommendation_history_entry" in recommendation["errors"]


def test_benchmark_fails_when_workflow_recommendation_references_unknown_workflow(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    path = ai / "review" / "workflow-routing-recommendation.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["recommended_workflow"] = "release"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is False
    assert "unknown_recommended_workflow" in recommendation["errors"]


def test_benchmark_fails_when_workflow_recommendation_references_unknown_rule(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    path = ai / "review" / "workflow-routing-recommendation.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["matched_rule_ids"] = ["missing-rule"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is False
    assert "unknown_matched_rule_ids" in recommendation["errors"]


def test_benchmark_fails_workflow_recommendation_with_unknown_evidence_source(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    path = ai / "review" / "workflow-routing-recommendation.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["evidence_sources"] = [".ai/review/missing.yaml"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is False
    assert "unknown_evidence_source" in recommendation["errors"]


def test_benchmark_fails_when_workflow_recommendation_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_workflow_recommendation(ai)
    (ai / "review" / "workflow-routing-recommendation.md").write_text("# Workflow Routing Recommendation\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    recommendation = next(check for check in checks if check["id"] == "content:workflow-recommendation-review")
    assert recommendation["passed"] is False
    assert "missing_markdown_sections" in recommendation["errors"]


def test_benchmark_accepts_valid_experience_summary_artifacts(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_experience_summary(ai)
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    summary = next(check for check in checks if check["id"] == "content:experience-summary-artifact")
    assert summary["passed"] is True
    assert summary["present"] is True
    assert summary["finding_count"] == 1


def test_benchmark_fails_experience_summary_with_outside_ai_evidence(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_experience_summary(ai)
    path = ai / "experience" / "experience-summary.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["findings"][0]["evidence_sources"] = ["README.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    summary = next(check for check in checks if check["id"] == "content:experience-summary-artifact")
    assert summary["passed"] is False
    assert "evidence_source_outside_ai" in summary["errors"]


def test_benchmark_fails_experience_summary_with_unknown_evidence_source(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_experience_summary(ai)
    path = ai / "experience" / "experience-summary.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["findings"][0]["evidence_sources"] = [".ai/experience/missing.md"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    summary = next(check for check in checks if check["id"] == "content:experience-summary-artifact")
    assert summary["passed"] is False
    assert "unknown_evidence_source" in summary["errors"]


def test_benchmark_fails_experience_summary_with_absent_optional_source(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_experience_summary(ai)
    path = ai / "experience" / "experience-summary.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["findings"][0]["evidence_sources"] = [".ai/review/asset-candidates.yaml"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    summary = next(check for check in checks if check["id"] == "content:experience-summary-artifact")
    assert summary["passed"] is False
    assert "unknown_evidence_source" in summary["errors"]


def test_benchmark_fails_experience_summary_when_markdown_sections_are_missing(tmp_path: Path, monkeypatch):
    repo = _prepare_passed_benchmark_repo(tmp_path, monkeypatch)
    ai = repo / ".ai"
    _write_valid_experience_summary(ai)
    (ai / "experience" / "experience-summary.md").write_text("# Experience Summary\n", encoding="utf-8")
    inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))

    checks = _content_checks(ai, inventory)

    summary = next(check for check in checks if check["id"] == "content:experience-summary-artifact")
    assert summary["passed"] is False
    assert "missing_markdown_sections" in summary["errors"]
