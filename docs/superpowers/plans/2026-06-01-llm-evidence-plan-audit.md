# LLM Evidence Plan 可审计 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 LLM evidence planner 的计划、置信度和实际读取结果写入 scan metadata，让 deep scan 可审计并能触发 human confirmation 信号。

**Architecture:** 新增 `LLMEvidenceExpansionMetadata` Pydantic schema，并作为 `ScanMetadata.evidence_expansion` 的可选字段。`scan_repository()` 保存 planner plan 并传给 `reconcile_scan()`；`reconcile_scan()` 根据 plan 和 `EvidenceBundle.llm_requested_files` 生成 metadata 与 warning。

**Tech Stack:** Python、Pydantic、pytest、YAML scan metadata。

---

## Files

- Modify: `src/harness_builder_agent/schemas/scan.py`
- Modify: `src/harness_builder_agent/tools/scan_repo.py`
- Modify: `src/harness_builder_agent/tools/scan_reconciler.py`
- Modify: `tests/unit/test_schema_contracts.py`
- Modify: `tests/unit/test_scan_repo.py`
- Modify: `tests/unit/test_scan_reconciler.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`
- Modify: `docs/todos/guided-init-ai4se-real-repo-findings.md`
- Modify: `docs/evolution-log.md`

## Task 1: Schema 契约

- [ ] Step 1: Add failing schema test in `tests/unit/test_schema_contracts.py`.

```python
def test_scan_metadata_accepts_evidence_expansion_audit():
    metadata = ScanMetadata(
        prompt_version="scan-v2",
        evidence_file_count=120,
        evidence_expansion={
            "planner_prompt_version": "llm-evidence-plan-v1",
            "requested_paths": ["src/auth/AuthService.py"],
            "risk_focus": ["auth flow"],
            "rationale": "Auth code was not in source samples.",
            "confidence": "low",
            "read_paths": ["src/auth/AuthService.py"],
            "read_file_count": 1,
        },
    )

    assert metadata.evidence_expansion is not None
    assert metadata.evidence_expansion.requested_paths == ["src/auth/AuthService.py"]
    assert metadata.evidence_expansion.read_file_count == 1
```

- [ ] Step 2: Run failing test.

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_scan_metadata_accepts_evidence_expansion_audit -q
```

Expected: FAIL because `ScanMetadata` has no `evidence_expansion`.

- [ ] Step 3: Implement schema in `src/harness_builder_agent/schemas/scan.py`.

Add:

```python
class LLMEvidenceExpansionMetadata(BaseModel):
    schema_version: str = "1.0"
    planner_prompt_version: str | None = None
    requested_paths: list[str] = Field(default_factory=list, max_length=8)
    risk_focus: list[str] = Field(default_factory=list, max_length=8)
    rationale: str
    confidence: Confidence = "medium"
    read_paths: list[str] = Field(default_factory=list, max_length=8)
    read_file_count: int = 0
