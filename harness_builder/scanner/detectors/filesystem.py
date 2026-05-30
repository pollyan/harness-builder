from __future__ import annotations

from collections import Counter
from pathlib import Path

IGNORED_DIRS = {".git", ".harness", "node_modules", "target", "bin", "obj", ".venv", "__pycache__"}
KEY_FILE_NAMES = {
    "README.md",
    "CONTRIBUTING.md",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "package.json",
    "global.json",
    "docker-compose.yml",
    "Dockerfile",
}


def scan_filesystem(repo_root: Path) -> dict:
    top_dirs = sorted(p.name for p in repo_root.iterdir() if p.is_dir() and p.name not in IGNORED_DIRS)
    key_files: list[str] = []
    ext_counter: Counter[str] = Counter()
    total = 0

    for path in repo_root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        rel = path.relative_to(repo_root).as_posix()
        if path.is_file():
            total += 1
            ext_counter[path.suffix or "<none>"] += 1
            if path.name in KEY_FILE_NAMES or path.name.endswith(".sln") or path.name.endswith(".csproj"):
                key_files.append(rel)

    return {
        "topLevelDirectories": top_dirs,
        "keyFiles": sorted(key_files),
        "fileCounts": {
            "total": total,
            "byExtension": dict(sorted(ext_counter.items())),
        },
    }
