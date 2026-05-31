import pytest
from pydantic import ValidationError

from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.harness_map import HarnessMap
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.sensor_report import SensorReport
from harness_builder_agent.schemas.scan import EvidenceBundle, EvidenceBucketCoverage, EvidenceCoverage, EvidenceFile, ScanMetadata
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidateReport
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport


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


def test_weapon_library_candidate_report_rejects_invalid_status():
    with pytest.raises(ValidationError):
        WeaponLibraryCandidateReport.model_validate(
            {
                "schema_version": "1.0",
                "source": "llm_scan_proposal",
                "candidates": [
                    {
                        "id": "llm-guide-001",
                        "candidate_type": "guide",
                        "status": "applied",
                        "title": "Guide",
                        "rationale": "Needs review.",
                        "evidence": [".ai/project-inventory.json"],
                        "source": "llm_scan_proposal",
                        "human_confirmation_required": True,
                    }
                ],
            }
        )


def test_evidence_bundle_records_priority_buckets_and_coverage():
    bundle = EvidenceBundle(
        repo_name="large-repo",
        root_path="/tmp/large-repo",
        files=[EvidenceFile(path="pom.xml", kind="build", priority="critical", reason="Maven build file", bucket="build")],
        priority_files=[EvidenceFile(path="pom.xml", kind="build", priority="critical", reason="Maven build file", bucket="build")],
        test_files=[EvidenceFile(path="quality/checks/UserFlowSpec.cs", kind="test", priority="high", bucket="test")],
        api_entrypoints=[EvidenceFile(path="src/api/UserController.java", kind="api_entrypoint", priority="critical", bucket="api_entrypoint")],
        risk_files=[EvidenceFile(path="src/security/AuthConfig.java", kind="risk", priority="high", bucket="risk")],
        coverage=EvidenceCoverage(
            detected_file_count=120,
            selected_evidence_count=4,
            bucket_coverage=[
                EvidenceBucketCoverage(
                    bucket="source:.java",
                    total_count=80,
                    selected_count=2,
                    skipped_count=78,
                    selected_paths=["src/api/UserController.java"],
                )
            ],
            warnings=[{"code": "source_sampling_truncated", "message": "source:.java had skipped files"}],
        ),
    )

    payload = bundle.model_dump(mode="json")

    assert payload["files"][0]["priority"] == "critical"
    assert payload["priority_files"][0]["bucket"] == "build"
    assert payload["coverage"]["bucket_coverage"][0]["skipped_count"] == 78
    assert payload["coverage"]["warnings"][0]["code"] == "source_sampling_truncated"


def test_scan_metadata_accepts_evidence_coverage():
    metadata = ScanMetadata(
        prompt_version="test",
        evidence_file_count=120,
        coverage={
            "schema_version": "1.0",
            "detected_file_count": 120,
            "selected_evidence_count": 10,
            "bucket_coverage": [
                {
                    "bucket": "test",
                    "total_count": 3,
                    "selected_count": 2,
                    "skipped_count": 1,
                    "selected_paths": ["quality/checks/UserFlowSpec.cs"],
                }
            ],
            "warnings": [],
        },
    )

    assert metadata.coverage["selected_evidence_count"] == 10


def test_benchmark_report_accepts_quality_scores():
    report = BenchmarkReport(
        repo_name="demo",
        profile="java-spring",
        status="passed",
        quality_status="degraded",
        checks=[{"id": "content:guides-quality", "passed": True}],
        quality_scores={
            "guide_quality": {
                "evidence_reference": {
                    "score": 3,
                    "max_score": 5,
                    "passed": False,
                    "reasons": ["来源证据章节存在但缺少路径。"],
                    "recommendations": ["在 guide 中补充 evidence path。"],
                }
            }
        },
        quality_summary={
            "total_score": 60,
            "minimum_score": 3,
            "degraded_items": ["guide_quality.evidence_reference"],
            "failed_items": [],
        },
    )

    payload = report.model_dump(mode="json")

    assert payload["quality_status"] == "degraded"
    assert payload["quality_scores"]["guide_quality"]["evidence_reference"]["score"] == 3
    assert payload["quality_summary"]["degraded_items"] == ["guide_quality.evidence_reference"]


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

    assert {"lightweight", "bugfix", "standard"}.issubset(workflow_names)
    assert config.workflows["lightweight"].skill_path == ".ai/skills/lightweight/SKILL.md"
    assert config.workflows["bugfix"].skill_path == ".ai/skills/bugfix/SKILL.md"
    assert config.workflows["standard"].skill_path == ".ai/skills/standard/SKILL.md"
    assert "solution_design" in config.workflows["standard"].stages
    assert "test_first_build_verify" in config.workflows["standard"].stages
    assert config.runtime.default_workflow == "lightweight"
    assert config.sensors.max_repair_attempts == 1
    routing = config.workflow_routing
    rule_ids = {rule.id for rule in routing.rules}
    assert routing.default_workflow == "lightweight"
    assert {"bugfix-intent", "low-risk-lightweight", "standard-escalation"}.issubset(rule_ids)
    standard_rule = next(rule for rule in routing.rules if rule.id == "standard-escalation")
    assert standard_rule.selected_workflow == "standard"
    assert standard_rule.human_confirmation_required is True
    assert "cross_module_design" in standard_rule.triggers
    assert "security_or_permission" in standard_rule.triggers
    assert "insufficient_sensor_coverage" in standard_rule.triggers


