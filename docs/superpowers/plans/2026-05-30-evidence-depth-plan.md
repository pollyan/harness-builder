# Evidence Depth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve repository evidence collection so large repositories produce stratified, prioritized, auditable evidence and scan coverage metadata.

**Architecture:** Extend scan schemas first, then change `evidence_collector` to build bucketed evidence and coverage without making final stack decisions. Feed coverage into the LLM prompt and reconcile it into `scan-metadata.yaml`, keeping existing `init` behavior compatible.

**Tech Stack:** Python 3.11+, Pydantic, pytest, PyYAML.

---

## File Structure

Modify:

- `src/harness_builder_agent/schemas/scan.py`: add evidence priority, bucket and coverage models.
- `src/harness_builder_agent/tools/evidence_collector.py`: implement stratified collection and coverage.
- `src/harness_builder_agent/tools/llm_scan_analyzer.py`: explain coverage and prioritized evidence in the prompt.
- `src/harness_builder_agent/tools/scan_reconciler.py`: add coverage to scan metadata and warnings.
- `tests/unit/test_evidence_collector.py`: add large/messy repo evidence tests.
- `tests/unit/test_llm_scan_analyzer.py`: assert prompt includes coverage guidance.
- `tests/unit/test_scan_reconciler.py`: assert metadata persists coverage.
- `tests/unit/test_schema_contracts.py`: assert scan schemas validate new fields.
- `docs/todos/evidence-depth-for-large-repositories.md`: mark implemented.

Do not change:

- LLM proposal schema output shape.
- CLI command signatures.
- DeepSeek fallback behavior.

---

### Task 1: Scan Schema Coverage Contract

**Files:**
- Modify: `src/harness_builder_agent/schemas/scan.py`
- Modify: `tests/unit/test_schema_contracts.py`

- [ ] **Step 1: Write failing schema contract test**

Add this import in `tests/unit/test_schema_contracts.py`:

```python
from harness_builder_agent.schemas.scan import EvidenceBundle, EvidenceBucketCoverage, EvidenceCoverage, EvidenceFile, ScanMetadata
```

Add this test:

```python
def test_evidence_bundle_records_priority_buckets_and_coverage():
    bundle = EvidenceBundle(
        repo_name="large-repo",
        root_path="/tmp/large-repo",
        files=[EvidenceFile(path="pom.xml", kind="build", priority="critical", reason="Maven build file", bucket="build")],
        priority_files=[EvidenceFile(path="pom.xml", kind="build", priority="critical", reason="Maven build file", bucket="build")],
        test_files=[EvidenceFile(path="quality/checks/UserFlowSpec.cs", kind="test", priority="high", bucket="test")],
        api_entrypoints=[EvidenceFile(path="src/api/UserController.java", kind="api_entrypoint", priority="critical", bucket="api_entrypoint")],
        risk_files=[EvidenceFile(path="src/security/AuthConfig.java", kind="risk", priority="high", bucket="risk")],
        coverage=EvidenceCoverage(
            detected_file_count=120,
            selected_evidence_count=4,
            bucket_coverage=[
                EvidenceBucketCoverage(
                    bucket="source:.java",
                    total_count=80,
                    selected_count=2,
                    skipped_count=78,
                    selected_paths=["src/api/UserController.java"],
                )
            ],
            warnings=[{"code": "source_sampling_truncated", "message": "source:.java had skipped files"}],
        ),
    )

    payload = bundle.model_dump(mode="json")

    assert payload["files"][0]["priority"] == "critical"
    assert payload["priority_files"][0]["bucket"] == "build"
    assert payload["coverage"]["bucket_coverage"][0]["skipped_count"] == 78
    assert payload["coverage"]["warnings"][0]["code"] == "source_sampling_truncated"
```

Add this test:

```python
def test_scan_metadata_accepts_evidence_coverage():
    metadata = ScanMetadata(
        prompt_version="test",
        evidence_file_count=120,
        coverage={
            "schema_version": "1.0",
            "detected_file_count": 120,
            "selected_evidence_count": 10,
            "bucket_coverage": [
                {
                    "bucket": "test",
                    "total_count": 3,
                    "selected_count": 2,
                    "skipped_count": 1,
                    "selected_paths": ["quality/checks/UserFlowSpec.cs"],
                }
            ],
            "warnings": [],
        },
    )

    assert metadata.coverage["selected_evidence_count"] == 10
```

- [ ] **Step 2: Verify test fails**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_evidence_bundle_records_priority_buckets_and_coverage tests/unit/test_schema_contracts.py::test_scan_metadata_accepts_evidence_coverage -q
```

Expected: fail because `EvidenceBucketCoverage`, `EvidenceCoverage`, and `ScanMetadata.coverage` do not exist.

- [ ] **Step 3: Implement schema fields**

In `src/harness_builder_agent/schemas/scan.py`, add:

```python
EvidencePriority = Literal["critical", "high", "medium", "low"]


