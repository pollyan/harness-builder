from __future__ import annotations

from pathlib import Path

from harness_builder_agent.schemas.scan import EvidenceBucketCoverage, EvidenceBundle, EvidenceCoverage, EvidenceFile

IGNORED_DIRS = {".git", ".ai", ".venv", "node_modules", "target", "bin", "obj", "dist", "build", "__pycache__"}
KEY_FILE_NAMES = {"pom.xml", "package.json", "global.json"}
CONFIG_NAMES = {".env.example"}
CONFIG_SUFFIXES = (".yml", ".yaml", ".json", ".config")
SOURCE_SUFFIXES = {".java", ".cs", ".js", ".ts", ".tsx", ".vue", ".py"}


def collect_evidence(repo: Path, max_summary_chars: int = 600, max_source_samples: int = 20) -> EvidenceBundle:
    root = repo.resolve()
    files = _walk_files(root)

    buckets: dict[str, list[Path]] = {}
    for path in files:
        buckets.setdefault(_bucket_for(path, root), []).append(path)

    selected_by_bucket = _select_by_bucket(buckets, max_source_samples)
    selected_paths = [path for bucket in sorted(selected_by_bucket) for path in selected_by_bucket[bucket]]

    evidence_files = [_evidence_file(path, root, "file", 0) for path in files]
    selected_evidence = [_evidence_for_bucket(path, root, max_summary_chars, _bucket_for(path, root)) for path in selected_paths]

    key_files = [item for item in selected_evidence if item.bucket == "build"]
    config_files = [item for item in selected_evidence if item.bucket == "config"]
    ci_files = [item for item in selected_evidence if item.bucket == "ci"]
    documents = [item for item in selected_evidence if item.bucket == "document"]
    source_samples = [item for item in selected_evidence if item.bucket and item.bucket.startswith("source:")]
    test_files = [item for item in selected_evidence if item.bucket == "test"]
    api_entrypoints = [item for item in selected_evidence if item.bucket == "api_entrypoint"]
    risk_files = [item for item in selected_evidence if item.bucket == "risk"]
    priority_files = [item for item in selected_evidence if item.priority in {"critical", "high"}]

    grouped = _unique_evidence(
        key_files
        + config_files
        + ci_files
        + documents
        + source_samples
        + priority_files
        + test_files
        + api_entrypoints
        + risk_files
    )
    return EvidenceBundle(
        repo_name=root.name,
        root_path=str(root),
        files=evidence_files,
        key_files=key_files,
        config_files=config_files,
        ci_files=ci_files,
        documents=documents,
        source_samples=source_samples,
        priority_files=priority_files,
        test_files=test_files,
        api_entrypoints=api_entrypoints,
        risk_files=risk_files,
        coverage=_coverage(files, root, buckets, selected_by_bucket),
        extension_counts=_extension_counts(files),
        detected_file_count=len(files),
        truncations=[
            {"path": item.path, "summary_chars": len(item.summary or "")}
            for item in grouped
            if item.truncated
        ],
    )


def expand_evidence_with_requested_paths(
    repo: Path,
    evidence: EvidenceBundle,
    requested_paths: list[str],
    *,
    max_summary_chars: int = 1200,
) -> EvidenceBundle:
    root = repo.resolve()
    known_paths = {item.path for item in evidence.files}
    requested: list[EvidenceFile] = []
    seen: set[str] = set()
    for relative_path in requested_paths:
        if relative_path in seen:
            continue
        seen.add(relative_path)
        if relative_path not in known_paths:
            raise ValueError(f"unknown evidence path requested by LLM planner: {relative_path}")
        path = (root / relative_path).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"LLM planner requested path outside repository: {relative_path}") from exc
        requested.append(
            _evidence_file(
                path,
                root,
                "llm_requested",
                max_summary_chars,
                bucket="llm_requested",
                priority="high",
                reason="LLM evidence planner requested this file.",
            )
        )
    return evidence.model_copy(update={"llm_requested_files": requested})


def _walk_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if any(part in IGNORED_DIRS for part in rel_parts):
            continue
        if path.is_file():
            found.append(path)
    return sorted(found)


def _evidence_file(
    path: Path,
    root: Path,
    kind: str,
    max_summary_chars: int,
    *,
    bucket: str | None = None,
    priority: str = "medium",
    reason: str | None = None,
) -> EvidenceFile:
    summary = _read_summary(path, max_summary_chars)
    return EvidenceFile(
        path=_relative(path, root),
        kind=kind,
        size_bytes=path.stat().st_size,
        summary=summary,
        truncated=summary is not None and path.stat().st_size > len(summary.encode("utf-8")),
        priority=priority,
        reason=reason,
        bucket=bucket,
    )


