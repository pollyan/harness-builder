from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from harness_builder.scanner.detectors.ci_docker import detect_ci_docker
from harness_builder.scanner.detectors.dotnet import detect_dotnet
from harness_builder.scanner.detectors.evidence_extractor import (
    _DOTNET_KEYWORDS,
    _JAVA_KEYWORDS,
    _NODE_KEYWORDS,
    _stack_mentions,
    extract_evidence,
)
from harness_builder.scanner.detectors.file_tree_collector import collect_file_tree
from harness_builder.scanner.detectors.filesystem import scan_filesystem
from harness_builder.scanner.detectors.generic_fallback import detect_generic_fallback
from harness_builder.scanner.detectors.java_maven import detect_java_maven
from harness_builder.scanner.detectors.llm_scanner import scan_with_llm
from harness_builder.scanner.detectors.node_frontend import detect_node_frontend
from harness_builder.scanner.detectors.shallow_code import detect_shallow_code_structure
from harness_builder.scanner.report import render_scanner_report


@dataclass
class ScanResult:
    inventory: dict[str, Any]
    commands: dict[str, Any]


def _command(name: str, command: str, source: str, working_directory: str = ".", confidence: str = "medium") -> dict:
    return {
        "name": name,
        "command": command,
        "workingDirectory": working_directory,
        "source": source,
        "confidence": confidence,
        "verified": False,
    }


