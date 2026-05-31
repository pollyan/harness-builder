from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.asset_candidate import AssetCandidateReport
from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.candidate_governance import CandidateGovernanceLog
from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.experience_index import ExperienceIndex
from harness_builder_agent.schemas.experience_summary import ExperienceSummaryReport
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.human_confirmation import ContextInputs, Questionnaire
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_evidence import MaturityEvidencePack
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.maturity_review import MaturityReviewReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.scan import LLMScanProposal, ScanMetadata
from harness_builder_agent.schemas.self_improve_package import SelfImprovePackageManifest
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.schemas.weapon_library_candidate import WeaponLibraryCandidateReport
from harness_builder_agent.schemas.workflow_recommendation import WorkflowRecommendationReport
from harness_builder_agent.schemas.workflow_recommendation_history import WorkflowRecommendationHistory
from harness_builder_agent.tools.ai_paths import is_safe_ai_relative_path
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.evidence_sources import (
    CORE_EVIDENCE_SOURCES,
    EXPERIENCE_SUMMARY_SOURCE_INPUTS,
    maturity_evidence_source_allowlist,
    unknown_evidence_sources,
)
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.runtime_task_runs import RuntimeTaskRunError, summarize_runtime_task_runs
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
    "init-summary.md",
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
    ai = root / ".ai"
    if (ai / "project-inventory.json").exists() and (ai / "command-catalog.yaml").exists():
        inventory = ProjectInventory.model_validate_json((ai / "project-inventory.json").read_text(encoding="utf-8"))
        commands = CommandCatalog.model_validate(yaml.safe_load((ai / "command-catalog.yaml").read_text(encoding="utf-8")))
        if trace:
            trace.event(
                "benchmark",
                "existing-harness",
                "Benchmark is validating existing Harness assets without rewriting them.",
                {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)},
            )
    else:
        inventory, commands = scan_repository(root)
        if trace:
            trace.event(
                "scan",
                "completed",
                "Repository scan completed for benchmark.",
                {"primary_stack": inventory.primary_stack, "command_count": len(commands.commands)},
            )
        write_initial_assets(root, inventory, commands, trace=trace)
    runtime_precheck = _runtime_task_run_artifacts_check(ai)
    runtime_invalid = runtime_precheck["present"] and not runtime_precheck["passed"]
    if not runtime_invalid:
        assess_maturity(root)
        generate_improvements(root)
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
    checks: list[dict[str, Any]] = []
    try:
        context_inputs = ContextInputs.model_validate(yaml.safe_load((ai / "context-inputs.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:context-inputs", "passed": True, "context_count": len(context_inputs.contexts)})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:context-inputs", "passed": False, "error": str(exc)})

    try:
        questionnaire = Questionnaire.model_validate(yaml.safe_load((ai / "questionnaire.yaml").read_text(encoding="utf-8")))
        questions = questionnaire.questions
        checks.append({"id": "schema:questionnaire", "passed": True, "question_count": len(questions)})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:questionnaire", "passed": False, "error": str(exc)})
        checks.append({"id": "content:human-confirmation", "passed": False, "error": "questionnaire unavailable"})
        return checks

    ids = {item.interaction_id for item in questions}
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
        report = WeaponLibraryCandidateReport.model_validate(yaml.safe_load(report_path.read_text(encoding="utf-8")))
        candidates = report.candidates
        checks = [{"id": "schema:weapon-library-candidates", "passed": True, "candidate_count": len(candidates)}]
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
            "passed": all(item.status == "candidate" and item.human_confirmation_required is True for item in candidates)
            and "candidate" in review_text.lower(),
        }
    )
    return checks


def _content_checks(ai: Path, inventory: ProjectInventory) -> list[dict[str, Any]]:
    return [
        _workflow_skills_check(ai),
        _workflow_skill_config_reference_check(ai),
        _workflow_routing_policy_check(ai),
        _risk_context_consistency_check(ai, inventory),
        _maturity_routing_evidence_check(ai),
        _workflow_recommendation_review_check(ai),
        _maturity_review_artifact_check(ai),
        _asset_candidate_review_check(ai),
        _candidate_governance_check(ai),
        _self_improve_package_check(ai),
        _experience_summary_artifact_check(ai),
        _runtime_task_run_artifacts_check(ai),
        _scan_report_check(ai, inventory),
        _init_summary_check(ai),
        _guide_quality_check(ai),
        _project_context_evidence_context_check(ai, inventory),
        _stack_specific_guide_check(ai, inventory),
        _sensor_quality_check(ai),
        _weapon_library_selection_check(ai, inventory),
        _hard_gate_command_evidence_check(ai),
    ]


def _init_summary_check(ai: Path) -> dict[str, Any]:
    path = ai / "init-summary.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    required_sections = [
        "## 当前成熟度",
        "## 主要阻断项",
        "## 建议下一步",
        "## 待人工确认",
        "## Benchmark 健康度",
        "## 推荐入口文件",
        "## 本次未执行的事项",
    ]
    required_entries = [
        ".ai/maturity-report.md",
        ".ai/human-input-needed.md",
        ".ai/human-input-needed.md#处理方式",
        ".ai/sensors/verification.md",
        "benchmark_status=",
        "quality_status=",
        ".ai/task-runs",
    ]
    missing = [
        item
        for item in [
            *required_sections,
            *required_entries,
            *_missing_init_summary_confirmation_ids(ai, text),
        ]
        if item not in text
    ]
    return {
        "id": "content:init-summary",
        "passed": not missing,
        "missing": missing,
    }


