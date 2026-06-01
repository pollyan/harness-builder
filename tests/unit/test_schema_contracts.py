import pytest
from pydantic import ValidationError

from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceLog
from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.harness_map import HarnessMap
from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire
from harness_builder_agent.schemas.human_input_governance import HumanInputGovernanceLog
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.sensor_report import SensorReport
from harness_builder_agent.schemas.scan import EvidenceBundle, EvidenceBucketCoverage, EvidenceCoverage, EvidenceFile, ScanMetadata
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidateReport
from harness_builder_agent.schemas.weapon_candidate_governance import WeaponCandidateGovernanceLog
from harness_builder_agent.schemas.workflow_recommendation_history import WorkflowRecommendationHistory
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.schemas.workflow_policy_patch import WorkflowPolicyPatch


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


def test_weapon_library_candidate_report_records_maturity_impact_contract():
    report = WeaponLibraryCandidateReport.model_validate(
        {
            "schema_version": "1.0",
            "source": "llm_scan_proposal",
            "candidates": [
                {
                    "id": "llm-guide-001",
                    "candidate_type": "guide",
                    "status": "candidate",
                    "title": "Guide",
                    "rationale": "Needs review.",
                    "evidence": [".ai/project-inventory.json"],
                    "source": "llm_scan_proposal",
                    "human_confirmation_required": True,
                    "maturity_dimensions": ["guides", "risk_control"],
                    "maturity_impact_summary": "补齐 Guides 上下文、Risk Control 风险控制。",
                    "next_stage_contribution": "连接风险区域到 Guide 和 Workflow 升级。",
                }
            ],
        }
    )

    candidate = report.candidates[0]
    assert candidate.maturity_dimensions == ["guides", "risk_control"]
    assert candidate.maturity_impact_summary == "补齐 Guides 上下文、Risk Control 风险控制。"
    assert candidate.next_stage_contribution == "连接风险区域到 Guide 和 Workflow 升级。"
    assert candidate.review_boundary == "review_only_no_formal_asset_change"

    legacy = WeaponLibraryCandidateReport.model_validate(
        {
            "schema_version": "1.0",
            "source": "llm_scan_proposal",
            "candidates": [
                {
                    "id": "llm-guide-legacy-001",
                    "candidate_type": "guide",
                    "status": "candidate",
                    "title": "Legacy",
                    "rationale": "Old report without maturity fields.",
                    "evidence": [".ai/project-inventory.json"],
                    "source": "llm_scan_proposal",
                    "human_confirmation_required": True,
                }
            ],
        }
    )
    assert legacy.candidates[0].maturity_dimensions == []
    assert legacy.candidates[0].maturity_impact_summary == ""
    assert legacy.candidates[0].next_stage_contribution == ""
    assert legacy.candidates[0].review_boundary == "review_only_no_formal_asset_change"


def test_weapon_candidate_governance_log_schema():
    log = WeaponCandidateGovernanceLog.model_validate(
        {
            "schema_version": "1.0",
            "decisions": [
                {
                    "candidate_id": "llm-guide-risk-001",
                    "candidate_type": "guide",
                    "source_report": ".ai/experience/weapon-library-candidates.yaml",
                    "decision": "accepted",
                    "rationale": "Reviewed by maintainer.",
                    "reviewer": "alice",
                    "decided_at": "2026-06-01T12:00:00Z",
                    "previous_status": "candidate",
                    "new_status": "confirmed",
                    "maturity_dimensions": ["guides", "risk_control"],
                    "review_boundary": "review_only_no_formal_asset_change",
                }
            ],
        }
    )

    decision = log.decisions[0]
    assert decision.candidate_id == "llm-guide-risk-001"
    assert decision.decision == "accepted"
    assert decision.new_status == "confirmed"
    assert decision.maturity_dimensions == ["guides", "risk_control"]


def test_context_inputs_reject_negative_size():
    with pytest.raises(ValidationError):
        ContextInputs.model_validate(
            {
                "schema_version": "1.0",
                "contexts": [
                    {"path": "/repo/team.md", "size_bytes": -1, "summary": "team", "truncated": False}
                ],
            }
        )


def test_questionnaire_rejects_unknown_interaction_type():
    with pytest.raises(ValidationError):
        Questionnaire.model_validate(
            {
                "schema_version": "1.0",
                "questions": [
                    {
                        "interaction_type": "unknown",
                        "interaction_id": "confirm:unknown",
                        "question": "Confirm?",
                        "options": ["yes"],
                        "confidence": "medium",
                        "reason": "Needs confirmation.",
                    }
                ],
            }
        )