# These schemas are retained as future AI Coding Runtime artifact contracts.
# Harness Builder no longer generates these files itself.
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


def test_harness_map_accepts_standard_workflow_contract():
    harness_map = HarnessMap.model_validate(
        {
            "task_id": "demo-task-002",
            "task_type": "standard",
            "selected_workflow": "standard",
            "risk_level": "high",
            "guide_policy": {"required": [".ai/guides/architecture.md"]},
            "workflow_skill": {"path": ".ai/skills/standard/SKILL.md"},
            "sensor_policy": {"hard_gates": ["unit_test"]},
        }
    )

    assert harness_map.selected_workflow == "standard"


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


def test_maturity_report_records_structured_dimension_roadmap():
    report = MaturityReport.model_validate(
        {
            "overall_level": "L2",
            "target_next_level": "L3",
            "dimension_scores": {"guides": "L2"},
            "dimensions": {
                "guides": {
                    "level": "L2",
                    "evidence": [{"source": ".ai/guides/project-context.md", "summary": "Structured project facts exist."}],
                    "blockers": [
                        {
                            "id": "guides-not-risk-routed",
                            "reason": "Guides are not loaded by risk context.",
                            "prevents_level": "L3",
                        }
                    ],
                    "next_level_requirements": ["Bind guides to workflow routing."],
                    "confidence": "high",
                }
            },
            "blocking_caps": [
                {
                    "id": "no-runtime-audit",
                    "reason": "No runtime audit events were found.",
                    "max_level": "L3",
                    "active": True,
                    "evidence": [".ai/task-runs absent"],
                }
            ],
            "next_steps": [
                {
                    "id": "bind-guides-to-workflow",
                    "target_dimension": "guides",
                    "action": "Bind project guides to workflow routing.",
                    "priority": "high",
                    "expected_lift": "guides L2 -> L3",
                }
            ],
            "evidence": ["summary"],
            "blocking_reasons": ["blocker"],
            "recommended_next_steps": ["next"],
        }
    )

    assert report.target_next_level == "L3"
    assert report.dimensions["guides"].evidence[0].source == ".ai/guides/project-context.md"
    assert report.dimensions["guides"].blockers[0].prevents_level == "L3"
    assert report.blocking_caps[0].active is True
    assert report.next_steps[0].target_dimension == "guides"


