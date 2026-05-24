from __future__ import annotations

from pathlib import Path

IGNORED_PARTS = {".git", ".harness", "node_modules", "target", "bin", "obj"}


def detect_shallow_code_structure(repo_root: Path) -> dict:
    result = {"controllers": [], "services": [], "entitiesOrModels": [], "tests": [], "frontendComponents": []}
    for path in repo_root.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        rel = path.relative_to(repo_root).as_posix()
        name = path.name.lower()
        if name.endswith(("controller.java", "controller.cs")) or "/controllers/" in rel.lower():
            result["controllers"].append(rel)
        if name.endswith(("service.java", "service.cs")) or "/services/" in rel.lower():
            result["services"].append(rel)
        if name.endswith(("entity.java", "model.java", "model.cs")) or "/models/" in rel.lower():
            result["entitiesOrModels"].append(rel)
        if "test" in rel.lower() and path.suffix in {".java", ".cs", ".js", ".ts"}:
            result["tests"].append(rel)
        if path.suffix in {".vue", ".tsx", ".jsx"}:
            result["frontendComponents"].append(rel)
    return {key: sorted(value) for key, value in result.items()}