def _scan_report_check(ai: Path, inventory: ProjectInventory) -> dict[str, Any]:
    path = ai / "scan-report.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    required_headings = [
        "# Scan Report",
        "## Evidence",
        "## LLM Evidence Expansion",
        "## Evidence Coverage",
        "## Stack Evidence Validation",
        "## Scan Warnings",
        "## Risk Areas",
        "## Command Candidates",
    ]
    missing = [item for item in required_headings if not _has_markdown_heading(text, item)]
    if "Primary stack: `" not in text:
        missing.append("Primary stack: `")

    evidence_text = _section_text(text, "## Evidence", "## LLM Evidence Expansion")
    for evidence_path in _inventory_evidence_paths(inventory):
        if f"`{evidence_path}`" not in evidence_text:
            missing.append(f"missing_evidence_path:{evidence_path}")

    expansion_text = _section_text(text, "## LLM Evidence Expansion", "## Evidence Coverage")
    _append_missing_evidence_expansion_details(missing, expansion_text, inventory)

    coverage_text = _section_text(text, "## Evidence Coverage", "## Stack Evidence Validation")
    coverage = _scan_metadata(inventory).get("coverage")
    if isinstance(coverage, dict):
        selected = coverage.get("selected_evidence_count")
        detected = coverage.get("detected_file_count", _scan_metadata(inventory).get("evidence_file_count"))
        if selected is not None and detected is not None and f"evidence_selected={selected}/{detected}" not in coverage_text:
            missing.append(f"missing_evidence_selected:{selected}/{detected}")
        for selected_path in _coverage_selected_paths(coverage):
            if f"`{selected_path}`" not in coverage_text:
                missing.append(f"missing_coverage_selected_path:{selected_path}")

    validation_text = _section_text(text, "## Stack Evidence Validation", "## Scan Warnings")
    validation = inventory.stack_extensions.get("scan_validation")
    if isinstance(validation, dict):
        for claim in _list_value(validation, "checked_claims"):
            if f"`{claim}`" not in validation_text:
                missing.append(f"missing_checked_claim:{claim}")
        for claim in _list_value(validation, "supported_claims"):
            if f"`{claim}`" not in validation_text:
                missing.append(f"missing_supported_claim:{claim}")
        unsupported = validation.get("unsupported_claims")
        if isinstance(unsupported, list):
            for item in unsupported:
                if isinstance(item, dict):
                    stack = str(item.get("stack") or "").strip()
                    if stack and f"unsupported_claim=`{stack}`" not in validation_text:
                        missing.append(f"missing_unsupported_claim:{stack}")

    warning_text = _section_text(text, "## Scan Warnings", "## Risk Areas")
    for warning in _scan_report_warnings(inventory):
        code = str(warning.get("code") or "").strip()
        if code and f"`{code}`" not in warning_text:
            missing.append(f"missing_scan_warning:{code}")

    risk_text = _section_text(text, "## Risk Areas", "## Command Candidates")
    for risk in _benchmark_risk_areas(inventory)[:8]:
        risk_path = str(risk.get("path") or risk.get("area") or "").strip()
        if risk_path and f"`{risk_path}`" not in risk_text:
            missing.append(f"missing_risk_area:{risk_path}")

    command_text = _section_text(text, "## Command Candidates", None)
    try:
        catalog = CommandCatalog.model_validate(yaml.safe_load((ai / "command-catalog.yaml").read_text(encoding="utf-8")))
    except Exception:
        catalog = CommandCatalog(commands=[])
    for command in catalog.commands:
        if f"`{command.id}`" not in command_text:
            missing.append(f"missing_command_id:{command.id}")
        if not _command_report_line_has_confidence(command_text, command.id):
            missing.append(f"missing_command_confidence:{command.id}")

    return {
        "id": "content:scan-report",
        "passed": not missing,
        "missing": missing,
    }


def _section_text(text: str, start: str, end: str | None) -> str:
    if start not in text:
        return ""
    section = text.split(start, 1)[1]
    if end and end in section:
        section = section.split(end, 1)[0]
    return section


def _has_markdown_heading(text: str, heading: str) -> bool:
    return text.startswith(f"{heading}\n") or f"\n{heading}\n" in text


def _command_report_line_has_confidence(command_text: str, command_id: str) -> bool:
    command_marker = f"`{command_id}`"
    return any(command_marker in line and "confidence=`" in line for line in command_text.splitlines())


