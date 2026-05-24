from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def _strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _project_references(csproj: Path, repo_root: Path) -> list[str]:
    try:
        root = ET.parse(csproj).getroot()
    except ET.ParseError:
        return []
    refs: list[str] = []
    for node in root.iter():
        if _strip_namespace(node.tag) == "ProjectReference" and "Include" in node.attrib:
            ref = (csproj.parent / node.attrib["Include"]).resolve()
            try:
                refs.append(ref.relative_to(repo_root).as_posix())
            except ValueError:
                refs.append(node.attrib["Include"])
    return refs


def detect_dotnet(repo_root: Path) -> dict:
    solutions = sorted(p.relative_to(repo_root).as_posix() for p in repo_root.rglob("*.sln"))
    csprojs = sorted(repo_root.rglob("*.csproj"))
    projects: list[dict] = []
    test_projects: list[str] = []
    for csproj in csprojs:
        rel = csproj.relative_to(repo_root).as_posix()
        is_test = "test" in rel.lower() or csproj.name.lower().endswith("tests.csproj")
        projects.append({"path": rel, "name": csproj.stem, "isTest": is_test, "projectReferences": _project_references(csproj, repo_root)})
        if is_test:
            test_projects.append(rel)
    global_json = repo_root / "global.json"
    return {
        "detected": bool(solutions or projects),
        "solutions": solutions,
        "projects": projects,
        "testProjects": sorted(test_projects),
        "globalJson": "global.json" if global_json.exists() else None,
    }
