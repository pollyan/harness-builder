from __future__ import annotations

from pathlib import Path

from harness_builder_agent.schemas.command_catalog import CommandCatalog, CommandDefinition
from harness_builder_agent.schemas.project_inventory import ProjectInventory

IGNORED_DIRS = {".git", ".ai", ".venv", "node_modules", "target", "bin", "obj", "dist", "build", "__pycache__"}


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def _detect_primary_stack(files: list[Path]) -> tuple[str, list[str]]:
    names = {path.name for path in files}
    suffixes = {path.suffix.lower() for path in files}

    if "pom.xml" in names:
        stacks = ["java", "maven"]
        if any("Controller.java" in path.name for path in files):
            stacks.append("spring-boot")
        if "package.json" in names:
            stacks.append("frontend")
        return "java-spring", stacks

    if any(path.suffix == ".sln" for path in files) or ".csproj" in suffixes:
        stacks = ["dotnet"]
        if any(".Web" in path.name or "Api" in path.name or "API" in path.name for path in files):
            stacks.append("aspnet-core")
        return "dotnet-aspnet", stacks

    if "package.json" in names:
        return "node", ["node"]

    return "unknown", []


def _detect_modules(root: Path, files: list[Path], primary_stack: str) -> list[dict[str, str]]:
    modules: list[dict[str, str]] = []
    if primary_stack == "java-spring":
        modules.append({"name": root.name, "path": ".", "kind": "backend"})
        if (root / "src" / "test").exists():
            modules.append({"name": f"{root.name}-tests", "path": "src/test", "kind": "test"})
        if (root / "package.json").exists():
            modules.append({"name": "frontend", "path": ".", "kind": "frontend"})
    elif primary_stack == "dotnet-aspnet":
        for csproj in sorted(path for path in files if path.suffix == ".csproj"):
            rel = _relative(csproj.parent, root) or "."
            kind = "test" if "test" in csproj.name.lower() or "test" in rel.lower() else "backend"
            modules.append({"name": csproj.stem, "path": rel, "kind": kind})
    else:
        modules.append({"name": root.name, "path": ".", "kind": "unknown"})
    return modules


def _detect_evidence(root: Path, files: list[Path]) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for path in files:
        rel = _relative(path, root)
        if path.name == "pom.xml":
            evidence.append({"path": rel, "reason": "maven build file"})
        elif path.name == "package.json":
            evidence.append({"path": rel, "reason": "node package manifest"})
        elif path.suffix == ".sln":
            evidence.append({"path": rel, "reason": "dotnet solution file"})
        elif path.suffix == ".csproj":
            evidence.append({"path": rel, "reason": "dotnet project file"})
    return evidence


def _detect_commands(files: list[Path], primary_stack: str) -> CommandCatalog:
    commands: list[CommandDefinition] = []
    if primary_stack == "java-spring":
        commands.extend(
            [
                CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml"),
                CommandDefinition(id="build", command="mvn package", type="build", gate="hard", source="pom.xml"),
            ]
        )
        if any(path.name == "package.json" for path in files):
            commands.append(CommandDefinition(id="frontend_test", command="npm test", type="test", gate="soft", source="package.json"))
    elif primary_stack == "dotnet-aspnet":
        commands.extend(
            [
                CommandDefinition(id="unit_test", command="dotnet test", type="test", gate="hard", source="*.sln/*.csproj"),
                CommandDefinition(id="build", command="dotnet build", type="build", gate="hard", source="*.sln/*.csproj"),
            ]
        )
    return CommandCatalog(commands=commands)


def scan_repository(repo: Path) -> tuple[ProjectInventory, CommandCatalog]:
    root = repo.resolve()
    files = _walk_files(root)
    primary_stack, stacks = _detect_primary_stack(files)
    inventory = ProjectInventory(
        repo_name=root.name,
        root_path=str(root),
        primary_stack=primary_stack,
        stacks=stacks,
        modules=_detect_modules(root, files, primary_stack),
        evidence=_detect_evidence(root, files),
        documents=[{"path": _relative(path, root), "kind": "readme"} for path in files if path.name.lower().startswith("readme")],
        configs=[{"path": _relative(path, root), "kind": "config"} for path in files if path.name in {"application.yml", "appsettings.json", ".env.example"}],
        ci_files=[{"path": _relative(path, root), "kind": "ci"} for path in files if ".github/workflows" in _relative(path, root)],
        stack_extensions={"detected_file_count": len(files)},
    )
    return inventory, _detect_commands(files, primary_stack)
