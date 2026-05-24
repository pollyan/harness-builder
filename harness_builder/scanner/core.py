from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from harness_builder.scanner.detectors.ci_docker import detect_ci_docker
from harness_builder.scanner.detectors.dotnet import detect_dotnet
from harness_builder.scanner.detectors.filesystem import scan_filesystem
from harness_builder.scanner.detectors.java_maven import detect_java_maven
from harness_builder.scanner.detectors.node_frontend import detect_node_frontend
from harness_builder.scanner.detectors.shallow_code import detect_shallow_code_structure


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


def _build_command_catalog(repo_name: str, java: dict, node: dict, dotnet: dict) -> dict:
    catalog = {"repo": repo_name, "commands": {"build": [], "test": [], "run": [], "frontend": [], "docker": []}}
    if java.get("detected"):
        catalog["commands"]["build"].append(_command("maven-package", "mvn clean package -DskipTests", "pom.xml", confidence="high"))
        catalog["commands"]["test"].append(_command("maven-test", "mvn test", "pom.xml", confidence="medium"))
    for project in node.get("projects", []):
        scripts = project.get("scripts", {})
        if "build" in scripts:
            catalog["commands"]["frontend"].append(_command("frontend-build", "npm run build", project["packageFile"], project["path"], "high"))
        if "dev" in scripts:
            catalog["commands"]["run"].append(_command("frontend-dev", "npm run dev", project["packageFile"], project["path"], "medium"))
    if dotnet.get("detected"):
        catalog["commands"]["build"].append(_command("dotnet-build", "dotnet build", "*.sln", confidence="high"))
        catalog["commands"]["test"].append(_command("dotnet-test", "dotnet test", "*.sln", confidence="high"))
    return catalog


def scan_repository(repo_root: Path, out_dir: Path) -> ScanResult:
    repo_root = repo_root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    fs = scan_filesystem(repo_root)
    java = detect_java_maven(repo_root)
    node = detect_node_frontend(repo_root)
    dotnet = detect_dotnet(repo_root)
    ci = detect_ci_docker(repo_root)
    shallow = detect_shallow_code_structure(repo_root)
    inventory = {
        "repo": {"name": repo_root.name, "path": str(repo_root)},
        "structure": fs,
        "stackExtensions": {"java": java, "node": node, "dotnet": dotnet},
        "ci": ci,
        "codeStructure": shallow,
    }
    commands = _build_command_catalog(repo_root.name, java, node, dotnet)
    return ScanResult(inventory=inventory, commands=commands)
