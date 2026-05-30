# Scanner v2 Validation Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the useful scanner v2 LLM claim validation idea into the current LLM-first scan reconciler without restoring the legacy scanner package.

**Architecture:** Keep `collect_evidence -> analyze_evidence_with_llm -> reconcile_scan` unchanged. Add scanner-v2-inspired validation inside `scan_reconciler` so LLM stack claims are checked against deterministic evidence and persisted as `ScanMetadata.warnings` plus `ProjectInventory.stack_extensions["scan_validation"]`.

**Tech Stack:** Python, Pydantic schemas in `harness_builder_agent.schemas.scan`, pytest, existing `scripts/test-fast.sh` regression gate.

---

## Files

- Modify: `src/harness_builder_agent/tools/scan_reconciler.py`
  - Add normalized stack claim validation helpers.
  - Preserve current primary-stack hard veto behavior.
  - Persist `scan_validation` in `ProjectInventory.stack_extensions`.
- Modify: `tests/unit/test_scan_reconciler.py`
  - Add failing tests for unsupported secondary stack claims, JavaScript-vs-Java false positives, and Java primary veto.
- Modify: `docs/todos/scanner-v2-review-and-migration.md`
  - Mark the todo implemented and point to the spec/plan/code landing.
- Modify: `docs/todos/README.md`
  - Remove the scanner v2 item from the open todo table.
- Modify: `docs/todos/archive.md`
  - Add the scanner v2 validation migration archive entry.

## Task 1: Failing Unit Tests

**Files:**
- Modify: `tests/unit/test_scan_reconciler.py`

- [ ] **Step 1: Add tests for scanner-v2-inspired validation**

Append these tests to `tests/unit/test_scan_reconciler.py`:

```python
def test_reconcile_warns_when_secondary_stack_claim_lacks_evidence():
    evidence = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[EvidenceFile(path="pom.xml", kind="build", summary="maven")],
        key_files=[EvidenceFile(path="pom.xml", kind="build", summary="maven")],
    )
    proposal = _proposal()
    proposal.stacks = ["java", "maven", "node"]

    inventory, _commands, metadata = reconcile_scan(evidence, proposal)

    validation = inventory.stack_extensions["scan_validation"]
    assert validation["checked_claims"] == ["java-spring", "node"]
    assert validation["supported_claims"] == ["java-spring"]
    assert validation["unsupported_claims"] == [
        {
            "stack": "node",
            "reason": "LLM claimed node but no package.json or JS/TS/Vue evidence was found",
        }
    ]
    assert any(warning.code == "llm_stack_claim_without_evidence" for warning in metadata.warnings)
    assert inventory.stack_extensions["scan_warnings"] == [warning.model_dump(mode="json") for warning in metadata.warnings]
```

- [ ] **Step 2: Add JavaScript false-positive coverage**

Append this test to `tests/unit/test_scan_reconciler.py`:

```python
def test_reconcile_does_not_treat_javascript_evidence_as_java_support():
    evidence = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[
            EvidenceFile(path="package.json", kind="build"),
            EvidenceFile(path="src/app.js", kind="source"),
        ],
        key_files=[EvidenceFile(path="package.json", kind="build")],
        source_samples=[EvidenceFile(path="src/app.js", kind="source")],
    )
    proposal = _proposal(command_source="package.json", gate="soft")
    proposal.primary_stack = "node"
    proposal.stacks = ["javascript", "java"]
    proposal.command_candidates = []

    inventory, _commands, metadata = reconcile_scan(evidence, proposal)

    validation = inventory.stack_extensions["scan_validation"]
    assert validation["checked_claims"] == ["node", "java-spring"]
    assert validation["supported_claims"] == ["node"]
    assert validation["unsupported_claims"][0]["stack"] == "java-spring"
    assert any("java-spring" in warning.evidence for warning in metadata.warnings)
```

- [ ] **Step 3: Add primary Java hard-veto coverage**

Append this test to `tests/unit/test_scan_reconciler.py`:

```python
def test_reconcile_vetoes_impossible_java_claim():
    evidence = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[EvidenceFile(path="package.json", kind="build")],
        key_files=[EvidenceFile(path="package.json", kind="build")],
    )
    proposal = _proposal(command_source="package.json")
    proposal.primary_stack = "java-spring"
    proposal.stacks = ["java"]

    with pytest.raises(ScanConflictError, match="Java"):
        reconcile_scan(evidence, proposal)
```