def _append_missing_evidence_expansion_details(
    missing: list[str],
    expansion_text: str,
    inventory: ProjectInventory,
) -> None:
    plan = _inventory_evidence_expansion(inventory)
    if not plan:
        if "evidence_expansion=not_run" not in expansion_text:
            missing.append("missing_evidence_expansion_not_run")
        return
    for path in _plan_list_value(plan, "requested_paths"):
        if f"`{path}`" not in expansion_text:
            missing.append(f"missing_expansion_requested_path:{path}")
    for path in _plan_list_value(plan, "read_paths"):
        if f"`{path}`" not in expansion_text:
            missing.append(f"missing_expansion_read_path:{path}")
    for focus in _plan_list_value(plan, "risk_focus"):
        if f"`{focus}`" not in expansion_text:
            missing.append(f"missing_expansion_risk_focus:{focus}")
    confidence = _plan_scalar_value(plan, "confidence")
    if confidence and f"confidence=`{confidence}`" not in expansion_text:
        missing.append(f"missing_expansion_confidence:{confidence}")
    read_file_count = _plan_scalar_value(plan, "read_file_count")
    if read_file_count and f"read_file_count={read_file_count}" not in expansion_text:
        missing.append(f"missing_expansion_read_file_count:{read_file_count}")
    rationale = _plan_scalar_value(plan, "rationale")
    if rationale and rationale not in expansion_text:
        missing.append("missing_expansion_rationale")


def _scan_metadata(inventory: ProjectInventory) -> dict[str, Any]:
    metadata = inventory.stack_extensions.get("scan_metadata", {})
    return metadata if isinstance(metadata, dict) else {}


