from __future__ import annotations

import json
from pathlib import Path

IGNORED_PARTS = {"node_modules", ".git", ".harness"}


def detect_node_frontend(repo_root: Path) -> dict:
    projects: list[dict] = []
    for package_json in sorted(repo_root.rglob("package.json")):
        if any(part in IGNORED_PARTS for part in package_json.parts):
            continue
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        project_dir = package_json.parent
        vue_count = sum(1 for _ in project_dir.rglob("*.vue"))
        projects.append(
            {
                "path": project_dir.relative_to(repo_root).as_posix() or ".",
                "packageFile": package_json.relative_to(repo_root).as_posix(),
                "scripts": data.get("scripts", {}),
                "dependencies": sorted((data.get("dependencies") or {}).keys()),
                "devDependencies": sorted((data.get("devDependencies") or {}).keys()),
                "vueFileCount": vue_count,
            }
        )
    return {"detected": bool(projects), "projects": projects}