def test_questionnaire_accepts_evidence_expansion_confirmation():
    payload = {
        "schema_version": "1.0",
        "questions": [
            {
                "interaction_type": "evidence_expansion_confirmation",
                "interaction_id": "confirm:evidence-expansion",
                "question": "LLM 深度补充读取的路径是否代表真实关键模块或风险边界？",
                "options": ["确认这些路径可作为关键 evidence", "人工补充或修正关键路径"],
                "confidence": "low",
                "reason": "规划原因：Auth code was not sampled.",
            }
        ],
    }

    questionnaire = Questionnaire.model_validate(payload)

    assert questionnaire.questions[0].interaction_type == "evidence_expansion_confirmation"


def test_questionnaire_defaults_followup_response_status_for_old_payloads():
    questionnaire = Questionnaire.model_validate(
        {
            "schema_version": "1.0",
            "questions": [
                {
                    "interaction_type": "scan_followup_confirmation",
                    "interaction_id": "confirm:scan-followup:test-evidence",
                    "question": "真实测试入口是什么？",
                    "options": ["补充或修正相关信息"],
                    "confidence": "low",
                    "reason": "缺少测试 evidence。",
                }
            ],
        }
    )

    assert questionnaire.questions[0].response_status == "unaddressed"
    assert questionnaire.questions[0].response_sources == []


def test_questionnaire_accepts_partially_addressed_followup_response_status():
    questionnaire = Questionnaire.model_validate(
        {
            "schema_version": "1.0",
            "questions": [
                {
                    "interaction_type": "scan_followup_confirmation",
                    "interaction_id": "confirm:scan-followup:test-evidence",
                    "question": "真实测试入口是什么？",
                    "options": ["补充或修正相关信息"],
                    "confidence": "low",
                    "reason": "缺少测试 evidence。",
                    "response_status": "partially_addressed_by_current_scan_supplement",
                    "response_sources": ["command=unit_test:mvn test"],
                }
            ],
        }
    )

    assert questionnaire.questions[0].response_status == "partially_addressed_by_current_scan_supplement"
    assert questionnaire.questions[0].response_sources == ["command=unit_test:mvn test"]


def test_questionnaire_accepts_resolved_followup_response_status():
    questionnaire = Questionnaire.model_validate(
        {
            "schema_version": "1.0",
            "questions": [
                {
                    "interaction_type": "scan_followup_confirmation",
                    "interaction_id": "confirm:scan-followup:test-evidence",
                    "question": "真实测试入口是什么？",
                    "options": ["补充或修正相关信息"],
                    "confidence": "low",
                    "reason": "缺少测试 evidence。",
                    "response_status": "reviewed_resolved_by_harness_maintainer",
                    "response_sources": ["command=unit_test:mvn test"],
                }
            ],
        }
    )

    assert questionnaire.questions[0].response_status == "reviewed_resolved_by_harness_maintainer"


def test_human_input_governance_log_records_review_decisions():
    log = HumanInputGovernanceLog.model_validate(
        {
            "decisions": [
                {
                    "interaction_id": "confirm:scan-followup:test-evidence",
                    "interaction_type": "scan_followup_confirmation",
                    "decision": "resolved",
                    "previous_response_status": "partially_addressed_by_current_scan_supplement",
                    "new_response_status": "reviewed_resolved_by_harness_maintainer",
                    "rationale": "Maintainer verified mvn test is the real gate.",
                    "reviewer": "maintainer",
                    "decided_at": "2026-06-01T00:00:00Z",
                    "response_sources": ["command=unit_test:mvn test"],
                }
            ]
        }
    )

    assert log.schema_version == "1.0"
    assert log.decisions[0].decision == "resolved"


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


def test_scan_metadata_accepts_evidence_expansion_audit():
    metadata = ScanMetadata(
        prompt_version="scan-v2",
        evidence_file_count=120,
        evidence_expansion={
            "planner_prompt_version": "llm-evidence-plan-v1",
            "requested_paths": ["src/auth/AuthService.py"],
            "risk_focus": ["auth flow"],
            "rationale": "Auth code was not in source samples.",
            "confidence": "low",
            "read_paths": ["src/auth/AuthService.py"],
            "read_file_count": 1,
        },
    )

    assert metadata.evidence_expansion is not None
    assert metadata.evidence_expansion.requested_paths == ["src/auth/AuthService.py"]
    assert metadata.evidence_expansion.read_file_count == 1


def test_scan_metadata_accepts_followup_questions():
    metadata = ScanMetadata(
        prompt_version="scan-v2",
        evidence_file_count=42,
        followup_questions=[
            {
                "interaction_id": "confirm:scan-followup:coverage-source-java",
                "trigger": "coverage_gap",
                "question": "哪些 Java 目录、入口文件或高风险路径需要补充扫描？",
                "reason": "source:.java 抽样不足，可能影响模块和风险判断。",
                "evidence": ["source:.java"],
                "confidence": "low",
                "affects": ["maturity", "guides", "sensors"],
            }
        ],
    )

    assert metadata.followup_questions[0].trigger == "coverage_gap"
    assert metadata.followup_questions[0].interaction_id == "confirm:scan-followup:coverage-source-java"