def _coverage_selected_paths(coverage: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    buckets = coverage.get("bucket_coverage")
    if not isinstance(buckets, list):
        return []
    for bucket in buckets:
        if not isinstance(bucket, dict):
            continue
        selected_paths = bucket.get("selected_paths")
        if not isinstance(selected_paths, list):
            continue
        for item in selected_paths:
            path = str(item).strip()
            if path and path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def _list_value(container: dict[str, Any], field: str) -> list[str]:
    value = container.get(field)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _scan_report_warnings(inventory: ProjectInventory) -> list[dict[str, Any]]:
    warnings = inventory.stack_extensions.get("scan_warnings")
    if isinstance(warnings, list) and warnings:
        return [item for item in warnings if isinstance(item, dict)]
    metadata_warnings = _scan_metadata(inventory).get("warnings", [])
    if isinstance(metadata_warnings, list):
        return [item for item in metadata_warnings if isinstance(item, dict)]
    return []


def _missing_init_summary_confirmation_ids(ai: Path, text: str) -> list[str]:
    path = ai / "questionnaire.yaml"
    if not path.exists():
        return []
    try:
        questionnaire = Questionnaire.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except Exception:
        return ["schema:questionnaire"]
    return [
        question.interaction_id
        for question in questionnaire.questions[:3]
        if question.interaction_id not in text
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


def _benchmark_risk_areas(inventory: ProjectInventory) -> list[dict[str, Any]]:
    risk_areas = inventory.stack_extensions.get("risk_areas", [])
    if isinstance(risk_areas, list) and risk_areas:
        return [item for item in risk_areas if isinstance(item, dict)]
    proposal = inventory.stack_extensions.get("llm_scan_proposal", {})
    if isinstance(proposal, dict):
        proposal_risks = proposal.get("risk_areas", [])
        if isinstance(proposal_risks, list):
            return [item for item in proposal_risks if isinstance(item, dict)]
    return []


def _risk_context_consistency_check(ai: Path, inventory: ProjectInventory) -> dict[str, Any]:
    risk_paths = [
        str(risk.get("path") or risk.get("area") or "unknown")
        for risk in _benchmark_risk_areas(inventory)[:5]
    ]
    if not risk_paths:
        return {
            "id": "content:risk-context-consistency",
            "passed": True,
            "risk_area_count": 0,
            "errors": [],
        }

    guide_path = ai / "guides" / "project-context.md"
    sensor_path = ai / "sensors" / "verification.md"
    guide_text = guide_path.read_text(encoding="utf-8") if guide_path.exists() else ""
    sensor_text = sensor_path.read_text(encoding="utf-8") if sensor_path.exists() else ""
    try:
        config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover
        return {
            "id": "content:risk-context-consistency",
            "passed": False,
            "risk_area_count": len(risk_paths),
            "errors": [str(exc)],
        }

    standard_rules = [rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation"]
    standard_rule = standard_rules[0] if standard_rules else None
    standard_triggers = set(standard_rule.triggers) if standard_rule else set()
    standard_rationale = standard_rule.rationale if standard_rule else ""

    errors: list[str] = []
    for risk_path in risk_paths:
        if risk_path not in guide_text:
            errors.append(f"missing_project_context_risk:{risk_path}")
        if risk_path not in sensor_text:
            errors.append(f"missing_verification_sensor_risk:{risk_path}")
        if f"risk_area:{risk_path}" not in standard_triggers and risk_path not in standard_rationale:
            errors.append(f"missing_routing_risk:{risk_path}")

    return {
        "id": "content:risk-context-consistency",
        "passed": not errors,
        "risk_area_count": len(risk_paths),
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


def _base_benchmark_evidence_sources(ai: Path) -> tuple[set[str], list[str]]:
    allowed = set(CORE_EVIDENCE_SOURCES)
    errors: list[str] = []

    evidence_path = ai / "maturity-evidence.yaml"
    if evidence_path.exists():
        try:
            evidence = MaturityEvidencePack.model_validate(yaml.safe_load(evidence_path.read_text(encoding="utf-8")))
            allowed.update(maturity_evidence_source_allowlist(evidence))
        except Exception:  # pragma: no cover - schema checks expose the detailed validation error
            errors.append("invalid_evidence_allowlist_source:maturity-evidence")

    index_path = ai / "experience" / "experience-index.yaml"
    if index_path.exists():
        try:
            index = ExperienceIndex.model_validate(yaml.safe_load(index_path.read_text(encoding="utf-8")))
            allowed.update(source.path for source in index.sources)
        except Exception:  # pragma: no cover
            errors.append("invalid_evidence_allowlist_source:experience-index")

    return allowed, errors


def _extend_maturity_review_evidence_sources(ai: Path, allowed: set[str], errors: list[str]) -> None:
    path = ai / "review" / "maturity-review.yaml"
    if not path.exists():
        return
    allowed.add(".ai/review/maturity-review.yaml")
    try:
        report = MaturityReviewReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except Exception:  # pragma: no cover
        errors.append("invalid_evidence_allowlist_source:maturity-review")
        return
    allowed.update(source for review in report.candidate_reviews for source in review.evidence_sources)


def _extend_experience_summary_evidence_sources(ai: Path, allowed: set[str], errors: list[str]) -> None:
    path = ai / "experience" / "experience-summary.yaml"
    if not path.exists():
        return
    allowed.add(".ai/experience/experience-summary.yaml")
    try:
        report = ExperienceSummaryReport.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except Exception:  # pragma: no cover
        errors.append("invalid_evidence_allowlist_source:experience-summary")
        return
    allowed.update(source for finding in report.findings for source in finding.evidence_sources)


def _workflow_recommendation_review_check(ai: Path) -> dict[str, Any]:
    yaml_path = ai / "review" / "workflow-routing-recommendation.yaml"
    markdown_path = ai / "review" / "workflow-routing-recommendation.md"
    history_index_path = ai / "review" / "workflow-routing-recommendations" / "index.yaml"
    history_summary_path = ai / "review" / "workflow-routing-recommendations.md"
    latest_present = yaml_path.exists() or markdown_path.exists()
    history_present = history_index_path.exists() or history_summary_path.exists()
    if not latest_present and not history_present:
        return {"id": "content:workflow-recommendation-review", "passed": True, "present": False}

    errors: list[str] = []
    report: WorkflowRecommendationReport | None = None
    if latest_present and (not yaml_path.exists() or not markdown_path.exists()):
        errors.append("incomplete_recommendation_artifact_pair")

    try:
        config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover - captured in benchmark report
        return {"id": "content:workflow-recommendation-review", "passed": False, "present": True, "errors": [str(exc)]}

    available_workflows = set(config.workflows)
    available_rule_ids = {rule.id for rule in config.workflow_routing.rules}
    allowed_evidence_sources, allowlist_errors = _base_benchmark_evidence_sources(ai)
    errors.extend(allowlist_errors)
    if latest_present and yaml_path.exists():
        try:
            report = WorkflowRecommendationReport.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
        except Exception as exc:  # pragma: no cover - captured in benchmark report
            return {"id": "content:workflow-recommendation-review", "passed": False, "present": True, "errors": [str(exc)]}
        errors.extend(_workflow_recommendation_report_errors(report, available_workflows, available_rule_ids, allowed_evidence_sources))

        markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
        if _missing_workflow_recommendation_sections(markdown):
            errors.append("missing_markdown_sections")

    history_count = 0
    if history_present:
        history_errors, history_count = _workflow_recommendation_history_errors(
            ai,
            config,
            allowed_evidence_sources,
        )
        errors.extend(history_errors)

    return {
        "id": "content:workflow-recommendation-review",
        "passed": not errors,
        "present": True,
        "recommended_workflow": report.recommended_workflow if report else None,
        "matched_rule_count": len(report.matched_rule_ids) if report else 0,
        "history_count": history_count,
        "errors": errors,
    }


def _workflow_recommendation_report_errors(
    report: WorkflowRecommendationReport,
    available_workflows: set[str],
    available_rule_ids: set[str],
    allowed_evidence_sources: set[str],
) -> list[str]:
    errors: list[str] = []
    if report.recommended_workflow not in available_workflows:
        errors.append("unknown_recommended_workflow")
    if any(rule_id not in available_rule_ids for rule_id in report.matched_rule_ids):
        errors.append("unknown_matched_rule_ids")
    if report.review_status != "pending_harness_maintainer_review":
        errors.append("recommendation_not_review_only")
    if any(not source.startswith(".ai/") for source in report.evidence_sources):
        errors.append("evidence_source_outside_ai")
    if unknown_evidence_sources(report.evidence_sources, allowed_evidence_sources):
        errors.append("unknown_evidence_source")
    return errors


def _workflow_recommendation_history_errors(
    ai: Path,
    config: HarnessConfig,
    allowed_evidence_sources: set[str],
) -> tuple[list[str], int]:
    history_index_path = ai / "review" / "workflow-routing-recommendations" / "index.yaml"
    history_summary_path = ai / "review" / "workflow-routing-recommendations.md"
    errors: list[str] = []
    if not history_index_path.exists() or not history_summary_path.exists():
        errors.append("incomplete_recommendation_history_pair")
        return errors, 0

    try:
        history = WorkflowRecommendationHistory.model_validate(yaml.safe_load(history_index_path.read_text(encoding="utf-8")) or {})
    except Exception as exc:  # pragma: no cover - captured in benchmark report
        return [str(exc)], 0

    summary = history_summary_path.read_text(encoding="utf-8")
    if "# Workflow Routing Recommendation History" not in summary or "## Review Boundary" not in summary:
        errors.append("missing_recommendation_history_sections")

    available_workflows = set(config.workflows)
    available_rule_ids = {rule.id for rule in config.workflow_routing.rules}
    for item in history.recommendations:
        recommendation_yaml = ai.parent / item.yaml_path
        recommendation_markdown = ai.parent / item.markdown_path
        if not recommendation_yaml.exists() or not recommendation_markdown.exists():
            errors.append("incomplete_recommendation_history_entry")
            continue
        try:
            report = WorkflowRecommendationReport.model_validate(yaml.safe_load(recommendation_yaml.read_text(encoding="utf-8")))
        except Exception as exc:  # pragma: no cover - captured in benchmark report
            errors.append(str(exc))
            continue
        if report.task_id != item.task_id or report.recommended_workflow != item.recommended_workflow:
            errors.append("recommendation_history_entry_mismatch")
        errors.extend(_workflow_recommendation_report_errors(report, available_workflows, available_rule_ids, allowed_evidence_sources))
        markdown = recommendation_markdown.read_text(encoding="utf-8")
        if _missing_workflow_recommendation_sections(markdown):
            errors.append("missing_recommendation_history_markdown_sections")
    return errors, len(history.recommendations)


def _missing_workflow_recommendation_sections(markdown: str) -> bool:
    required_sections = [
        "# Workflow Routing Recommendation",
        "## Task",
        "## Recommended Workflow",
        "## Matched Routing Rules",
        "## Required Harness Assets",
        "## Review Boundary",
    ]
    return any(section not in markdown for section in required_sections)


def _maturity_review_artifact_check(ai: Path) -> dict[str, Any]:
    yaml_path = ai / "review" / "maturity-review.yaml"
    markdown_path = ai / "review" / "maturity-review.md"
    if not yaml_path.exists() and not markdown_path.exists():
        return {"id": "content:maturity-review-artifact", "passed": True, "present": False}

    errors: list[str] = []
    if not yaml_path.exists() or not markdown_path.exists():
        errors.append("incomplete_maturity_review_artifact_pair")

    try:
        report = MaturityReviewReport.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
        improvements = ImprovementCandidateReport.model_validate(
            yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
        )
    except Exception as exc:  # pragma: no cover - captured in benchmark report
        return {"id": "content:maturity-review-artifact", "passed": False, "present": True, "errors": [str(exc)]}

    if report.review_status != "pending_harness_maintainer_review":
        errors.append("maturity_review_not_review_only")

    known_candidate_ids = {candidate.id for candidate in improvements.candidates}
    allowed_evidence_sources, allowlist_errors = _base_benchmark_evidence_sources(ai)
    errors.extend(allowlist_errors)
    allowed_evidence_sources.update(source for candidate in improvements.candidates for source in candidate.evidence_sources)
    for item in report.candidate_reviews:
        if item.candidate_id not in known_candidate_ids:
            errors.append("unknown_candidate_id")
        if any(not source.startswith(".ai/") for source in item.evidence_sources):
            errors.append("evidence_source_outside_ai")
        if unknown_evidence_sources(item.evidence_sources, allowed_evidence_sources):
            errors.append("unknown_evidence_source")

    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    required_sections = [
        "# Maturity Review",
        "## Summary",
        "## Candidate Reviews",
        "## Missing Candidates",
        "## Global Risks",
        "## Review Boundary",
    ]
    if any(section not in markdown for section in required_sections):
        errors.append("missing_markdown_sections")

    return {
        "id": "content:maturity-review-artifact",
        "passed": not errors,
        "present": True,
        "candidate_review_count": len(report.candidate_reviews),
        "errors": sorted(set(errors)),
    }


def _asset_candidate_review_check(ai: Path) -> dict[str, Any]:
    yaml_path = ai / "review" / "asset-candidates.yaml"
    markdown_by_kind = {
        "guide": ai / "review" / "asset-candidate-guides.md",
        "sensor": ai / "review" / "asset-candidate-sensors.md",
        "workflow_policy": ai / "review" / "asset-candidate-workflows.md",
    }
    markdown_paths = list(markdown_by_kind.values())
    present_paths = [path for path in [yaml_path, *markdown_paths] if path.exists()]
    if not present_paths:
        return {"id": "content:asset-candidate-review", "passed": True, "present": False}

    errors: list[str] = []
    if not yaml_path.exists() or len(present_paths) != 4:
        errors.append("incomplete_asset_candidate_artifact_set")

    try:
        report = AssetCandidateReport.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
        improvements = ImprovementCandidateReport.model_validate(
            yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8"))
        )
    except Exception as exc:  # pragma: no cover - captured in benchmark report
        return {"id": "content:asset-candidate-review", "passed": False, "present": True, "errors": [str(exc)]}

    known_candidate_ids = {candidate.id for candidate in improvements.candidates}
    allowed_evidence_sources, allowlist_errors = _base_benchmark_evidence_sources(ai)
    errors.extend(allowlist_errors)
    allowed_evidence_sources.update(source for improvement in improvements.candidates for source in improvement.evidence_sources)
    _extend_maturity_review_evidence_sources(ai, allowed_evidence_sources, errors)
    _extend_experience_summary_evidence_sources(ai, allowed_evidence_sources, errors)
    for candidate in report.candidates:
        if (
            candidate.source_candidate_id
            and candidate.source_review_decision != "missing"
            and candidate.source_candidate_id not in known_candidate_ids
        ):
            errors.append("unknown_source_candidate_id")
        if not is_safe_ai_relative_path(candidate.suggested_path):
            errors.append("suggested_path_outside_ai")
        if candidate.kind == "workflow_policy" and candidate.suggested_path != ".ai/harness-config.yaml":
            errors.append("workflow_policy_target_not_harness_config")
        if any(not source.startswith(".ai/") for source in candidate.evidence_sources):
            errors.append("evidence_source_outside_ai")
        if unknown_evidence_sources(candidate.evidence_sources, allowed_evidence_sources):
            errors.append("unknown_evidence_source")

    required_sections = ["### Rationale", "### Draft Content", "### Evidence Sources", "### Acceptance Checks"]
    candidate_kinds = {candidate.kind for candidate in report.candidates}
    for kind, path in markdown_by_kind.items():
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if kind in candidate_kinds and any(section not in text for section in required_sections):
            errors.append("missing_markdown_sections")
            break

    return {
        "id": "content:asset-candidate-review",
        "passed": not errors,
        "present": True,
        "candidate_count": len(report.candidates),
        "errors": sorted(set(errors)),
    }


def _candidate_governance_check(ai: Path) -> dict[str, Any]:
    yaml_path = ai / "review" / "candidate-governance.yaml"
    markdown_path = ai / "review" / "candidate-governance.md"
    if not yaml_path.exists() and not markdown_path.exists():
        return {"id": "content:candidate-governance", "passed": True, "present": False}

    errors: list[str] = []
    if not yaml_path.exists() or not markdown_path.exists():
        errors.append("incomplete_candidate_governance_pair")

    try:
        log = CandidateGovernanceLog.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
        candidates = AssetCandidateReport.model_validate(yaml.safe_load((ai / "review" / "asset-candidates.yaml").read_text(encoding="utf-8")))
        config = HarnessConfig.model_validate(yaml.safe_load((ai / "harness-config.yaml").read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover - captured in benchmark report
        return {"id": "content:candidate-governance", "passed": False, "present": True, "errors": [str(exc)]}

    candidates_by_id = {candidate.id: candidate for candidate in candidates.candidates}
    rules_by_id = {rule.id: rule for rule in config.workflow_routing.rules}
    for decision in log.decisions:
        source = candidates_by_id.get(decision.candidate_id)
        if source is None:
            errors.append("unknown_candidate_id")
        elif source.kind != decision.candidate_kind:
            errors.append("candidate_kind_mismatch")
        elif source.suggested_path != decision.suggested_path:
            errors.append("suggested_path_mismatch")
        elif source.source_candidate_id != decision.source_candidate_id:
            errors.append("source_candidate_id_mismatch")
        if decision.source_report != ".ai/review/asset-candidates.yaml":
            errors.append("unexpected_source_report")
        if not is_safe_ai_relative_path(decision.suggested_path):
            errors.append("suggested_path_outside_ai")
        if any(not source_path.startswith(".ai/") for source_path in decision.evidence_sources):
            errors.append("evidence_source_outside_ai")
        for applied_path in decision.applied_paths:
            if not is_safe_ai_relative_path(applied_path):
                errors.append("applied_path_outside_ai")
                continue
            if decision.decision == "applied" and not (ai.parent / applied_path).exists():
                errors.append("applied_path_missing")
        if decision.decision == "applied" and not decision.applied_paths:
            errors.append("applied_decision_without_applied_path")
        if decision.decision == "applied" and source and source.kind == "workflow_policy":
            if source.source_review_decision not in {"support", "revise"}:
                errors.append("workflow_policy_applied_without_supported_review")
            if source.suggested_path != ".ai/harness-config.yaml":
                errors.append("workflow_policy_target_not_harness_config")
            if ".ai/harness-config.yaml" not in decision.applied_paths:
                errors.append("workflow_policy_applied_without_harness_config")
            if source.workflow_policy_patch is None:
                errors.append("workflow_policy_patch_missing")
            else:
                applied_rule = rules_by_id.get(source.workflow_policy_patch.rule.id)
                if applied_rule is None:
                    errors.append("workflow_policy_rule_missing")
                elif applied_rule.model_dump(mode="json") != source.workflow_policy_patch.rule.model_dump(mode="json"):
                    errors.append("workflow_policy_rule_mismatch")

    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    required_sections = ["# Candidate Governance", "## Decisions", "## Review Boundary"]
    if any(section not in markdown for section in required_sections):
        errors.append("missing_markdown_sections")

    return {
        "id": "content:candidate-governance",
        "passed": not errors,
        "present": True,
        "decision_count": len(log.decisions),
        "errors": sorted(set(errors)),
    }


def _self_improve_package_check(ai: Path) -> dict[str, Any]:
    yaml_path = ai / "review" / "self-improve-package.yaml"
    markdown_path = ai / "review" / "self-improve-package.md"
    if not yaml_path.exists() and not markdown_path.exists():
        return {"id": "content:self-improve-package", "passed": True, "present": False}

    errors: list[str] = []
    if not yaml_path.exists() or not markdown_path.exists():
        errors.append("incomplete_self_improve_package_pair")

    try:
        manifest = SelfImprovePackageManifest.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover - captured in benchmark report
        return {"id": "content:self-improve-package", "passed": False, "present": True, "errors": [str(exc)]}

    if manifest.review_status != "pending_harness_maintainer_review":
        errors.append("package_not_review_only")
    for artifact in manifest.generated_artifacts:
        if not artifact.path.startswith(".ai/"):
            errors.append("artifact_path_outside_ai")
            continue
        if not (ai.parent / artifact.path).exists():
            errors.append("generated_artifact_missing")

    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    required_sections = [
        "# Self-Improve Package",
        "## Maturity Snapshot",
        "## Generated Artifacts",
        "## Candidate Counts",
        "## Next Actions",
        "## Review Boundary",
    ]
    if any(section not in markdown for section in required_sections):
        errors.append("missing_markdown_sections")
    if "pending_harness_maintainer_review" not in markdown:
        errors.append("missing_review_status_boundary")

    return {
        "id": "content:self-improve-package",
        "passed": not errors,
        "present": True,
        "asset_candidate_count": manifest.candidate_counts.asset_candidates,
        "errors": sorted(set(errors)),
    }


def _experience_summary_artifact_check(ai: Path) -> dict[str, Any]:
    yaml_path = ai / "experience" / "experience-summary.yaml"
    markdown_path = ai / "experience" / "experience-summary.md"
    if not yaml_path.exists() and not markdown_path.exists():
        return {"id": "content:experience-summary-artifact", "passed": True, "present": False}

    errors: list[str] = []
    if not yaml_path.exists() or not markdown_path.exists():
        errors.append("incomplete_experience_summary_artifact_pair")

    try:
        report = ExperienceSummaryReport.model_validate(yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover - captured in benchmark report
        return {"id": "content:experience-summary-artifact", "passed": False, "present": True, "errors": [str(exc)]}

    if report.review_status != "pending_harness_maintainer_review":
        errors.append("summary_not_review_only")
    if any(not source.startswith(".ai/") for finding in report.findings for source in finding.evidence_sources):
        errors.append("evidence_source_outside_ai")
    allowed_evidence_sources, allowlist_errors = _base_benchmark_evidence_sources(ai)
    errors.extend(allowlist_errors)
    allowed_evidence_sources.update(
        source for source in EXPERIENCE_SUMMARY_SOURCE_INPUTS if (ai.parent / source).exists()
    )
    if unknown_evidence_sources(
        (source for finding in report.findings for source in finding.evidence_sources),
        allowed_evidence_sources,
    ):
        errors.append("unknown_evidence_source")

    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else ""
    required_sections = ["# Experience Summary", "## Summary", "## Findings", "## Warnings"]
    if any(section not in markdown for section in required_sections):
        errors.append("missing_markdown_sections")

    return {
        "id": "content:experience-summary-artifact",
        "passed": not errors,
        "present": True,
        "finding_count": len(report.findings),
        "errors": sorted(set(errors)),
    }


def _runtime_task_run_artifacts_check(ai: Path) -> dict[str, Any]:
    task_runs = ai / "task-runs"
    if not task_runs.exists() or not any(path.is_dir() for path in task_runs.iterdir()):
        return {"id": "content:runtime-task-run-artifacts", "passed": True, "present": False}
    try:
        summary = summarize_runtime_task_runs(ai)
    except RuntimeTaskRunError as exc:
        return {
            "id": "content:runtime-task-run-artifacts",
            "passed": False,
            "present": True,
            "errors": [str(exc)],
        }
    return {
        "id": "content:runtime-task-run-artifacts",
        "passed": True,
        "present": True,
        "task_run_count": summary.task_run_count,
        "passed_sensor_count": summary.passed_sensor_count,
        "failed_sensor_count": summary.failed_sensor_count,
        "skipped_sensor_count": summary.skipped_sensor_count,
        "unresolved_sensor_count": summary.unresolved_sensor_count,
        "repair_attempt_count": summary.repair_attempt_count,
        "source_paths": summary.source_paths,
    }


def _guide_quality_check(ai: Path) -> dict[str, Any]:
    required_sections = ["## 当前项目事实", "## 来源证据", "## 候选规则", "## Harness Builder 推荐补齐项", "## 人工确认点"]
    guide = ai / "guides" / "project-context.md"
    text = guide.read_text(encoding="utf-8") if guide.exists() else ""
    passed = all(section in text for section in required_sections)
    return {"id": "content:guides-quality", "passed": passed}


def _project_context_evidence_context_check(ai: Path, inventory: ProjectInventory) -> dict[str, Any]:
    guide = ai / "guides" / "project-context.md"
    text = guide.read_text(encoding="utf-8") if guide.exists() else ""
    missing: list[str] = []

    if "## 来源证据" not in text:
        missing.append("missing_source_evidence_section")
        evidence_text = ""
    else:
        evidence_text = text.split("## 来源证据", 1)[1]
        if "## LLM 证据扩展" in evidence_text:
            evidence_text = evidence_text.split("## LLM 证据扩展", 1)[0]

    evidence_paths = _inventory_evidence_paths(inventory)
    for path in evidence_paths:
        if f"`{path}`" not in evidence_text:
            missing.append(f"missing_evidence_path:{path}")

    if "## LLM 证据扩展" not in text:
        missing.append("missing_llm_evidence_expansion_section")
        expansion_text = ""
    else:
        expansion_text = text.split("## LLM 证据扩展", 1)[1]

    plan = _inventory_evidence_expansion(inventory)
    if not plan:
        if "evidence_expansion=not_run" not in expansion_text:
            missing.append("missing_evidence_expansion_not_run")
    else:
        for path in _plan_list_value(plan, "requested_paths"):
            if f"`{path}`" not in expansion_text:
                missing.append(f"missing_expansion_requested_path:{path}")
        for path in _plan_list_value(plan, "read_paths"):
            if f"`{path}`" not in expansion_text:
                missing.append(f"missing_expansion_read_path:{path}")
        for focus in _plan_list_value(plan, "risk_focus"):
            if f"`{focus}`" not in expansion_text:
                missing.append(f"missing_expansion_risk_focus:{focus}")
        confidence = _plan_scalar_value(plan, "confidence")
        if confidence and f"confidence=`{confidence}`" not in expansion_text:
            missing.append(f"missing_expansion_confidence:{confidence}")
        read_file_count = _plan_scalar_value(plan, "read_file_count")
        if read_file_count and f"read_file_count={read_file_count}" not in expansion_text:
            missing.append(f"missing_expansion_read_file_count:{read_file_count}")
        rationale = _plan_scalar_value(plan, "rationale")
        if rationale and rationale not in expansion_text:
            missing.append("missing_expansion_rationale")

    return {
        "id": "content:project-context-evidence-context",
        "passed": not missing,
        "evidence_path_count": len(evidence_paths),
        "missing": missing,
    }


def _inventory_evidence_paths(inventory: ProjectInventory) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for bucket in (inventory.evidence, inventory.documents, inventory.configs, inventory.ci_files):
        for item in bucket:
            path = str(item.get("path") or "").strip()
            if path and path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def _inventory_evidence_expansion(inventory: ProjectInventory) -> Any:
    scan_metadata = inventory.stack_extensions.get("scan_metadata", {})
    if not isinstance(scan_metadata, dict):
        return None
    return scan_metadata.get("evidence_expansion") or scan_metadata.get("evidence_expansion_plan")


def _plan_list_value(plan: Any, field: str) -> list[str]:
    value = plan.get(field) if isinstance(plan, dict) else getattr(plan, field, None)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _plan_scalar_value(plan: Any, field: str) -> str:
    value = plan.get(field) if isinstance(plan, dict) else getattr(plan, field, None)
    return str(value).strip() if value is not None else ""


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
    weak = [_hard_gate_command_evidence_issue(ai.parent, command) for command in hard_commands]
    weak = [item for item in weak if item is not None]
    return {
        "id": "content:hard-gate-command-evidence",
        "passed": bool(hard_commands) and not weak,
        "hard_gate_count": len(hard_commands),
        "weak_commands": weak,
    }


def _hard_gate_command_evidence_issue(root: Path, command: CommandDefinition) -> dict[str, str] | None:
    if not command.source:
        return {"id": command.id, "source": command.source, "confidence": command.confidence, "reason": "missing_source"}
    if command.confidence == "low":
        return {"id": command.id, "source": command.source, "confidence": command.confidence, "reason": "low_confidence"}
    source_path = (root / command.source).resolve()
    try:
        source_path.relative_to(root)
    except ValueError:
        return {"id": command.id, "source": command.source, "confidence": command.confidence, "reason": "source_path_outside_repo"}
    if not source_path.exists() or not source_path.is_file():
        return {"id": command.id, "source": command.source, "confidence": command.confidence, "reason": "source_path_missing"}
    return None


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
