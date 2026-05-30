from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from harness_builder_agent.schemas.benchmark_report import BenchmarkReport
from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.harness_config import HarnessConfig
from harness_builder_agent.schemas.harness_map import HarnessMap
from harness_builder_agent.schemas.improvement_candidate import ImprovementCandidateReport
from harness_builder_agent.schemas.maturity_report import MaturityReport
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.sensor_report import SensorReport
from harness_builder_agent.schemas.scan import LLMScanProposal, ScanMetadata
from harness_builder_agent.schemas.weapon_library import WeaponLibrarySelection
from harness_builder_agent.tools.assess_maturity import assess_maturity
from harness_builder_agent.tools.generate_improvements import generate_improvements
from harness_builder_agent.tools.generation_trace import GenerationTrace
from harness_builder_agent.tools.run_task import run_task
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
    "evolution-plan.md",
    "guides/project-context.md",
    "guides/coding-rules.md",
    "guides/architecture.md",
    "sensors/verification.md",
    "sensors/test-strategy.md",
    "skills/lightweight/SKILL.md",
    "skills/bugfix/SKILL.md",
    "improvement-candidates.yaml",
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
    run_task(root, _benchmark_task(profile or inventory.primary_stack))
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
    checks.extend(_runtime_trace_checks(ai))
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
        HarnessMap.model_validate(yaml.safe_load((ai / "task-runs" / "demo-task-001" / "harness-map.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:harness-map", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:harness-map", "passed": False, "error": str(exc)})

    try:
        SensorReport.model_validate(yaml.safe_load((ai / "task-runs" / "demo-task-001" / "sensor-report.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:sensor-report", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:sensor-report", "passed": False, "error": str(exc)})

    try:
        MaturityReport.model_validate(yaml.safe_load((ai / "maturity-score.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:maturity-score", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:maturity-score", "passed": False, "error": str(exc)})

    try:
        ImprovementCandidateReport.model_validate(yaml.safe_load((ai / "improvement-candidates.yaml").read_text(encoding="utf-8")))
        checks.append({"id": "schema:improvement-candidates", "passed": True})
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "schema:improvement-candidates", "passed": False, "error": str(exc)})
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


def _runtime_trace_checks(ai: Path) -> list[dict[str, Any]]:
    task_dir = ai / "task-runs" / "demo-task-001"
    summary_path = task_dir / "runtime-summary.yaml"
    events_path = task_dir / "workflow-events.jsonl"
    used_guides_path = task_dir / "used-guides.yaml"

    try:
        summary = yaml.safe_load(summary_path.read_text(encoding="utf-8"))
        required = {
            "schema_version",
            "task_id",
            "task_type",
            "selected_workflow",
            "hard_gate_count",
            "sensor_statuses",
            "unresolved_sensor_count",
            "used_guide_count",
            "workflow_skill_path",
        }
        schema_passed = required.issubset(set(summary))
        checks = [{"id": "schema:runtime-summary", "passed": schema_passed, "task_id": summary.get("task_id")}]
    except Exception as exc:  # pragma: no cover
        return [
            {"id": "schema:runtime-summary", "passed": False, "error": str(exc)},
            {"id": "content:runtime-workflow-trace", "passed": False, "error": "runtime summary unavailable"},
        ]

    try:
        events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        used_guides = yaml.safe_load(used_guides_path.read_text(encoding="utf-8"))
        stages = {event["stage"] for event in events}
        required_stages = {
            "task-classification",
            "guide-selection",
            "workflow-selection",
            "sensor-selection",
            "sensor-execution",
            "handoff",
            "experience-candidate",
        }
        required_guides = used_guides.get("required_guides", [])
        passed = (
            required_stages.issubset(stages)
            and len(required_guides) == summary.get("used_guide_count")
            and bool(summary.get("sensor_statuses"))
        )
        checks.append(
            {
                "id": "content:runtime-workflow-trace",
                "passed": passed,
                "stage_count": len(stages),
                "used_guide_count": len(required_guides),
            }
        )
    except Exception as exc:  # pragma: no cover
        checks.append({"id": "content:runtime-workflow-trace", "passed": False, "error": str(exc)})
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
        _harness_map_skill_check(ai),
        _guide_quality_check(ai),
        _stack_specific_guide_check(ai, inventory),
        _sensor_quality_check(ai),
        _weapon_library_selection_check(ai, inventory),
        _hard_gate_sensors_check(ai),
    ]


def _workflow_skills_check(ai: Path) -> dict[str, Any]:
    lightweight = ai / "skills" / "lightweight" / "SKILL.md"
    bugfix = ai / "skills" / "bugfix" / "SKILL.md"
    passed = (
        lightweight.exists()
        and bugfix.exists()
        and "轻量级开发工作流" in lightweight.read_text(encoding="utf-8")
        and "缺陷修复工作流" in bugfix.read_text(encoding="utf-8")
    )
    return {"id": "content:workflow-skills", "passed": passed}


def _harness_map_skill_check(ai: Path) -> dict[str, Any]:
    map_path = ai / "task-runs" / "demo-task-001" / "harness-map.yaml"
    if not map_path.exists():
        return {"id": "content:harness-map-workflow-skill", "passed": False, "error": "missing harness-map.yaml"}
    harness_map = HarnessMap.model_validate(yaml.safe_load(map_path.read_text(encoding="utf-8")))
    skill_path = harness_map.workflow_skill.get("path")
    passed = bool(skill_path) and (ai.parent / skill_path).exists()
    return {"id": "content:harness-map-workflow-skill", "passed": passed, "path": skill_path}


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


def _hard_gate_sensors_check(ai: Path) -> dict[str, Any]:
    report_path = ai / "task-runs" / "demo-task-001" / "sensor-report.yaml"
    if not report_path.exists():
        return {"id": "content:hard-gate-sensors-passed", "passed": False, "error": "missing sensor-report.yaml"}
    try:
        sensor_report = SensorReport.model_validate(yaml.safe_load(report_path.read_text(encoding="utf-8")))
    except Exception as exc:  # pragma: no cover
        return {"id": "content:hard-gate-sensors-passed", "passed": False, "error": str(exc)}

    failing = [result for result in sensor_report.sensor_results if result.status != "passed"]
    return {
        "id": "content:hard-gate-sensors-passed",
        "passed": not failing,
        "failed_or_skipped": [result.model_dump(mode="json") for result in failing],
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
            "runtime_trace_completeness": _score_runtime_trace_completeness(ai),
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
    try:
        sensor_report = SensorReport.model_validate(yaml.safe_load((ai / "task-runs" / "demo-task-001" / "sensor-report.yaml").read_text(encoding="utf-8")))
    except Exception as exc:
        return _score_item(0, [f"sensor-report.yaml 不可读：{exc}"], ["重新运行 task sensors。"])
    if not sensor_report.sensor_results:
        return _score_item(1, ["没有 hard gate sensor result。"], ["确认 hard gate sensor。"])
    if any(result.status == "passed" for result in sensor_report.sensor_results):
        return _score_item(5)
    return _score_item(3, ["存在 hard gate，但没有 passed result。"], ["处理 failed/skipped sensor。"])


def _score_failure_policy(ai: Path) -> dict[str, Any]:
    text = _read_text(ai / "sensors" / "verification.md")
    if text is None:
        return _score_item(0, ["verification sensor Markdown 不可读。"], ["重新生成 sensors。"])
    if "## 失败处理策略" not in text:
        return _score_item(0, ["缺少失败处理策略。"], ["补充失败处理策略。"])
    report = _hard_gate_sensors_check(ai)
    if report.get("failed_or_skipped") or report.get("passed"):
        return _score_item(5)
    return _score_item(3, ["有失败处理策略，但没有 hard gate 结果。"], ["运行 task sensors。"])


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
    check = _harness_map_skill_check(ai)
    if check["passed"]:
        return _score_item(5)
    return _score_item(0, [check.get("error", "workflow skill 引用无效。")], ["修复 harness-map workflow skill path。"])


def _score_runtime_trace_completeness(ai: Path) -> dict[str, Any]:
    checks = _runtime_trace_checks(ai)
    content = next((check for check in checks if check["id"] == "content:runtime-workflow-trace"), None)
    schema = next((check for check in checks if check["id"] == "schema:runtime-summary"), None)
    if content and content.get("passed"):
        return _score_item(5)
    if schema and schema.get("passed"):
        return _score_item(3, ["runtime summary 存在，但 workflow events 或 used guides 不完整。"], ["检查 runtime trace 产物。"])
    return _score_item(0, ["runtime trace 不可读。"], ["重新运行 task workflow。"])


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def _benchmark_task(profile: str) -> str:
    if profile == "java-spring":
        return "修复登录接口错误提示不一致的问题"
    return "调整 Catalog 相关低风险文案"