```

Then add to `ScanMetadata`:

```python
evidence_expansion: LLMEvidenceExpansionMetadata | None = None
```

- [ ] Step 4: Re-run schema test.

Expected: PASS.

## Task 2: Reconciler metadata 和 low-confidence warning

- [ ] Step 1: Add failing tests in `tests/unit/test_scan_reconciler.py`.

Use `LLMEvidencePlan` and evidence with `llm_requested_files`.

Assertions:

```python
assert metadata.evidence_expansion.requested_paths == ["src/auth/AuthService.py"]
assert metadata.evidence_expansion.read_paths == ["src/auth/AuthService.py"]
assert metadata.evidence_expansion.rationale == "Auth code was not sampled."
assert inventory.stack_extensions["scan_metadata"]["evidence_expansion"]["read_file_count"] == 1
```

For low confidence:

```python
assert any(warning.code == "llm_evidence_plan_low_confidence" for warning in metadata.warnings)
assert inventory.stack_extensions["needs_human_confirmation"] is True
```

- [ ] Step 2: Run failing tests.

```bash
.venv/bin/python -m pytest tests/unit/test_scan_reconciler.py::test_reconcile_persists_llm_evidence_expansion_metadata tests/unit/test_scan_reconciler.py::test_reconcile_marks_low_confidence_evidence_plan_for_human_confirmation -q
```

Expected: FAIL because `reconcile_scan()` has no evidence plan parameter.

- [ ] Step 3: Implement in `scan_reconciler.py`.

Import `LLMEvidencePlan` and `EVIDENCE_PLAN_PROMPT_VERSION`.

Change signature:

```python
def reconcile_scan(..., evidence_plan: LLMEvidencePlan | None = None) -> ...
```

Before metadata, if `evidence_plan.confidence == "low"`, append warning. Build evidence expansion metadata from plan and `evidence.llm_requested_files`.

Set:

```python
needs_human_confirmation = proposal.needs_human_confirmation or (
    evidence_plan is not None and evidence_plan.confidence == "low"
)
```

Use that value in `stack_extensions`.

- [ ] Step 4: Re-run reconciler tests.

Expected: PASS.

## Task 3: scan_repository 传递 plan 并验证纵向链路

- [ ] Step 1: Extend `tests/unit/test_scan_repo.py::test_scan_repository_uses_llm_evidence_plan_before_final_scan`.

After scan:

```python
metadata = inventory.stack_extensions["scan_metadata"]
assert metadata["evidence_expansion"]["requested_paths"] == ["src/zz_RefundRiskService.java"]
assert metadata["evidence_expansion"]["risk_focus"] == ["refund flow"]
assert metadata["evidence_expansion"]["rationale"] == "The planner selected the hidden refund risk file from the full index."
assert metadata["evidence_expansion"]["read_paths"] == ["src/zz_RefundRiskService.java"]
assert metadata["evidence_expansion"]["read_file_count"] == 1
```

- [ ] Step 2: Run failing test.

```bash
.venv/bin/python -m pytest tests/unit/test_scan_repo.py::test_scan_repository_uses_llm_evidence_plan_before_final_scan -q
```

Expected: FAIL because `scan_repository()` does not pass plan to reconciler.

- [ ] Step 3: Modify `scan_repo.py`.

Initialize `evidence_plan = None`; assign plan result; pass `evidence_plan=evidence_plan` into `reconcile_scan()`.

- [ ] Step 4: Re-run scan repo test.

Expected: PASS.

## Task 4: Init 产物集成断言

- [ ] Step 1: Update `_assert_init_outputs()` in `tests/integration/test_init_on_fixture_projects.py`.

After loading scan metadata:

```python
ScanMetadata.model_validate(scan_metadata)
assert scan_metadata["evidence_expansion"]["requested_paths"] == []
assert scan_metadata["evidence_expansion"]["read_paths"] == []
assert scan_metadata["evidence_expansion"]["read_file_count"] == 0
```

Need import `ScanMetadata`.

- [ ] Step 2: Run targeted integration test.

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_generates_expected_assets_for_fixtures -q
```

Expected: PASS if non-interactive scan runs planner and writes empty evidence expansion for no requested paths.

## Task 5: Docs and verification

- [ ] Step 1: Update todo completed slice, keeping remaining deep scan open.
- [ ] Step 2: Add `docs/evolution-log.md` entry with gap analysis, user story, decisions, sub agent use, validation and next gaps.
- [ ] Step 3: Run targeted tests.

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_scan_reconciler.py tests/unit/test_scan_repo.py tests/integration/test_init_on_fixture_projects.py::test_init_generates_expected_assets_for_fixtures -q
```

- [ ] Step 4: Run fast regression.

```bash
scripts/test-fast.sh
```

- [ ] Step 5: Commit.

```bash
git add src/harness_builder_agent/schemas/scan.py src/harness_builder_agent/tools/scan_repo.py src/harness_builder_agent/tools/scan_reconciler.py tests/unit/test_schema_contracts.py tests/unit/test_scan_reconciler.py tests/unit/test_scan_repo.py tests/integration/test_init_on_fixture_projects.py docs/todos/guided-init-ai4se-real-repo-findings.md docs/evolution-log.md docs/superpowers/specs/2026-06-01-llm-evidence-plan-audit-design.md docs/superpowers/plans/2026-06-01-llm-evidence-plan-audit.md
git commit -m "记录LLM证据规划审计信息"
```

本轮不 push；`LLM-planned deep scan` 工作包仍有 claim schema hardening 和 claim-level validation 后续切片。