def test_scan_metadata_accepts_self_check_report():
    metadata = ScanMetadata(
        prompt_version="scan-v2",
        evidence_file_count=42,
        self_check={
            "prompt_version": "llm-scan-self-check-v1",
            "review_status": "pending_harness_maintainer_review",
            "overall_risk": "medium",
            "summary": "coverage gap still needs maintainer review.",
            "resolutions": [
                {
                    "interaction_id": "confirm:scan-followup:coverage-source-java",
                    "trigger": "coverage_gap",
                    "status": "needs_targeted_scan",
                    "rationale": "Only one source sample is present.",
                    "evidence_sources": ["source:.java", "src/App.java"],
                    "suggested_next_action": "Ask maintainer for core module paths.",
                    "confidence": "medium",
                }
            ],
        },
    )

    assert metadata.self_check is not None
    assert metadata.self_check.review_status == "pending_harness_maintainer_review"
    assert metadata.self_check.resolutions[0].status == "needs_targeted_scan"
    assert metadata.self_check.resolutions[0].evidence_sources == ["source:.java", "src/App.java"]


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


def test_benchmark_report_preserves_failed_check_details():
    report = BenchmarkReport.model_validate(
        {
            "repo_name": "demo",
            "profile": "java-spring",
            "status": "failed",
            "quality_status": "failed",
            "checks": [
                {
                    "id": "content:hard-gate-command-evidence",
                    "passed": False,
                    "errors": ["hard_gate_without_source"],
                    "missing": ["source_path"],
                    "weak_commands": [
                        {
                            "id": "unit_test",
                            "source": "missing-pom.xml",
                            "confidence": "low",
                            "reason": "source_path_missing",
                        }
                    ],
                }
            ],
            "quality_scores": {},
        }
    )

    check = report.checks[0]

    assert check.errors == ["hard_gate_without_source"]
    assert check.missing == ["source_path"]
    assert check.weak_commands[0].id == "unit_test"
    assert check.weak_commands[0].reason == "source_path_missing"


def test_candidate_governance_log_records_review_decisions():
    log = CandidateGovernanceLog.model_validate(
        {
            "schema_version": "1.0",
            "decisions": [
                {
                    "candidate_id": "guide-project-context-scope",
                    "candidate_kind": "guide",
                    "source_report": ".ai/review/asset-candidates.yaml",
                    "source_candidate_id": "maturity-next-step-guides",
                    "suggested_path": ".ai/guides/project-context.md",
                    "decision": "applied",
                    "rationale": "Maintainer accepted the guide scope addition.",
                    "reviewer": "harness-maintainer",
                    "decided_at": "2026-05-31T00:00:00Z",
                    "applied_paths": [".ai/guides/project-context.md"],
                    "acceptance_checks": ["Run benchmark."],
                    "evidence_sources": [".ai/maturity-evidence.yaml"],
                }
            ],
        }
    )

    assert log.decisions[0].decision == "applied"
    assert log.decisions[0].applied_paths == [".ai/guides/project-context.md"]


def test_candidate_governance_log_rejects_unknown_decision():
    with pytest.raises(ValidationError):
        CandidateGovernanceLog.model_validate(
            {
                "schema_version": "1.0",
                "decisions": [
                    {
                        "candidate_id": "guide-project-context-scope",
                        "candidate_kind": "guide",
                        "source_report": ".ai/review/asset-candidates.yaml",
                        "suggested_path": ".ai/guides/project-context.md",
                        "decision": "auto_merged",
                        "rationale": "Invalid state.",
                        "reviewer": "harness-maintainer",
                        "decided_at": "2026-05-31T00:00:00Z",
                    }
                ],
            }
        )


def test_workflow_policy_patch_accepts_upsert_routing_rule():
    patch = WorkflowPolicyPatch.model_validate(
        {
            "schema_version": "1.0",
            "operation": "upsert_routing_rule",
            "target": "workflow_routing.rules",
            "rule": {
                "id": "standard-escalation",
                "selected_workflow": "standard",
                "rationale": "Escalate domain policy changes.",
                "task_type_hints": ["policy"],
                "triggers": [
                    "high_risk_module",
                    "cross_module_design",
                    "security_or_permission",
                    "insufficient_sensor_coverage",
                    "domain_policy_change",
                ],
                "required_guides": [".ai/guides/project-context.md"],
                "required_sensors": [".ai/sensors/verification.md"],
                "human_confirmation_required": True,
            },
        }
    )

    assert patch.operation == "upsert_routing_rule"
    assert patch.rule.id == "standard-escalation"