def _evidence_for_bucket(path: Path, root: Path, max_summary_chars: int, bucket: str) -> EvidenceFile:
    return _evidence_file(
        path,
        root,
        _kind_for_bucket(bucket),
        max_summary_chars,
        bucket=bucket,
        priority=_priority_for(bucket),
        reason=_reason_for(path, root, bucket),
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


def _bucket_for(path: Path, root: Path) -> str:
    rel = _relative(path, root).lower()
    name = path.name.lower()
    suffix = path.suffix.lower()
    if _is_key_file(path):
        return "build"
    if _is_config_file(path):
        return "config"
    if ".github/workflows" in rel:
        return "ci"
    if _is_document(path):
        return "document"
    if _is_test_file(path):
        return "test"
    if _is_api_entrypoint(path):
        return "api_entrypoint"
    if _is_risk_file(path):
        return "risk"
    if suffix in SOURCE_SUFFIXES:
        return f"source:{suffix}"
    return "other"


def _priority_for(bucket: str) -> str:
    if bucket in {"build", "ci", "api_entrypoint", "config"}:
        return "critical"
    if bucket in {"risk", "test"}:
        return "high"
    if bucket == "document" or bucket.startswith("source:"):
        return "medium"
    return "low"


def _kind_for_bucket(bucket: str) -> str:
    if bucket.startswith("source:"):
        return "source"
    return bucket


def _reason_for(path: Path, root: Path, bucket: str) -> str:
    rel = _relative(path, root)
    if bucket == "build":
        return "Build or package manifest."
    if bucket == "config":
        return "Configuration file."
    if bucket == "ci":
        return "CI workflow definition."
    if bucket == "document":
        return "Repository documentation."
    if bucket == "test":
        return "Test or specification file."
    if bucket == "api_entrypoint":
        return "API or application entrypoint signal."
    if bucket == "risk":
        return "Security, auth, database, or migration risk area."
    if bucket.startswith("source:"):
        return f"Representative {path.suffix.lower() or 'source'} source sample."
    return f"Collected file evidence for {rel}."


def _select_by_bucket(buckets: dict[str, list[Path]], max_source_samples: int) -> dict[str, list[Path]]:
    selected: dict[str, list[Path]] = {}
    for bucket, paths in buckets.items():
        ordered = sorted(paths)
        if bucket.startswith("source:"):
            selected[bucket] = ordered[:max_source_samples]
        elif bucket == "other":
            selected[bucket] = []
        else:
            selected[bucket] = ordered
    return selected


def _coverage(
    files: list[Path],
    root: Path,
    buckets: dict[str, list[Path]],
    selected_by_bucket: dict[str, list[Path]],
) -> EvidenceCoverage:
    bucket_coverage: list[EvidenceBucketCoverage] = []
    warnings: list[dict[str, str]] = []
    selected_count = 0
    for bucket in sorted(buckets):
        selected = [_relative(path, root) for path in selected_by_bucket.get(bucket, [])]
        total = len(buckets[bucket])
        skipped = max(total - len(selected), 0)
        selected_count += len(selected)
        bucket_coverage.append(
            EvidenceBucketCoverage(
                bucket=bucket,
                total_count=total,
                selected_count=len(selected),
                skipped_count=skipped,
                selected_paths=selected,
            )
        )
        if skipped and bucket.startswith("source:"):
            warnings.append(
                {
                    "code": "source_sampling_truncated",
                    "bucket": bucket,
                    "message": f"{bucket} skipped {skipped} files",
                }
            )
    return EvidenceCoverage(
        detected_file_count=len(files),
        selected_evidence_count=selected_count,
        bucket_coverage=bucket_coverage,
        warnings=warnings,
    )


def _unique_evidence(items: list[EvidenceFile]) -> list[EvidenceFile]:
    seen: set[str] = set()
    unique: list[EvidenceFile] = []
    for item in items:
        if item.path in seen:
            continue
        seen.add(item.path)
        unique.append(item)
    return unique


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


def _is_test_file(path: Path) -> bool:
    rel = path.as_posix().lower()
    name = path.name.lower()
    return (
        any(token in rel for token in ("/test/", "/tests/", "tests-", "/spec/", "/quality/checks/"))
        or "test" in name
        or "spec" in name
    )


def _is_api_entrypoint(path: Path) -> bool:
    name = path.name.lower()
    rel = path.as_posix().lower()
    return (
        any(token in name for token in ("controller", "endpoint", "router", "route"))
        or name in {"program.cs", "application.java"}
        or "api" in rel
        and path.suffix.lower() in SOURCE_SUFFIXES
    )


def _is_risk_file(path: Path) -> bool:
    rel = path.as_posix().lower()
    return any(token in rel for token in ("security", "auth", "database", "migration", "migrations", ".sql"))


def _extension_counts(files: list[Path]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in files:
        suffix = path.suffix.lower() or "<none>"
        counts[suffix] = counts.get(suffix, 0) + 1
    return dict(sorted(counts.items()))