class EvidenceBucketCoverage(BaseModel):
    bucket: str
    total_count: int
    selected_count: int
    skipped_count: int
    selected_paths: list[str] = Field(default_factory=list)


class EvidenceCoverage(BaseModel):
    schema_version: str = "1.0"
    detected_file_count: int
    selected_evidence_count: int
    bucket_coverage: list[EvidenceBucketCoverage] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
```

Extend `EvidenceFile`:

```python
    priority: EvidencePriority = "medium"
    reason: str | None = None
    bucket: str | None = None
```

Extend `EvidenceBundle`:

```python
    priority_files: list[EvidenceFile] = Field(default_factory=list)
    test_files: list[EvidenceFile] = Field(default_factory=list)
    api_entrypoints: list[EvidenceFile] = Field(default_factory=list)
    risk_files: list[EvidenceFile] = Field(default_factory=list)
    coverage: EvidenceCoverage | None = None
```

Extend `ScanMetadata`:

```python
    coverage: dict[str, Any] | None = None
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py -q
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/schemas/scan.py tests/unit/test_schema_contracts.py
git commit -m "feat: add evidence coverage schema"
```

---

### Task 2: Stratified Evidence Collector

**Files:**
- Modify: `src/harness_builder_agent/tools/evidence_collector.py`
- Modify: `tests/unit/test_evidence_collector.py`

- [ ] **Step 1: Write failing large repository tests**

Add helper:

```python
def _write(path: Path, content: str = "content") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
```

Add test:

```python
def test_collect_evidence_uses_stratified_sampling_for_large_messy_repo(tmp_path: Path):
    _write(tmp_path / "pom.xml", "<project><artifactId>root</artifactId></project>")
    _write(tmp_path / "src/api/UserController.java", "@RestController class UserController {}")
    _write(tmp_path / "src/security/AuthConfig.java", "class AuthConfig {}")
    _write(tmp_path / "quality/checks/UserFlowSpec.cs", "public class UserFlowSpec {}")
    _write(tmp_path / ".github/workflows/build.yml", "jobs: {}")
    _write(tmp_path / "appsettings.Production.json", "{}")
    for index in range(40):
        _write(tmp_path / "aaa" / f"Generated{index:02d}.java", f"class Generated{index:02d} {{}}")

    bundle = collect_evidence(tmp_path, max_source_samples=5)

    assert any(item.path == "pom.xml" for item in bundle.priority_files)
    assert any(item.path == "src/api/UserController.java" for item in bundle.api_entrypoints)
    assert any(item.path == "quality/checks/UserFlowSpec.cs" for item in bundle.test_files)
    assert any(item.path == "src/security/AuthConfig.java" for item in bundle.risk_files)
    assert any(item.path == ".github/workflows/build.yml" for item in bundle.ci_files)
    assert any(item.path == "appsettings.Production.json" for item in bundle.config_files)
    assert bundle.coverage is not None
    java_bucket = next(item for item in bundle.coverage.bucket_coverage if item.bucket == "source:.java")
    assert java_bucket.total_count >= 40
    assert java_bucket.skipped_count > 0
```

Add test:

```python
def test_collect_evidence_marks_priority_reason_and_bucket(tmp_path: Path):
    _write(tmp_path / "src" / "Program.cs", "var builder = WebApplication.CreateBuilder(args);")
    _write(tmp_path / "tests-weird" / "CheckoutSpec.cs", "public class CheckoutSpec {}")

    bundle = collect_evidence(tmp_path)

    program = next(item for item in bundle.api_entrypoints if item.path == "src/Program.cs")
    spec = next(item for item in bundle.test_files if item.path == "tests-weird/CheckoutSpec.cs")
    assert program.priority == "critical"
    assert program.bucket == "api_entrypoint"
    assert program.reason
    assert spec.priority == "high"
    assert spec.bucket == "test"
```

- [ ] **Step 2: Verify tests fail**

```bash
.venv/bin/python -m pytest tests/unit/test_evidence_collector.py -q
```

Expected: fail because new fields/lists are empty.

- [ ] **Step 3: Implement bucket classification**

In `evidence_collector.py`, add helpers:

```python
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
```

Add `_priority_for(bucket: str) -> str`:

```python
def _priority_for(bucket: str) -> str:
    if bucket in {"build", "ci", "api_entrypoint", "config"}:
        return "critical"
    if bucket in {"risk", "test"}:
        return "high"
    if bucket == "document" or bucket.startswith("source:"):
        return "medium"
    return "low"