def test_workflow_policy_patch_rejects_unknown_operation():
    with pytest.raises(ValidationError):
        WorkflowPolicyPatch.model_validate(
            {
                "schema_version": "1.0",
                "operation": "replace_config",
                "target": "workflow_routing.rules",
                "rule": {
                    "id": "standard-escalation",
                    "selected_workflow": "standard",
                    "rationale": "Invalid operation.",
                },
            }
        )


def test_asset_candidate_requires_structured_patch_for_workflow_policy():
    with pytest.raises(ValidationError):
        AssetCandidateReport.model_validate(
            {
                "schema_version": "1.0",
                "source": "llm_maturity_review",
                "candidates": [
                    {
                        "id": "workflow-routing-policy-review",
                        "kind": "workflow_policy",
                        "source_candidate_id": "candidate-1",
                        "source_review_decision": "support",
                        "suggested_path": ".ai/harness-config.yaml",
                        "title": "Review workflow routing policy",
                        "rationale": "Needs structured patch.",
                        "draft_content": "free text is not enough",
                        "evidence_sources": [".ai/maturity-evidence.yaml"],
                        "acceptance_checks": ["Run benchmark."],
                        "risk_level": "medium",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ],
            }
        )


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


def test_self_improve_package_manifest_schema():
    manifest = SelfImprovePackageManifest.model_validate(
        {
            "package_id": "self-improve-001",
            "review_status": "pending_harness_maintainer_review",
            "generated_artifacts": [
                {"path": ".ai/improvement-candidates.yaml", "kind": "improvement_candidates"},
                {"path": ".ai/review/maturity-review.yaml", "kind": "maturity_review"},
                {"path": ".ai/review/asset-candidates.yaml", "kind": "asset_candidates"},
            ],
            "candidate_counts": {
                "improvement_candidates": 3,
                "maturity_reviews": 3,
                "asset_candidates": 2,
                "guide_candidates": 1,
                "sensor_candidates": 1,
                "workflow_policy_candidates": 0,
            },
            "maturity": {
                "overall_level": "L2",
                "target_next_level": "L3",
                "dimension_scores": {"guides": "L2", "sensors": "L2"},
            },
            "next_actions": ["Review asset candidates before applying formal Harness changes."],
            "warnings": ["Runtime task-runs are absent."],
        }
    )

    assert manifest.schema_version == "1.0"
    assert manifest.review_status == "pending_harness_maintainer_review"
    assert manifest.candidate_counts.asset_candidates == 2
    assert manifest.maturity.overall_level == "L2"


def test_workflow_recommendation_history_schema_tracks_latest_entry():
    history = WorkflowRecommendationHistory.model_validate(
        {
            "latest_recommendation_id": "task-2-20260531T120000Z",
            "recommendations": [
                {
                    "recommendation_id": "task-1-20260531T115900Z",
                    "task_id": "task-1",
                    "created_at": "2026-05-31T11:59:00Z",
                    "yaml_path": ".ai/review/workflow-routing-recommendations/task-1-20260531T115900Z.yaml",
                    "markdown_path": ".ai/review/workflow-routing-recommendations/task-1-20260531T115900Z.md",
                    "recommended_workflow": "bugfix",
                    "risk_level": "medium",
                    "confidence": "high",
                    "review_status": "pending_harness_maintainer_review",
                },
                {
                    "recommendation_id": "task-2-20260531T120000Z",
                    "task_id": "task-2",
                    "created_at": "2026-05-31T12:00:00Z",
                    "yaml_path": ".ai/review/workflow-routing-recommendations/task-2-20260531T120000Z.yaml",
                    "markdown_path": ".ai/review/workflow-routing-recommendations/task-2-20260531T120000Z.md",
                    "recommended_workflow": "standard",
                    "risk_level": "high",
                    "confidence": "medium",
                    "review_status": "pending_harness_maintainer_review",
                },
            ],
        }
    )

    assert history.schema_version == "1.0"
    assert history.latest_recommendation_id == "task-2-20260531T120000Z"
    assert len(history.recommendations) == 2


def test_workflow_recommendation_history_rejects_latest_id_not_in_entries():
    with pytest.raises(ValidationError):
        WorkflowRecommendationHistory.model_validate(
            {
                "latest_recommendation_id": "missing",
                "recommendations": [
                    {
                        "recommendation_id": "task-1-20260531T115900Z",
                        "task_id": "task-1",
                        "created_at": "2026-05-31T11:59:00Z",
                        "yaml_path": ".ai/review/workflow-routing-recommendations/task-1-20260531T115900Z.yaml",
                        "markdown_path": ".ai/review/workflow-routing-recommendations/task-1-20260531T115900Z.md",
                        "recommended_workflow": "bugfix",
                        "risk_level": "medium",
                        "confidence": "high",
                        "review_status": "pending_harness_maintainer_review",
                    }
                ],
            }
        )