def test_maturity_evidence_pack_records_harness_inputs_for_review():
    pack = MaturityEvidencePack.model_validate(
        {
            "repo_name": "demo",
            "primary_stack": "java-spring",
            "inventory_summary": {"module_count": 2, "evidence_count": 3, "risk_area_count": 1},
            "command_summary": {"total_count": 2, "hard_gate_count": 1, "soft_gate_count": 1, "command_ids": ["unit_test"]},
            "harness_assets": {
                "guide_count": 3,
                "sensor_count": 2,
                "workflow_skill_count": 2,
                "has_harness_config": True,
                "has_weapon_library_selection": True,
                "workflow_routing_rules": [
                    {
                        "id": "standard-escalation",
                        "selected_workflow": "standard",
                        "task_type_hints": ["feature"],
                        "triggers": ["high_risk_module", "security_or_permission"],
                        "required_guides": [".ai/guides/architecture.md"],
                        "required_sensors": [".ai/sensors/verification.md"],
                        "human_confirmation_required": True,
                        "rationale": "Escalate risky work.",
                    }
                ],
            },
            "observability": {
                "generation_run_count": 1,
                "has_runtime_task_runs": False,
                "latest_generation_status": "completed",
            },
            "experience": {
                "has_pending_improvements": True,
                "pending_improvement_count": 2,
                "has_experience_index": True,
                "asset_candidate_count": 1,
                "maturity_review_count": 1,
                "runtime_task_run_count": 0,
                "experience_file_count": 6,
                "has_experience_summary": True,
                "experience_summary_finding_count": 1,
            },
            "benchmark": {"has_report": True, "status": "passed"},
            "maturity_inputs": [".ai/project-inventory.json", ".ai/command-catalog.yaml"],
            "warnings": ["runtime task-runs absent"],
        }
    )

    assert pack.schema_version == "1.0"
    assert pack.command_summary.hard_gate_count == 1
    assert pack.observability.has_runtime_task_runs is False
    assert pack.experience.has_experience_index is True
    assert pack.experience.asset_candidate_count == 1
    assert pack.experience.experience_file_count == 6
    assert pack.experience.has_experience_summary is True
    assert pack.experience.experience_summary_finding_count == 1
    assert pack.harness_assets.workflow_routing_rules[0].id == "standard-escalation"
    assert "security_or_permission" in pack.harness_assets.workflow_routing_rules[0].triggers


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
                    "target_dimension": "guides",
                    "source_next_step": "guides-bind-workflow",
                    "source_blocking_cap": None,
                    "acceptance_checks": ["Benchmark content:guides-quality passes."],
                    "evidence_sources": [".ai/maturity-evidence.yaml", ".ai/project-inventory.json"],
                }
            ]
        }
    )

    assert report.candidates[0].suggested_target.startswith(".ai/")
    assert report.candidates[0].human_confirmation_required is True
    assert report.candidates[0].target_dimension == "guides"
    assert report.candidates[0].source_next_step == "guides-bind-workflow"
    assert report.candidates[0].acceptance_checks == ["Benchmark content:guides-quality passes."]
    assert ".ai/maturity-evidence.yaml" in report.candidates[0].evidence_sources


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


def test_maturity_review_report_records_candidate_judgment():
    report = MaturityReviewReport.model_validate(
        {
            "summary": "Candidates are directionally useful but need stronger acceptance checks.",
            "reviewer_model": "deepseek-test",
            "candidate_reviews": [
                {
                    "candidate_id": "maturity-next-step-guides",
                    "decision": "revise",
                    "rationale": "Guide update should be scoped to project-context first.",
                    "risks": ["May overgeneralize local rules."],
                    "suggested_acceptance_checks": ["Benchmark content:guides-quality passes."],
                    "evidence_sources": [".ai/maturity-evidence.yaml"],
                }
            ],
            "missing_candidates": ["Add runtime observability candidate."],
            "global_risks": ["No runtime task-runs are available."],
        }
    )

    assert report.schema_version == "1.0"
    assert report.candidate_reviews[0].decision == "revise"
    assert report.global_risks


def test_maturity_review_report_rejects_invalid_decision():
    with pytest.raises(ValidationError):
        MaturityReviewReport.model_validate(
            {
                "summary": "bad",
                "candidate_reviews": [
                    {
                        "candidate_id": "candidate-1",
                        "decision": "approve",
                        "rationale": "bad enum",
                    }
                ],
            }
        )


def test_asset_candidate_report_records_review_only_drafts():
    report = AssetCandidateReport.model_validate(
        {
            "candidates": [
                {
                    "id": "guide-project-context-scope",
                    "kind": "guide",
                    "source_candidate_id": "candidate-1",
                    "source_review_decision": "revise",
                    "suggested_path": ".ai/guides/project-context.md",
                    "title": "Scope project context guide",
                    "rationale": "The guide needs a more explicit task loading scope.",
                    "draft_content": "## Candidate Addition\n\nAdd task loading scope.",
                    "evidence_sources": [".ai/maturity-evidence.yaml"],
                    "acceptance_checks": ["Benchmark content:guides-quality passes."],
                    "risk_level": "medium",
                    "review_status": "pending_harness_maintainer_review",
                }
            ]
        }
    )

    assert report.schema_version == "1.0"
    assert report.candidates[0].kind == "guide"
    assert report.candidates[0].review_status == "pending_harness_maintainer_review"