```

Add detectors:

```python
def _is_test_file(path: Path) -> bool:
    rel = path.as_posix().lower()
    name = path.name.lower()
    return any(token in rel for token in ("/test/", "/tests/", "tests-", "/spec/", "/quality/checks/")) or "test" in name or "spec" in name


def _is_api_entrypoint(path: Path) -> bool:
    name = path.name.lower()
    rel = path.as_posix().lower()
    return any(token in name for token in ("controller", "endpoint", "router", "route")) or name in {"program.cs", "application.java"} or "api" in rel and path.suffix.lower() in SOURCE_SUFFIXES


def _is_risk_file(path: Path) -> bool:
    rel = path.as_posix().lower()
    return any(token in rel for token in ("security", "auth", "database", "migration", "migrations", ".sql"))
```

- [ ] **Step 4: Implement stratified selection and coverage**

Replace the old `source_samples = [...][:max_source_samples]` logic with bucket-based selection:

```python
buckets: dict[str, list[Path]] = {}
for path in files:
    buckets.setdefault(_bucket_for(path, root), []).append(path)

selected_by_bucket = _select_by_bucket(buckets, max_source_samples)
```

Implement:

```python
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
```

Build category lists from selected paths and all critical/high paths. Use `_evidence_file(path, root, kind, max_summary_chars, bucket=bucket, priority=priority, reason=reason)`.

Add coverage:

```python
def _coverage(files: list[Path], buckets: dict[str, list[Path]], selected_by_bucket: dict[str, list[Path]]) -> EvidenceCoverage:
    bucket_coverage = []
    warnings = []
    selected_count = 0
    for bucket in sorted(buckets):
        selected = [_relative(path, root) for path in selected_by_bucket.get(bucket, [])]
        total = len(buckets[bucket])
        skipped = max(total - len(selected), 0)
        selected_count += len(selected)
        bucket_coverage.append(EvidenceBucketCoverage(bucket=bucket, total_count=total, selected_count=len(selected), skipped_count=skipped, selected_paths=selected))
        if skipped and bucket.startswith("source:"):
            warnings.append({"code": "source_sampling_truncated", "bucket": bucket, "message": f"{bucket} skipped {skipped} files"})
    return EvidenceCoverage(detected_file_count=len(files), selected_evidence_count=selected_count, bucket_coverage=bucket_coverage, warnings=warnings)
```

Use a version of `_coverage` that receives `root`.

- [ ] **Step 5: Run tests**

```bash
.venv/bin/python -m pytest tests/unit/test_evidence_collector.py tests/unit/test_schema_contracts.py -q
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add src/harness_builder_agent/tools/evidence_collector.py tests/unit/test_evidence_collector.py
git commit -m "feat: stratify evidence collection"
```

---

### Task 3: LLM Prompt Includes Coverage

**Files:**
- Modify: `src/harness_builder_agent/tools/llm_scan_analyzer.py`
- Modify: `tests/unit/test_llm_scan_analyzer.py`

- [ ] **Step 1: Write failing prompt test**

Add test:

```python
def test_scan_prompt_explains_coverage_and_priority_evidence():
    bundle = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        priority_files=[{"path": "pom.xml", "kind": "build", "priority": "critical", "bucket": "build"}],
        test_files=[{"path": "quality/checks/UserFlowSpec.cs", "kind": "test", "priority": "high", "bucket": "test"}],
        api_entrypoints=[{"path": "src/api/UserController.java", "kind": "api_entrypoint", "priority": "critical", "bucket": "api_entrypoint"}],
        coverage={
            "detected_file_count": 50,
            "selected_evidence_count": 3,
            "bucket_coverage": [],
            "warnings": [{"code": "source_sampling_truncated", "message": "source skipped"}],
        },
    )

    combined = "\n".join(message["content"] for message in build_scan_messages(bundle))

    assert "coverage" in combined.lower()
    assert "priority_files" in combined
    assert "test_files" in combined
    assert "api_entrypoints" in combined
    assert "Do not conclude there are no tests only because a standard tests directory is missing" in combined
