from __future__ import annotations

from pathlib import Path

from harness_builder_agent.schemas.scan import EvidenceBundle, EvidenceFile

IGNORED_DIRS = {".git", ".ai", ".venv", "node_modules", "target", "bin", "obj", "dist", "build", "__pycache__"}
KEY_FILE_NAMES = {"pom.xml", "package.json", "global.json"}
CONFIG_NAMES = {".env.example"}
CONFIG_SUFFIXES = (".yml", ".yaml", ".json", ".config")
SOURCE_SUFFIXES = {".java", ".cs", ".js", ".ts", ".tsx", ".vue", ".py"}


def collect_evidence(repo: Path, max_summary_chars: int = 600, max_source_samples: int = 20) -> EvidenceBundle:
    root = repo.resolve()
    files = _walk_files(root)
    evidence_files = [_evidence_file(path, root, "file", max_summary_chars) for path in files]

    key_files = [_evidence_file(path, root, "build", max_summary_chars) for path in files if _is_key_file(path)]
    config_files = [_evidence_file(path, root, "config", max_summary_chars) for path in files if _is_config_file(path)]
    ci_files = [_evidence_file(path, root, "ci", max_summary_chars) for path in files if ".github/workflows" in _relative(path, root)]
    documents = [_evidence_file(path, root, "document", max_summary_chars) for path in files if _is_document(path)]
    source_samples = [
        _evidence_file(path, root, "source", max_summary_chars)
        for path in files
        if path.suffix.lower() in SOURCE_SUFFIXES
    ][:max_source_samples]

    grouped = key_files + config_files + ci_files + documents + source_samples
    return EvidenceBundle(
        repo_name=root.name,
        root_path=str(root),
        files=evidence_files,
        key_files=key_files,
        config_files=config_files,
        ci_files=ci_files,
        documents=documents,
        source_samples=source_samples,
        extension_counts=_extension_counts(files),
        detected_file_count=len(files),
        truncations=[
            {"path": item.path, "summary_chars": len(item.summary or "")}
            for item in grouped
            if item.truncated
        ],
    )


def _walk_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if any(part in IGNORED_DIRS for part in rel_parts):
            continue
        if path.is_file():
            found.append(path)
    return sorted(found)


def _evidence_file(path: Path, root: Path, kind: str, max_summary_chars: int) -> EvidenceFile:
    summary = _read_summary(path, max_summary_chars)
    return EvidenceFile(
        path=_relative(path, root),
        kind=kind,
        size_bytes=path.stat().st_size,
        summary=summary,
        truncated=summary is not None and path.stat().st_size > len(summary.encode("utf-8")),
    )


def _read_summary(path: Path, max_summary_chars: int) -> str | None:
    if max_summary_chars <= 0:
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    return text[:max_summary_chars]


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_key_file(path: Path) -> bool:
    return path.name in KEY_FILE_NAMES or path.suffix in {".sln", ".csproj"}


def _is_config_file(path: Path) -> bool:
    name = path.name.lower()
    return (
        path.name in CONFIG_NAMES
        or name.startswith("application")
        or name.startswith("appsettings")
        or name == "docker-compose.yml"
        or name == "docker-compose.yaml"
        or path.suffix.lower() in CONFIG_SUFFIXES and "config" in name
    )


def _is_document(path: Path) -> bool:
    return path.name.lower().startswith("readme") or "docs" in path.parts


def _extension_counts(files: list[Path]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in files:
        suffix = path.suffix.lower() or "<none>"
        counts[suffix] = counts.get(suffix, 0) + 1
    return dict(sorted(counts.items()))
