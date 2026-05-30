from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.scan import LLMScanProposal, ScanMetadata
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.scan_repo import scan_repository
from harness_builder_agent.tools.write_assets import write_initial_assets

REQUIRED_FILES = [
    "project-inventory.json",
    "command-catalog.yaml",
    "harness-config.yaml",
    "scan-metadata.yaml",
    "llm-scan-proposal.json",
    "weapon-library-selection.yaml",
    "context-inputs.yaml",
    "questionnaire.yaml",
    "human-input-needed.md",
    "scan-report.md",
    "maturity-report.md",
    "maturity-score.yaml",
    "maturity-evidence.yaml",
    "evolution-plan.md",
    "guides/project-context.md",
    "guides/coding-rules.md",
    "guides/architecture.md",
    "sensors/verification.md",
    "sensors/test-strategy.md",
    "skills/lightweight/SKILL.md",
    "skills/bugfix/SKILL.md",
    "skills/standard/SKILL.md",
    "improvement-candidates.yaml",
    "experience/experience-index.yaml",
    "review/llm-enhancement-candidates.md",
    "review/candidate-guides.md",
    "review/candidate-sensors.md",
    "experience/weapon-library-candidates.yaml",
]


def run_benchmark(repo: Path, profile: str | None = None, trace: GenerationTrace | None = None) -> dict[str, Any]:
    root = repo.resolve()
    if trace:
        trace.event("benchmark", "started", "Benchmark started.", {"profile": profile})
    inventory, commands = scan_repository(root)
    if trace:
        trace.event(
            "scan",
            "completed",
            "Repository scan completed for benchmark.",
            {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)},
        )
    write_initial_assets(root, inventory, commands, trace=trace)
    assess_maturity(root)
    generate_improvements(root)
    ai = root / ".ai"
    if trace:
        trace.artifact(ai / "benchmark-report.yaml", "benchmark_report")
        trace.event("benchmark", "completed", "Benchmark checks are ready to evaluate.", {"profile": profile or inventory.primary_stack})
        trace.finish("completed", {"profile": profile or inventory.primary_stack, "primary_stack": inventory.primary_stack})

    checks: list[dict[str, Any]] = []
    for rel in REQUIRED_FILES:
        checks.append({"id": f"exists:{rel}", "passed": (ai / rel).exists(), "path": f".ai/{rel}"})

    checks.extend(_schema_checks(ai))
    checks.extend(_generation_trace_checks(ai))
    checks.extend(_human_confirmation_checks(ai))
    checks.extend(_llm_enhancement_checks(ai))
    checks.extend(_content_checks(ai, inventory))
    if profile:
        checks.append({"id": "profile_matches_stack", "passed": profile == inventory.primary_stack, "expected": profile, "actual": inventory.primary_stack})

    hard_status = "passed" if all(check["passed"] for check in checks) else "failed"
    quality_scores = _quality_scores(ai, inventory)
    quality_summary = _quality_summary(quality_scores)
    report = {
        "schema_version": "1.0",
        "repo_name": root.name,
        "profile": profile or inventory.primary_stack,
        "status": hard_status,
        "checks": checks,
        "quality_status": _quality_status(hard_status, quality_summary),
        "quality_scores": quality_scores,
        "quality_summary": quality_summary,
    }
    report["checks"].append({"id": "schema:benchmark-report", "passed": True})
    report["status"] = "passed" if all(check["passed"] for check in report["checks"]) else "failed"
    report["quality_status"] = _quality_status(report["status"], quality_summary)
    BenchmarkReport.model_validate(report)
    (ai / "benchmark-report.yaml").write_text(yaml.safe_dump(report, sort_keys=False, allow_unicode=True), encoding="utf-8")
    if trace:
        trace.finish(
            "completed" if report["status"] == "passed" else "failed",
            {"profile": report["profile"], "status": report["status"], "check_count": len(report["checks"])},
        )
    return report