```

- [ ] **Step 2: Verify test fails**

```bash
.venv/bin/python -m pytest tests/unit/test_llm_scan_analyzer.py::test_scan_prompt_explains_coverage_and_priority_evidence -q
```

Expected: fail because prompt lacks the exact guidance.

- [ ] **Step 3: Update prompt contract**

In `build_scan_messages()`, add to `schema_contract`:

```text
Evidence coverage rules:
- Review coverage, priority_files, test_files, api_entrypoints, and risk_files before deciding confidence.
- Prefer critical/high priority evidence over ordinary source samples.
- Do not conclude there are no tests only because a standard tests directory is missing; inspect test_files and command evidence.
- If coverage warnings show skipped source buckets or missing key buckets, lower confidence or set needs_human_confirmation=true.
- Mention important coverage uncertainty briefly in reasoning_summary.
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/unit/test_llm_scan_analyzer.py -q
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/llm_scan_analyzer.py tests/unit/test_llm_scan_analyzer.py
git commit -m "feat: include evidence coverage in scan prompt"
```

---

### Task 4: Reconcile Coverage Into Scan Metadata

**Files:**
- Modify: `src/harness_builder_agent/tools/scan_reconciler.py`
- Modify: `tests/unit/test_scan_reconciler.py`

- [ ] **Step 1: Write failing metadata test**

Add test:

```python
def test_reconcile_persists_evidence_coverage_and_warnings():
    evidence = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[EvidenceFile(path="pom.xml", kind="build", priority="critical", bucket="build")],
        key_files=[EvidenceFile(path="pom.xml", kind="build", priority="critical", bucket="build")],
        coverage={
            "detected_file_count": 40,
            "selected_evidence_count": 3,
            "bucket_coverage": [
                {
                    "bucket": "source:.java",
                    "total_count": 30,
                    "selected_count": 2,
                    "skipped_count": 28,
                    "selected_paths": ["src/App.java"],
                }
            ],
            "warnings": [{"code": "source_sampling_truncated", "message": "source:.java skipped files"}],
        },
    )

    inventory, _commands, metadata = reconcile_scan(evidence, _proposal())

    assert metadata.coverage["selected_evidence_count"] == 3
    assert metadata.coverage["bucket_coverage"][0]["skipped_count"] == 28
    assert any(warning.code == "source_sampling_truncated" for warning in metadata.warnings)
    assert inventory.stack_extensions["scan_metadata"]["coverage"]["selected_evidence_count"] == 3
```

- [ ] **Step 2: Verify test fails**

```bash
.venv/bin/python -m pytest tests/unit/test_scan_reconciler.py::test_reconcile_persists_evidence_coverage_and_warnings -q
```

Expected: fail because metadata coverage/warning propagation is missing.

- [ ] **Step 3: Implement metadata propagation**

In `reconcile_scan()`:

```python
warnings: list[ScanWarning] = []
warnings.extend(_coverage_warnings(evidence))
```

Pass `coverage=evidence.coverage.model_dump(mode="json") if evidence.coverage else None` into `ScanMetadata`.

Add helper:

```python
def _coverage_warnings(evidence: EvidenceBundle) -> list[ScanWarning]:
    if not evidence.coverage:
        return []
    warnings: list[ScanWarning] = []
    for item in evidence.coverage.warnings:
        warnings.append(
            ScanWarning(
                code=str(item.get("code", "evidence_coverage_warning")),
                message=str(item.get("message", "Evidence coverage warning.")),
                severity="warning",
                evidence=[str(item.get("bucket"))] if item.get("bucket") else [],
            )
        )
    if not evidence.test_files:
        warnings.append(
            ScanWarning(
                code="test_evidence_not_found",
                message="No dedicated test evidence bucket was found; test strategy needs human confirmation.",
                severity="warning",
            )
        )
    return warnings
```

- [ ] **Step 4: Run tests**

```bash
.venv/bin/python -m pytest tests/unit/test_scan_reconciler.py tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py -q
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add src/harness_builder_agent/tools/scan_reconciler.py tests/unit/test_scan_reconciler.py
git commit -m "feat: persist evidence coverage in scan metadata"
```

---

### Task 5: Todo Status And Final Verification

**Files:**
- Modify: `docs/todos/evidence-depth-for-large-repositories.md`

- [ ] **Step 1: Run targeted tests**

```bash
.venv/bin/python -m pytest tests/unit/test_evidence_collector.py tests/unit/test_llm_scan_analyzer.py tests/unit/test_scan_reconciler.py tests/unit/test_schema_contracts.py -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py tests/e2e/test_fixture_end_to_end.py -q
```

Expected: pass.

- [ ] **Step 2: Run full verification**

```bash
scripts/test-full.sh
```

Expected: fast regression passes and acceptance passes.

- [ ] **Step 3: Update todo**

Change status:

```markdown
- 状态：implemented
```

Add implementation result:

```markdown
## 实现结果

- Evidence schema 已支持 priority、bucket、分层 evidence 和 coverage。
- Evidence collector 已从简单源码前 N 个采样升级为分层采样，关键构建、配置、CI、测试、API 入口和风险文件不会被普通源码样本挤掉。
- LLM scan prompt 已包含 coverage 和 priority evidence 使用规则。
- `scan-metadata.yaml` 已记录 coverage、截断和扫描风险 warning。
- 已补充大仓库、多语言、非标准测试目录和 metadata 传播相关测试。
```

- [ ] **Step 4: Commit**

```bash
git add docs/todos/evidence-depth-for-large-repositories.md
git commit -m "docs: mark evidence depth implemented"
```
