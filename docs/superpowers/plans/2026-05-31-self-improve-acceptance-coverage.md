# Self-Improve Acceptance Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real DeepSeek acceptance coverage for the `self-improve` command on one real repository.

**Architecture:** Extend the existing real repository acceptance helper with an opt-in `run_self_improve` flag. Validate the generated self-improve package and asset candidates through their Pydantic schemas, then rely on benchmark to validate the optional review artifact.

**Tech Stack:** Python, pytest, PyYAML, Pydantic schemas, Typer CLI subprocess acceptance harness.

---

### Task 1: Acceptance Test Red

**Files:**
- Modify: `tests/acceptance/test_real_repositories_e2e.py`

- [ ] **Step 1: Write the failing acceptance expectation**

Import `AssetCandidateReport` and `SelfImprovePackageManifest`. Add an optional `run_self_improve` parameter to `_assert_real_repo`. Before adding the CLI call, assert that when `run_self_improve=True`, `.ai/review/self-improve-package.yaml` exists and benchmark contains a passing `content:self-improve-package` check.

- [ ] **Step 2: Run the targeted acceptance test**

Run:

```bash
unset HARNESS_BUILDER_LLM_API_KEY HARNESS_BUILDER_LLM_MODEL HARNESS_BUILDER_LLM_BASE_URL HARNESS_BUILDER_LLM_TEMPERATURE HARNESS_BUILDER_LLM_MAX_TOKENS
export DEEPSEEK_API_KEY="$(awk -F= '/^DEEPSEEK_API_KEY=/{print substr($0, index($0,"=")+1); exit}' .env)"
.venv/bin/python -m pytest tests/acceptance/test_real_repositories_e2e.py -q
```

Expected: fail because the package has not been generated.

### Task 2: Acceptance Green

**Files:**
- Modify: `tests/acceptance/test_real_repositories_e2e.py`
- Modify: `docs/engineering/testing-strategy.md`
- Modify: `docs/todos/README.md`
- Modify: `docs/todos/archive.md`
- Delete: `docs/todos/self-improve-acceptance-coverage.md`

- [ ] **Step 1: Add the self-improve CLI call**

When `run_self_improve=True`, call:

```python
self_improve_result = _run_cli("self-improve", "--repo", str(repo))
assert self_improve_result.returncode == 0, self_improve_result.stderr + self_improve_result.stdout
```

Set `run_self_improve=True` only for `RuoYi-Vue`.

- [ ] **Step 2: Validate generated artifacts**

Validate:

```python
manifest = SelfImprovePackageManifest.model_validate(yaml.safe_load((ai / "review" / "self-improve-package.yaml").read_text()))
asset_candidates = AssetCandidateReport.model_validate(yaml.safe_load((ai / "review" / "asset-candidates.yaml").read_text()))
assert manifest.review_status == "pending_harness_maintainer_review"
assert all(candidate.review_status == "pending_harness_maintainer_review" for candidate in asset_candidates.candidates)
```

- [ ] **Step 3: Update docs and todo archive**

Update testing strategy to state one real repository covers `self-improve`. Move the todo from README to archive and delete the active todo file.

- [ ] **Step 4: Run targeted acceptance**

Run the command from Task 1. Expected: pass.

### Task 3: Verification And Commit

**Files:**
- Review: all changed files

- [ ] **Step 1: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [ ] **Step 2: Run full regression**

Run:

```bash
unset HARNESS_BUILDER_LLM_API_KEY HARNESS_BUILDER_LLM_MODEL HARNESS_BUILDER_LLM_BASE_URL HARNESS_BUILDER_LLM_TEMPERATURE HARNESS_BUILDER_LLM_MAX_TOKENS
export DEEPSEEK_API_KEY="$(awk -F= '/^DEEPSEEK_API_KEY=/{print substr($0, index($0,"=")+1); exit}' .env)"
scripts/test-full.sh
```

Expected: pass.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs tests
git commit -m "test: cover self-improve in acceptance"
```
