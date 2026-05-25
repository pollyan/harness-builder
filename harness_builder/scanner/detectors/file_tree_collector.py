"""File tree collector for Scanner v2.

Recursively traverses a repo and outputs a structured, JSON-serializable manifest.
Pure collection, zero judgment. This is the only input to the LLM.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Directories to always skip
EXCLUDED_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        "target",
        "__pycache__",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".venv",
        "venv",
        "dist",
        "build",
        ".idea",
        ".vscode",
    }
)


def collect_file_tree(
    repo_root: Path,
    max_depth: int = 6,
) -> dict[str, Any]:
    """Collect a structured file tree manifest from *repo_root*.

    Returns a JSON-serializable dict with:
      - root: POSIX path of the repo root
      - files: list of file records
      - directories: list of directory records

    Each file record: {path, name, extension, sizeBytes}
    Each directory record: {path, name, fileCount, subdirectoryCount}
    """
    repo_root = Path(repo_root)
    files: list[dict[str, Any]] = []
    directories: list[dict[str, Any]] = []

    _walk(repo_root, repo_root, files, directories, max_depth, depth=0)

    return {
        "root": repo_root.as_posix(),
        "files": files,
        "directories": directories,
    }


def _walk(
    root: Path,
    base: Path,
    files: list[dict[str, Any]],
    directories: list[dict[str, Any]],
    max_depth: int,
    depth: int,
) -> None:
    """Recursively walk *root*, collecting file and directory records."""
    if depth > max_depth:
        return

    try:
        entries = sorted(os.scandir(root), key=lambda e: e.name)
    except PermissionError:
        return

    child_files: list[os.DirEntry[Any]] = []  # type: ignore[type-arg]
    child_dirs: list[os.DirEntry[Any]] = []  # type: ignore[type-arg]

    for entry in entries:
        name = entry.name

        # Skip excluded directories
        if entry.is_dir(follow_symlinks=False) and name in EXCLUDED_DIRS:
            continue

        if entry.is_file(follow_symlinks=False):
            child_files.append(entry)
        elif entry.is_dir(follow_symlinks=False):
            child_dirs.append(entry)

    # Record this directory (unless it's the repo root itself at depth 0,
    # we still need to descend into it)
    if depth > 0:
        rel = root.relative_to(base).as_posix()
        directories.append(
            {
                "path": rel,
                "name": root.name,
                "fileCount": len(child_files),
                "subdirectoryCount": len(child_dirs),
            }
        )

    # Record files
    for entry in child_files:
        name = entry.name
        rel = root.joinpath(name).relative_to(base).as_posix()
        suffix = Path(name).suffix
        try:
            size = entry.stat(follow_symlinks=False).st_size
        except OSError:
            size = 0
        files.append(
            {
                "path": rel,
                "name": name,
                "extension": suffix,
                "sizeBytes": size,
            }
        )

    # Recurse into subdirectories
    for entry in child_dirs:
        _walk(
            Path(entry.path),
            base,
            files,
            directories,
            max_depth,
            depth + 1,
        )