def _schema_checks(ai: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    try:
        ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))
        checks.append({"id": "schema:project-inventory", "passed": True})
    except Exception as exc:  # pragma: no cover - captured in benchmark report
        checks.append({"id": "schema:project-inventory", "passed": False, "error": str(exc)})

    try:
        CommandCatalog.model_validate(yaml.safe_load((ai / "command-catalog.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:command-catalog", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:command-catalog", "passed": False, "error": str(exc)})

    try:
        HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:harness-config", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:harness-config", "passed": False, "error": str(exc)})

    try:
        ScanMetadata.model_validate(yaml.safe_load((ai / "scan-metadata.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:scan-metadata", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:scan-metadata", "passed": False, "error": str(exc)})

    try:
        LLMScanProposal.model_validate_json((ai / "llm-scan-proposal.json").read_text(encoding="utf-8"))
        checks.append({"id": "schema:llm-scan-proposal", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:llm-scan-proposal", "passed": False, "error": str(exc)})

    try:
        WeaponLibrarySelection.model_validate(yaml.safe_load((ai / "weapon-library-selection.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:weapon-library-selection", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:weapon-library-selection", "passed": False, "error": str(exc)})

    try:
        MaturityReport.model_validate(yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:maturity-score", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:maturity-score", "passed": False, "error": str(exc)})

    try:
        MaturityEvidencePack.model_validate(yaml.safe_load((ai / "maturity-evidence.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:maturity-evidence", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:maturity-evidence", "passed": False, "error": str(exc)})

    try:
        ImprovementCandidateReport.model_validate(yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:improvement-candidates", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:improvement-candidates", "passed": False, "error": str(exc)})

    try:
        ExperienceIndex.model_validate(yaml.safe_load((ai / "experience" / "experience-index.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:experience-index", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:experience-index", "passed": False, "error": str(exc)})
    return checks


def _generation_trace_checks(ai: Path) -> list[dict[str, Any]]:
    runs = ai / "runs"
    if not runs.exists():
        return [
            {"id": "exists:runs-trace", "passed": False, "error": "missing .ai/runs"},
            {"id": "schema:generation-trace", "passed": False, "error": "missing trace.yaml"},
            {"id": "content:generation-trace", "passed": False, "error": "missing trace content"},
        ]

    run_dirs = sorted(path for path in runs.iterdir() if path.is_dir())
    if not run_dirs:
        return [
            {"id": "exists:runs-trace", "passed": False, "error": "no run directories"},
            {"id": "schema:generation-trace", "passed": False, "error": "missing trace.yaml"},
            {"id": "content:generation-trace", "passed": False, "error": "missing trace content"},
        ]

    latest = run_dirs[-1]
    checks: list[dict[str, Any]] = [{"id": "exists:runs-trace", "passed": True, "path": f".ai/runs/{latest.name}"}]
    try:
        trace = yaml.safe_load((latest / "trace.yaml").read_text(encoding="utf-8"))
        required = {"schema_version", "run_id", "command", "status", "stages", "summary"}
        checks.append({"id": "schema:generation-trace", "passed": required.issubset(set(trace)), "run_id": trace.get("run_id")})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:generation-trace", "passed": False, "error": str(exc)})
        trace = {}

    events_path = latest / "events.jsonl"
    artifacts_path = latest / "artifacts.yaml"
    try:
        events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        artifacts = yaml.safe_load(artifacts_path.read_text(encoding="utf-8"))
        passed = bool(trace.get("stages")) and bool(events) and bool(artifacts.get("artifacts"))
        checks.append(
            {
                "id": "content:generation-trace",
                "passed": passed,
                "stage_count": len(trace.get("stages", [])),
                "event_count": len(events),
                "artifact_count": len(artifacts.get("artifacts", [])),
            }
        )
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "content:generation-trace", "passed": False, "error": str(exc)})
    return checks


def _human_confirmation_checks(ai: Path) -> list[dict[str, Any]]:
    try:
        questionnaire = yaml.safe_load((ai / "questionnaire.yaml").read_text(encoding="utf-8"))
        questions = questionnaire.get("questions", [])
        schema_passed = questionnaire.get("schema_version") == "1.0" and bool(questions)
        checks = [{"id": "schema:questionnaire", "passed": schema_passed, "question_count": len(questions)}]
    except Exception as exc:  # pragma: no cover
        return [
            {"id": "schema:questionnaire", "passed": False, "error": str(exc)},
            {"id": "content:human-confirmation", "passed": False, "error": "questionnaire unavailable"},
        ]

    ids = {item.get("interaction_id") for item in questions}
    required_ids = {"confirm:team-context", "confirm:guide-candidates", "confirm:sensor-gates"}
    human_input = (ai / "human-input-needed.md").read_text(encoding="utf-8") if (ai / "human-input-needed.md").exists() else ""
    checks.append(
        {
            "id": "content:human-confirmation",
            "passed": required_ids.issubset(ids) and "# Human Input Needed" in human_input,
            "required_question_count": len(required_ids),
        }
    )
    return checks


def _llm_enhancement_checks(ai: Path) -> list[dict[str, Any]]:
    report_path = ai / "experience" / "weapon-library-candidates.yaml"
    try:
        report = yaml.safe_load(report_path.read_text(encoding="utf-8"))
        candidates = report.get("candidates", [])
        schema_passed = report.get("schema_version") == "1.0" and report.get("source") == "llm_scan_proposal" and bool(candidates)
        checks = [{"id": "schema:weapon-library-candidates", "passed": schema_passed, "candidate_count": len(candidates)}]
    except Exception as exc:  # pragma: no cover
        return [
            {"id": "schema:weapon-library-candidates", "passed": False, "error": str(exc)},
            {"id": "content:llm-enhancement-candidates", "passed": False, "error": "candidate report unavailable"},
        ]

    review_text = (
        (ai / "review" / "llm-enhancement-candidates.md").read_text(encoding="utf-8")
        if (ai / "review" / "llm-enhancement-candidates.md").exists()
        else ""
    )
    checks.append(
        {
            "id": "content:llm-enhancement-candidates",
            "passed": all(item.get("status") == "candidate" and item.get("human_confirmation_required") is True for item in candidates)
            and "candidate" in review_text.lower(),
        }
    )
    return checks


def _content_checks(ai: Path, inventory: ProjectInventory) -> list[dict[str, Any]]:
    return [
        _workflow_skills_check(ai),
        _workflow_skill_config_reference_check(ai),
        _workflow_routing_policy_check(ai),
        _maturity_routing_evidence_check(ai),
        _workflow_recommendation_review_check(ai),
        _guide_quality_check(ai),
        _stack_specific_guide_check(ai, inventory),
        _sensor_quality_check(ai),
        _weapon_library_selection_check(ai, inventory),
        _hard_gate_command_evidence_check(ai),
    ]


def _workflow_skills_check(ai: Path) -> dict[str, Any]:
    lightweight = ai / "skills" / "lightweight" / "SKILL.md"
    bugfix = ai / "skills" / "bugfix" / "SKILL.md"
    standard = ai / "skills" / "standard" / "SKILL.md"
    lightweight_text = lightweight.read_text(encoding="utf-8") if lightweight.exists() else ""
    bugfix_text = bugfix.read_text(encoding="utf-8") if bugfix.exists() else ""
    standard_text = standard.read_text(encoding="utf-8") if standard.exists() else ""
    passed = all(
        (
            "轻量级开发工作流" in lightweight_text,
            "缺陷修复工作流" in bugfix_text,
            "标准开发工作流" in standard_text,
            "Requirement Alignment" in standard_text,
        )
    )
    return {"id": "content:workflow-skills", "passed": passed}


def _workflow_skill_config_reference_check(ai: Path) -> dict[str, Any]:
    config_path = ai / "harness-config.yaml"
    if not config_path.exists():
        return {"id": "content:workflow-skill-config-reference", "passed": False, "error": "missing harness-config.yaml"}
    try:
        config = HarnessConfig.model_validate(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover
        return {"id": "content:workflow-skill-config-reference", "passed": False, "error": str(exc)}
    missing = [
        workflow.skill_path
        for workflow in config.workflows.values()
        if not workflow.skill_path or not (ai.parent / workflow.skill_path).exists()
    ]
    return {
        "id": "content:workflow-skill-config-reference",
        "passed": not missing and bool(config.workflows),
        "workflow_count": len(config.workflows),
        "missing": missing,
    }


def _workflow_routing_policy_check(ai: Path) -> dict[str, Any]:
    config_path = ai / "harness-config.yaml"
    if not config_path.exists():
        return {"id": "content:workflow-routing-policy", "passed": False, "errors": ["missing_harness_config"]}
    try:
        config = HarnessConfig.model_validate(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover
        return {"id": "content:workflow-routing-policy", "passed": False, "errors": [str(exc)]}

    errors: list[str] = []
    available_workflows = set(config.workflows)
    rules = config.workflow_routing.rules
    if config.workflow_routing.default_workflow != "lightweight":
        errors.append("default_workflow_not_lightweight")
    if config.workflow_routing.default_workflow not in available_workflows:
        errors.append("default_workflow_unknown")

    rule_ids = {rule.id for rule in rules}
    if not {"bugfix-intent", "low-risk-lightweight", "standard-escalation"}.issubset(rule_ids):
        errors.append("missing_required_routing_rules")

    unknown_workflows = sorted({rule.selected_workflow for rule in rules if rule.selected_workflow not in available_workflows})
    if unknown_workflows:
        errors.append("unknown_selected_workflow")

    standard_rules = [rule for rule in rules if rule.id == "standard-escalation" and rule.selected_workflow == "standard"]
    if not standard_rules:
        errors.append("missing_standard_escalation")
    else:
        triggers = set(standard_rules[0].triggers)
        required_triggers = {"high_risk_module", "cross_module_design", "security_or_permission", "insufficient_sensor_coverage"}
        if not required_triggers.issubset(triggers):
            errors.append("incomplete_standard_escalation_triggers")
        if not standard_rules[0].human_confirmation_required:
            errors.append("standard_escalation_without_human_confirmation")

    return {
        "id": "content:workflow-routing-policy",
        "passed": not errors,
        "rule_count": len(rules),
        "errors": errors,
    }


def _maturity_routing_evidence_check(ai: Path) -> dict[str, Any]:
    config_path = ai / "harness-config.yaml"
    evidence_path = ai / "maturity-evidence.yaml"
    if not config_path.exists() or not evidence_path.exists():
        return {"id": "content:maturity-routing-evidence", "passed": False, "errors": ["missing_config_or_evidence"]}
    try:
        config = HarnessConfig.model_validate(yaml.safe_load(config_path.read_text(encoding="utf-8")))
        evidence = MaturityEvidencePack.model_validate(yaml.safe_load(evidence_path.read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover
        return {"id": "content:maturity-routing-evidence", "passed": False, "errors": [str(exc)]}

    errors: list[str] = []
    config_rule_ids = {rule.id for rule in config.workflow_routing.rules}
    evidence_rules = evidence.harness_assets.workflow_routing_rules
    evidence_rule_ids = {rule.id for rule in evidence_rules}
    if not evidence_rules:
        errors.append("missing_routing_evidence_detail")
    if config_rule_ids != evidence_rule_ids:
        errors.append("routing_evidence_out_of_sync")

    standard_rules = [rule for rule in evidence_rules if rule.id == "standard-escalation" and rule.selected_workflow == "standard"]
    if not standard_rules:
        errors.append("missing_standard_escalation_evidence")
    elif "security_or_permission" not in standard_rules[0].triggers:
        errors.append("incomplete_standard_escalation_evidence")

    return {
        "id": "content:maturity-routing-evidence",
        "passed": not errors,
        "rule_count": len(evidence_rules),
        "errors": errors,
    }


def _workflow_recommendation_review_check(ai: Path) -> dict[str, Any]:
    yaml_path = ai / "review" / "workflow-routing-recommendation.yaml"
    markdown_path = ai / "review" / "workflow-routing-recommendation.md"
    if not yaml_path.exists() and not markdown_path.exists():
        return {"id": "content:workflow-recommendation-review", "passed": True, "present": False}

    errors: list[str] = []
    if not yaml_path.exists() or not markdown_path.exists():
        errors.append("incomplete_recommendation_artifact_pair")

    try:
        config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
        report = WorkflowRecommendationReport.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover - captured in benchmark report
        return {"id": "content:workflow-recommendation-review", "passed": False, "present": True, "errors": [str(exc)]}

    available_workflows = set(config.workflows)
    available_rule_ids = {rule.id for rule in config.workflow_routing.rules}
    if report.recommended_workflow not in available_workflows:
        errors.append("unknown_recommended_workflow")
    if any(rule_id not in available_rule_ids for rule_id in report.matched_rule_ids):
        errors.append("unknown_matched_rule_ids")
    if report.review_status != "pending_harness_maintainer_review":
        errors.append("recommendation_not_review_only")
    if any(not source.startswith(".ai/") for source in report.evidence_sources):
        errors.append("evidence_source_outside_ai")

    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    required_sections = [
        "# Workflow Routing Recommendation",
        "## Task",
        "## Recommended Workflow",
        "## Matched Routing Rules",
        "## Required Harness Assets",
        "## Review Boundary",
    ]
    if any(section not in markdown for section in required_sections):
        errors.append("missing_markdown_sections")

    return {
        "id": "content:workflow-recommendation-review",
        "passed": not errors,
        "present": True,
        "recommended_workflow": report.recommended_workflow,
        "matched_rule_count": len(report.matched_rule_ids),
        "errors": errors,
    }


def _guide_quality_check(ai: Path) -> dict[str, Any]:
    required_sections = ["## 当前项目事实", "## 来源证据", "## 候选规则", "## Harness Builder 推荐补齐项", "## 人工确认点"]
    guide = ai / "guides" / "project-context.md"
    text = guide.read_text(encoding="utf-8") if guide.exists() else ""
    passed = all(section in text for section in required_sections)
    return {"id": "content:guides-quality", "passed": passed}


def _sensor_quality_check(ai: Path) -> dict[str, Any]:
    required_sections = ["## 已发现的验证命令", "## 缺失验证能力", "## 推荐验证活动", "## 失败处理策略"]
    sensor = ai / "sensors" / "verification.md"
    text = sensor.read_text(encoding="utf-8") if sensor.exists() else ""
    passed = all(section in text for section in required_sections) and "hard" in text
    return {"id": "content:sensors-quality", "passed": passed}


def _stack_specific_guide_check(ai: Path, inventory: ProjectInventory) -> dict[str, Any]:
    guide = ai / "guides" / "project-context.md"
    text = guide.read_text(encoding="utf-8") if guide.exists() else ""
    if inventory.primary_stack == "java-spring":
        passed = "java-spring.guide.maven-boundary" in text and "java-spring.guide.auth-sql-config-risk" in text
    elif inventory.primary_stack == "dotnet-aspnet":
        passed = "dotnet-aspnet.guide.solution-boundary" in text and "dotnet-aspnet.guide.publicapi-config-risk" in text
    else:
        passed = "人工确认" in text
    return {"id": "content:stack-specific-guides", "passed": passed, "stack": inventory.primary_stack}


def _weapon_library_selection_check(ai: Path, inventory: ProjectInventory) -> dict[str, Any]:
    selection_path = ai / "weapon-library-selection.yaml"
    guide_path = ai / "guides" / "project-context.md"
    sensor_path = ai / "sensors" / "verification.md"
    if not selection_path.exists():
        return {"id": "content:weapon-library-selection", "passed": False, "error": "missing weapon-library-selection.yaml"}

    try:
        selection = WeaponLibrarySelection.model_validate(yaml.safe_load(selection_path.read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover
        return {"id": "content:weapon-library-selection", "passed": False, "error": str(exc)}

    guide_text = guide_path.read_text(encoding="utf-8") if guide_path.exists() else ""
    sensor_text = sensor_path.read_text(encoding="utf-8") if sensor_path.exists() else ""
    expected_stacks = {"common", inventory.primary_stack}
    passed = (
        selection.source == "built_in_weapon_library"
        and expected_stacks.issubset(set(selection.selected_stacks))
        and all(weapon_id in guide_text for weapon_id in selection.guide_weapon_ids)
        and all(weapon_id in sensor_text for weapon_id in selection.sensor_weapon_ids)
    )
    return {
        "id": "content:weapon-library-selection",
        "passed": passed,
        "selected_stacks": selection.selected_stacks,
        "guide_weapon_count": len(selection.guide_weapon_ids),
        "sensor_weapon_count": len(selection.sensor_weapon_ids),
    }


def _hard_gate_command_evidence_check(ai: Path) -> dict[str, Any]:
    try:
        catalog = CommandCatalog.model_validate(yaml.safe_load((ai / "command-catalog.yaml").read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover
        return {"id": "content:hard-gate-command-evidence", "passed": False, "error": str(exc)}
    hard_commands = [command for command in catalog.commands if command.gate == "hard"]
    weak = [
        {"id": command.id, "source": command.source, "confidence": command.confidence}
        for command in hard_commands
        if not command.source or command.confidence == "low"
    ]
    return {
        "id": "content:hard-gate-command-evidence",
        "passed": bool(hard_commands) and not weak,
        "hard_gate_count": len(hard_commands),
        "weak_commands": weak,
    }


def _quality_scores(ai: Path, inventory: ProjectInventory) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "scan_quality": {
            "evidence_coverage": _score_evidence_coverage(ai),
            "stack_confidence": _score_stack_confidence(ai),
            "command_reliability": _score_command_reliability(ai),
        },
        "guide_quality": {
            "specificity": _score_guide_specificity(ai, inventory),
            "evidence_reference": _score_guide_evidence_reference(ai),
            "stack_specificity": _score_guide_stack_specificity(ai, inventory),
        },
        "sensor_quality": {
            "executable_gate": _score_executable_gate(ai),
            "failure_policy": _score_failure_policy(ai),
            "missing_capability_clarity": _score_missing_capability_clarity(ai),
        },
        "workflow_quality": {
            "skill_reference_integrity": _score_skill_reference_integrity(ai),
        },
    }


def _score_item(score: int, reasons: list[str] | None = None, recommendations: list[str] | None = None) -> dict[str, Any]:
    return {
        "score": score,
        "max_score": 5,
        "passed": score >= 4,
        "reasons": reasons or [],
        "recommendations": recommendations or [],
    }


def _quality_summary(scores: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    flat = [(f"{category}.{name}", item) for category, items in scores.items() for name, item in items.items()]
    total_possible = len(flat) * 5
    total = sum(item["score"] for _name, item in flat)
    total_score = int(round((total / total_possible) * 100)) if total_possible else 0
    minimum_score = min((item["score"] for _name, item in flat), default=0)
    degraded_items = [name for name, item in flat if 0 < item["score"] < 4]
    failed_items = [name for name, item in flat if item["score"] == 0]
    return {
        "total_score": total_score,
        "minimum_score": minimum_score,
        "degraded_items": degraded_items,
        "failed_items": failed_items,
    }


def _quality_status(hard_status: str, summary: dict[str, Any]) -> str:
    if hard_status == "failed" or summary["failed_items"]:
        return "failed"
    if summary["degraded_items"]:
        return "degraded"
    return "passed"


def _score_evidence_coverage(ai: Path) -> dict[str, Any]:
    try:
        metadata = yaml.safe_load((ai / "scan-metadata.yaml").read_text(encoding="utf-8"))
    except Exception as exc:
        return _score_item(0, [f"scan-metadata.yaml 不可读：{exc}"], ["修复 scan metadata schema 或重新运行 init。"])
    coverage = metadata.get("coverage")
    evidence_count = metadata.get("evidence_file_count", 0)
    if coverage and coverage.get("selected_evidence_count", 0) > 0:
        warnings = coverage.get("warnings", [])
        if warnings:
            return _score_item(4, ["存在 evidence coverage warning。"], ["检查 scan-metadata.yaml 中的 coverage warnings。"])
        return _score_item(5)
    if evidence_count > 0:
        return _score_item(3, ["缺少 coverage 详情，但存在 evidence 文件计数。"], ["重新运行支持 coverage 的 init。"])
    return _score_item(1, ["未发现 evidence 文件计数。"], ["检查 evidence collector 是否正常运行。"])


def _score_stack_confidence(ai: Path) -> dict[str, Any]:
    try:
        proposal = json.loads((ai / "llm-scan-proposal.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return _score_item(0, [f"llm-scan-proposal.json 不可读：{exc}"], ["重新运行 LLM scan。"])
    confidence = proposal.get("confidence")
    primary_stack = proposal.get("primary_stack")
    if confidence == "high" and primary_stack != "unknown":
        return _score_item(5)
    if confidence == "medium" and primary_stack != "unknown":
        return _score_item(3, ["LLM scan confidence 为 medium。"], ["人工确认 stack 判断。"])
    return _score_item(1, ["LLM scan confidence 低或 primary_stack unknown。"], ["补充 context 或 evidence 后重新 init。"])


def _score_command_reliability(ai: Path) -> dict[str, Any]:
    try:
        catalog = yaml.safe_load((ai / "command-catalog.yaml").read_text(encoding="utf-8"))
    except Exception as exc:
        return _score_item(0, [f"command-catalog.yaml 不可读：{exc}"], ["修复 command catalog。"])
    hard_commands = [command for command in catalog.get("commands", []) if command.get("gate") == "hard"]
    if not hard_commands:
        return _score_item(1, ["没有 hard gate command。"], ["确认至少一个可执行验证命令。"])
    if any(not command.get("source") or command.get("confidence") == "low" for command in hard_commands):
        return _score_item(2, ["存在 source 缺失或 low confidence 的 hard command。"], ["将不可靠命令降级为 advisory 或补充证据。"])
    if any(command.get("confidence") == "medium" for command in hard_commands):
        return _score_item(4, ["部分 hard command confidence 为 medium。"], ["人工确认这些命令在本地和 CI 稳定。"])
    return _score_item(5)


def _score_guide_specificity(ai: Path, inventory: ProjectInventory) -> dict[str, Any]:
    text = _read_text(ai / "guides" / "project-context.md")
    if text is None:
        return _score_item(0, ["project-context guide 不可读。"], ["重新生成 guides。"])
    has_stack = inventory.primary_stack in text
    has_module = any(str(module.get("path")) in text for module in inventory.modules)
    has_weapon = ".guide." in text
    has_context = "## 团队上下文" in text
    if has_stack and has_module and has_weapon and has_context:
        return _score_item(5)
    if has_stack and has_module and has_weapon:
        return _score_item(4, ["缺少团队上下文章节。"], ["补充团队 context。"])
    if all(section in text for section in ["## 当前项目事实", "## 候选规则", "## 人工确认点"]):
        return _score_item(2, ["guide 有必需章节但缺少具体 stack/module/weapon 内容。"], ["增强 guide 生成内容。"])
    return _score_item(0, ["guide 缺少关键章节。"], ["重新生成 guides。"])


def _score_guide_evidence_reference(ai: Path) -> dict[str, Any]:
    text = _read_text(ai / "guides" / "project-context.md")
    if text is None:
        return _score_item(0, ["project-context guide 不可读。"], ["重新生成 guides。"])
    if "## 来源证据" not in text:
        return _score_item(0, ["缺少来源证据章节。"], ["在 guide 中补充来源证据。"])
    evidence_section = text.split("## 来源证据", 1)[1]
    has_path = "`" in evidence_section and "/" in evidence_section or ".xml" in evidence_section or ".csproj" in evidence_section
    if has_path:
        return _score_item(5)
    return _score_item(2, ["来源证据章节存在但缺少 evidence path。"], ["在 guide 中补充 evidence path。"])


def _score_guide_stack_specificity(ai: Path, inventory: ProjectInventory) -> dict[str, Any]:
    text = _read_text(ai / "guides" / "project-context.md")
    if text is None:
        return _score_item(0, ["project-context guide 不可读。"], ["重新生成 guides。"])
    if inventory.primary_stack == "unknown":
        return _score_item(1, ["primary_stack unknown。"], ["人工确认技术栈。"])
    if f"{inventory.primary_stack}.guide." in text:
        return _score_item(5)
    if "common.guide." in text:
        return _score_item(3, ["只命中 common guide weapon。"], ["补充 stack-specific guide。"])
    return _score_item(0, ["guide 中没有 weapon id。"], ["检查 weapon library selection。"])


def _score_executable_gate(ai: Path) -> dict[str, Any]:
    check = _hard_gate_command_evidence_check(ai)
    if check["passed"]:
        return _score_item(5)
    if check.get("hard_gate_count", 0) > 0:
        return _score_item(2, ["存在 hard gate command，但证据不足或置信度过低。"], ["补充 source/evidence 或降级为 advisory。"])
    return _score_item(1, ["没有 hard gate command。"], ["确认至少一个可执行验证命令。"])


def _score_failure_policy(ai: Path) -> dict[str, Any]:
    text = _read_text(ai / "sensors" / "verification.md")
    if text is None:
        return _score_item(0, ["verification sensor Markdown 不可读。"], ["重新生成 sensors。"])
    if "## 失败处理策略" not in text:
        return _score_item(0, ["缺少失败处理策略。"], ["补充失败处理策略。"])
    return _score_item(5)


def _score_missing_capability_clarity(ai: Path) -> dict[str, Any]:
    text = _read_text(ai / "sensors" / "verification.md")
    if text is None:
        return _score_item(0, ["verification sensor Markdown 不可读。"], ["重新生成 sensors。"])
    has_missing = "## 缺失验证能力" in text
    has_recommended = "## 推荐验证活动" in text
    if has_missing and has_recommended:
        return _score_item(5)
    if has_missing or has_recommended:
        return _score_item(2, ["缺失验证能力或推荐验证活动章节不完整。"], ["补齐 sensor Markdown 章节。"])
    return _score_item(0, ["缺少缺失验证能力和推荐验证活动章节。"], ["补齐 sensor Markdown 章节。"])


def _score_skill_reference_integrity(ai: Path) -> dict[str, Any]:
    check = _workflow_skill_config_reference_check(ai)
    if check["passed"]:
        return _score_item(5)
    return _score_item(0, [check.get("error", "workflow skill 引用无效。")], ["修复 harness-config workflow skill path。"])


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None