def test_asset_candidate_report_rejects_invalid_kind():
    with pytest.raises(ValidationError):
        AssetCandidateReport.model_validate(
            {
                "candidates": [
                    {
                        "id": "bad",
                        "kind": "unknown",
                        "source_review_decision": "support",
                        "suggested_path": ".ai/guides/project-context.md",
                        "title": "Bad",
                        "rationale": "Bad kind.",
                        "draft_content": "content",
                    }
                ]
            }
        )


def test_workflow_recommendation_report_records_review_only_routing_judgment():
    report = WorkflowRecommendationReport.model_validate(
        {
            "task_id": "task-1",
            "task_brief": "Fix checkout permission bug.",
            "recommended_workflow": "bugfix",
            "matched_rule_ids": ["bugfix-intent"],
            "risk_level": "medium",
            "confidence": "high",
            "rationale": "Bugfix intent matches the configured routing rule.",
            "required_guides": [".ai/guides/task-templates/bugfix.md"],
            "required_sensors": [".ai/sensors/verification.md"],
            "human_confirmation_required": False,
            "review_status": "pending_harness_maintainer_review",
            "evidence_sources": [".ai/harness-config.yaml", ".ai/maturity-evidence.yaml"],
        }
    )

    assert report.schema_version == "1.0"
    assert report.recommended_workflow == "bugfix"
    assert report.review_status == "pending_harness_maintainer_review"


def test_workflow_recommendation_report_rejects_invalid_review_status():
    with pytest.raises(ValidationError):
        WorkflowRecommendationReport.model_validate(
            {
                "task_id": "task-1",
                "task_brief": "Fix checkout permission bug.",
                "recommended_workflow": "bugfix",
                "rationale": "Bad status.",
                "review_status": "applied",
            }
        )


def test_experience_index_records_sources_and_counts():
    index = ExperienceIndex.model_validate(
        {
            "experience_files": {
                "project-experience.md": True,
                "repair-patterns.md": True,
                "sensor-feedback.md": True,
                "team-preferences.md": True,
                "pending-improvements.md": True,
                "deprecated-experience.md": True,
            },
            "sources": [
                {"path": ".ai/experience/pending-improvements.md", "kind": "pending_improvements", "item_count": 2},
                {"path": ".ai/review/workflow-routing-recommendation.yaml", "kind": "workflow_recommendation", "item_count": 1},
            ],
            "pending_improvement_count": 2,
            "asset_candidate_count": 1,
            "maturity_review_count": 1,
            "workflow_recommendation_count": 1,
            "runtime_task_run_count": 0,
            "warnings": ["runtime task-runs absent"],
        }
    )

    assert index.schema_version == "1.0"
    assert index.sources[0].kind == "pending_improvements"
    assert index.sources[1].kind == "workflow_recommendation"
    assert index.workflow_recommendation_count == 1


def test_experience_summary_report_records_review_only_findings():
    report = ExperienceSummaryReport.model_validate(
        {
            "summary": "Repeated sensor gaps are blocking maturity improvement.",
            "findings": [
                {
                    "id": "sensor-feedback-coverage-gap",
                    "kind": "sensor_feedback",
                    "title": "Coverage gap blocks confidence",
                    "summary": "Pending improvements repeatedly mention missing sensor coverage.",
                    "evidence_sources": [".ai/experience/pending-improvements.md"],
                    "confidence": "medium",
                    "suggested_follow_up": "Create a reviewed sensor candidate.",
                }
            ],
            "warnings": ["Runtime task-runs are absent."],
        }
    )

    assert report.schema_version == "1.0"
    assert report.source == "llm_experience_summary"
    assert report.review_status == "pending_harness_maintainer_review"
    assert report.findings[0].kind == "sensor_feedback"


def test_experience_summary_report_rejects_invalid_kind():
    with pytest.raises(ValidationError):
        ExperienceSummaryReport.model_validate(
            {
                "summary": "Invalid.",
                "findings": [
                    {
                        "id": "bad",
                        "kind": "not_allowed",
                        "title": "Bad",
                        "summary": "Bad.",
                        "evidence_sources": [".ai/experience/pending-improvements.md"],
                    }
                ],
            }
        )
