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
    checks.extend(_content_checks(ai, inventory))
    if profile:
        checks.append({"id": "profile_matches_stack", "passed": profile == inventory.primary_stack, "expected": profile, "actual": inventory.primary_stack})

    report = {
        "schema_version": "1.0",
        "repo_name": root.name,
        "profile": profile or inventory.primary_stack,
        "status": "passed" if all(check["passed"] for check in checks) else "failed",
        "checks": checks,
    }
    report["checks"].append({"id": "schema:benchmark-report", "passed": True})
    report["status"] = "passed" if all(check["passed"] for check in report["checks"]) else "failed"
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


def _benchmark_task(profile: str) -> str:
    if profile == "java-spring":
        return "修复登录接口错误提示不一致的问题"
    return "调整 Catalog 相关低风险文案"