- [ ] **Step 4: Run the focused unit tests and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_scan_reconciler.py -q
```

Expected: at least one failure because `scan_validation` and `llm_stack_claim_without_evidence` are not implemented yet.

## Task 2: Reconciler Validation Implementation

**Files:**
- Modify: `src/harness_builder_agent/tools/scan_reconciler.py`

- [ ] **Step 1: Add stack claim validation helpers**

Add helpers that:

```python
def _validate_stack_claims(evidence: EvidenceBundle, proposal: LLMScanProposal) -> dict[str, object]:
    paths = _all_evidence_paths(evidence)
    checked_claims: list[str] = []
    supported_claims: list[str] = []
    unsupported_claims: list[dict[str, str]] = []
    for stack in _normalized_stack_claims(proposal):
        checked_claims.append(stack)
        if _stack_has_evidence(stack, paths):
            supported_claims.append(stack)
        else:
            unsupported_claims.append({"stack": stack, "reason": _unsupported_stack_reason(stack)})
    return {
        "checked_claims": checked_claims,
        "supported_claims": supported_claims,
        "unsupported_claims": unsupported_claims,
    }
```

Normalization rules:

```python
STACK_ALIASES = {
    "java-spring": "java-spring",
    "java": "java-spring",
    "spring": "java-spring",
    "spring-boot": "java-spring",
    "maven": "java-spring",
    "gradle": "java-spring",
    "dotnet-aspnet": "dotnet-aspnet",
    "dotnet": "dotnet-aspnet",
    ".net": "dotnet-aspnet",
    "csharp": "dotnet-aspnet",
    "c#": "dotnet-aspnet",
    "aspnet": "dotnet-aspnet",
    "node": "node",
    "nodejs": "node",
    "node.js": "node",
    "javascript": "node",
    "typescript": "node",
    "react": "node",
    "vue": "node",
}
```

- [ ] **Step 2: Wire validation into `reconcile_scan`**

Inside `reconcile_scan`, after `_coverage_warnings(evidence)`:

```python
scan_validation = _validate_stack_claims(evidence, proposal)
warnings.extend(_stack_validation_warnings(scan_validation))
```

Then add this field inside `stack_extensions`:

```python
"scan_validation": scan_validation,
```

- [ ] **Step 3: Preserve explicit failure for impossible primary claims**

Keep `_veto_impossible_stack()` before warnings are created. Ensure `java-spring` and `dotnet-aspnet` primary claims still raise `ScanConflictError` when required evidence is absent.

- [ ] **Step 4: Run focused unit tests and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_scan_reconciler.py -q
```

Expected: all `test_scan_reconciler.py` tests pass.

## Task 3: Todo Closure Docs

**Files:**
- Modify: `docs/todos/scanner-v2-review-and-migration.md`
- Modify: `docs/todos/README.md`
- Modify: `docs/todos/archive.md`

- [ ] **Step 1: Mark scanner v2 todo implemented**

Update the status block in `docs/todos/scanner-v2-review-and-migration.md`:

```markdown
- 状态：implemented
```

Add a completion section:

```markdown
## 完成说明

已完成审查并迁移第一轮能力：旧 scanner v2 的 LLM claim validation 思路已落入当前 `scan_reconciler`，以 `ScanMetadata.warnings` 和 `ProjectInventory.stack_extensions["scan_validation"]` 记录 LLM stack claims 与 deterministic evidence 的支持/冲突关系。

相关落点：

- 审查设计：`docs/superpowers/specs/2026-05-31-scanner-v2-review-validation-design.md`
- 实施计划：`docs/superpowers/plans/2026-05-31-scanner-v2-validation-migration.md`
- 代码：`src/harness_builder_agent/tools/scan_reconciler.py`
- 测试：`tests/unit/test_scan_reconciler.py`
```

- [ ] **Step 2: Move the item out of open todos**

Remove the scanner v2 row from `docs/todos/README.md`.

- [ ] **Step 3: Add archive row**

Add this row to `docs/todos/archive.md`:

```markdown
| [旧 scanner v2 实现审查与迁移评估](scanner-v2-review-and-migration.md) | 当前 todo | implemented | 审查旧 scanner v2 并迁移 LLM claim validation 到当前 `scan_reconciler`，产出 `scan_validation` 和 validation warnings |
```

## Task 4: Verification and Commit

**Files:**
- Verify all modified source, tests, and docs.

- [ ] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_scan_reconciler.py -q
```

Expected: pass.

- [ ] **Step 2: Run default non-acceptance regression**

Run:

```bash
.venv/bin/python -m pytest tests/unit tests/integration tests/e2e -q
```

Expected: pass.

- [ ] **Step 3: Run required fast regression before commit**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 4: Commit scanner validation migration**

Run:

```bash
git add src/harness_builder_agent/tools/scan_reconciler.py tests/unit/test_scan_reconciler.py docs/todos/scanner-v2-review-and-migration.md docs/todos/README.md docs/todos/archive.md docs/superpowers/plans/2026-05-31-scanner-v2-validation-migration.md
git commit -m "feat: validate scanner stack claims"
```

Expected: commit succeeds after the pre-commit test gate.