def _validate(analysis: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Cross-check LLM analysis against script evidence.

    Produces validation points where LLM claims a stack but scripts
    did not confirm it.
    """
    points: list[dict[str, Any]] = []

    # Java / Maven check
    if _stack_mentions(analysis, _JAVA_KEYWORDS):
        java = evidence.get("java", {})
        if not java.get("detected", False):
            points.append({
                "type": "stack-mismatch",
                "stack": "java",
                "llmClaim": "Java/Maven detected",
                "scriptEvidence": "not detected",
                "resolution": "calibration",
            })

    # Node check
    if _stack_mentions(analysis, _NODE_KEYWORDS):
        node = evidence.get("node", {})
        if not node.get("detected", False):
            points.append({
                "type": "stack-mismatch",
                "stack": "node",
                "llmClaim": "Node/frontend detected",
                "scriptEvidence": "not detected",
                "resolution": "calibration",
            })

    # .NET check
    if _stack_mentions(analysis, _DOTNET_KEYWORDS):
        dotnet = evidence.get("dotnet", {})
        if not dotnet.get("detected", False):
            points.append({
                "type": "stack-mismatch",
                "stack": "dotnet",
                "llmClaim": ".NET detected",
                "scriptEvidence": "not detected",
                "resolution": "calibration",
            })

    return {
        "enabled": analysis.get("enabled", False),
        "points": points,
        "summary": f"{len(points)} validation point(s)" if points else "All LLM claims confirmed by scripts",
    }


def _commands_from_analysis(
    analysis: dict[str, Any],
    evidence: dict[str, Any],
    repo_name: str,
) -> dict[str, Any]:
    """Convert analysis.commandCandidates into command-catalog shape.

    Falls back to evidence-based commands when analysis is disabled or
    has no commandCandidates.
    """
    catalog: dict[str, Any] = {
        "repo": repo_name,
        "commands": {"build": [], "test": [], "run": [], "frontend": [], "docker": []},
    }

    # Try LLM-provided command candidates first
    candidates = analysis.get("commandCandidates", [])
    if analysis.get("enabled") and candidates:
        added_llm_commands = False
        for c, group_category in _iter_command_candidates(candidates):
            command = c.get("command")
            if not command:
                continue
            category = c.get("category", c.get("type", group_category)) or _infer_command_category(command)
            if category == "other":
                category = _infer_command_category(command)
            if category not in catalog["commands"]:
                continue
            catalog["commands"][category].append(_command(
                name=c.get("name", command),
                command=command,
                source=c.get("evidence", ["llm-analysis"])[0] if c.get("evidence") else "llm-analysis",
                working_directory=c.get("workingDirectory", "."),
                confidence=c.get("confidence", "medium"),
            ))
            added_llm_commands = True
        if added_llm_commands:
            return catalog

    # Fallback: evidence-based commands (equivalent to old _build_command_catalog)
    java = evidence.get("java", {})
    node = evidence.get("node", {})
    dotnet = evidence.get("dotnet", {})

    if java.get("detected"):
        catalog["commands"]["build"].append(
            _command("maven-package", "mvn clean package -DskipTests", "pom.xml", confidence="high")
        )
        catalog["commands"]["test"].append(
            _command("maven-test", "mvn test", "pom.xml", confidence="medium")
        )

    for project in node.get("projects", []):
        scripts = project.get("scripts", {})
        if "build" in scripts:
            catalog["commands"]["frontend"].append(
                _command("frontend-build", "npm run build", project["packageFile"], project["path"], "high")
            )
        if "dev" in scripts:
            catalog["commands"]["run"].append(
                _command("frontend-dev", "npm run dev", project["packageFile"], project["path"], "medium")
            )

    if dotnet.get("detected"):
        catalog["commands"]["build"].append(
            _command("dotnet-build", "dotnet build", "*.sln", confidence="high")
        )
        catalog["commands"]["test"].append(
            _command("dotnet-test", "dotnet test", "*.sln", confidence="high")
        )

    return catalog


def _iter_command_candidates(candidates: Any) -> list[tuple[dict[str, Any], str | None]]:
    """Normalize LLM commandCandidates from list or grouped dict shapes."""
    if isinstance(candidates, list):
        return [(c, None) for c in candidates if isinstance(c, dict)]
    if isinstance(candidates, dict):
        normalized: list[tuple[dict[str, Any], str | None]] = []
        for group, value in candidates.items():
            if isinstance(value, dict):
                items = value.get("commands", [])
            else:
                items = value
            if isinstance(items, list):
                normalized.extend((c, str(group)) for c in items if isinstance(c, dict))
        return normalized
    return []


def _infer_command_category(command: str) -> str:
    """Infer command category when LLM omits explicit category/type."""
    normalized = command.lower()
    if " test" in f" {normalized}" or normalized.startswith("pytest"):
        return "test"
    if "docker" in normalized:
        return "docker"
    if "npm run dev" in normalized or "pnpm dev" in normalized or "yarn dev" in normalized or "spring-boot:run" in normalized or normalized.startswith("dotnet run"):
        return "run"
    if "npm run build" in normalized or "pnpm build" in normalized or "yarn build" in normalized:
        return "frontend"
    return "build"


def scan_repository(repo_root: Path, out_dir: Path, llm_caller=None) -> ScanResult:
    """Five-stage scan pipeline.

    1. collect_file_tree  → fileTree
    2. scan_with_llm      → analysis
    3. extract_evidence   → evidence
    4. _validate          → validation
    5. merge into inventory + commands
    """
    repo_root = repo_root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Stage 1: Collect file tree
    file_tree = collect_file_tree(repo_root)

    # Stage 2: LLM analysis (two-round with self-check)
    analysis = scan_with_llm(file_tree, llm_caller)

    # Stage 3: Extract evidence based on analysis
    # When analysis is disabled, run all detectors for full coverage
    if analysis.get("enabled"):
        evidence = extract_evidence(repo_root, analysis)
    else:
        # No LLM — run all detectors unconditionally
        evidence = {
            "java": detect_java_maven(repo_root),
            "node": detect_node_frontend(repo_root),
            "dotnet": detect_dotnet(repo_root),
            "filesystem": scan_filesystem(repo_root),
            "ci": detect_ci_docker(repo_root),
            "codeStructure": detect_shallow_code_structure(repo_root),
            "genericFallback": detect_generic_fallback(repo_root),
        }

    # Stage 4: Validate LLM claims against script evidence
    validation = _validate(analysis, evidence)

    # Stage 5: Merge into inventory + commands
    inventory = {
        "repo": {"name": repo_root.name, "path": str(repo_root)},
        "fileTree": file_tree,
        "analysis": analysis,
        "evidence": evidence,
        "validation": validation,
    }

    commands = _commands_from_analysis(analysis, evidence, repo_root.name)

    return ScanResult(inventory=inventory, commands=commands)


def write_scan_outputs(result: ScanResult, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "project-inventory.json").write_text(
        json.dumps(result.inventory, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "command-catalog.yaml").write_text(
        yaml.safe_dump(result.commands, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    (out_dir / "scanner-report.md").write_text(
        render_scanner_report(result.inventory, result.commands), encoding="utf-8"
    )
