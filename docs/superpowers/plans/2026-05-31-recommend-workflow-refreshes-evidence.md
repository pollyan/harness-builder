# Recommend Workflow Refreshes Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Refresh Experience Index and Maturity Evidence immediately after `recommend-workflow` writes review-only workflow recommendation artifacts.

**Architecture:** Extend the existing integration test for `recommend-workflow`, then update the tool to call `write_experience_index` and `assess_maturity` after writing the recommendation. Update CLI trace artifact recording and engineering docs.

**Tech Stack:** Python, Typer integration tests, Pydantic/YAML, pytest.

---

### Task 1: Add failing integration assertions

**Files:**
- Modify: `tests/integration/test_assess_improve_commands.py`

- [x] **Step 1: Assert refreshed evidence artifacts**

In `test_recommend_workflow_writes_review_only_artifacts`, after loading recommendation and markdown, add:

```python
experience_index = yaml.safe_load((repo / ".ai" / "experience" / "experience-index.yaml").read_text(encoding="utf-8"))
maturity_evidence = yaml.safe_load((repo / ".ai" / "maturity-evidence.yaml").read_text(encoding="utf-8"))
assert experience_index["workflow_recommendation_count"] == 1
assert maturity_evidence["experience"]["workflow_recommendation_count"] == 1
```

- [x] **Step 2: Assert trace records refreshed evidence**

After reading `artifacts`, add:

```python
assert {"path": ".ai/experience/experience-index.yaml", "kind": "experience_index"} in artifacts["artifacts"]
assert {"path": ".ai/maturity-evidence.yaml", "kind": "maturity_evidence"} in artifacts["artifacts"]
assert {"path": ".ai/maturity-score.yaml", "kind": "maturity_score"} in artifacts["artifacts"]
```

- [x] **Step 3: Run focused test and confirm failure**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_recommend_workflow_writes_review_only_artifacts -q
```

Expected: fail because evidence artifacts are stale and trace does not record them.

### Task 2: Refresh evidence in tool and trace

**Files:**
- Modify: `src/harness_builder_agent/tools/recommend_workflow.py`
- Modify: `src/harness_builder_agent/cli.py`

- [x] **Step 1: Refresh derived evidence**

In `recommend_workflow.py`, import:

```python
from harness_builder_agent.tools.experience_index import write_experience_index
```

After writing recommendation YAML and Markdown:

```python
write_experience_index(ai)
assess_maturity(root)
```

- [x] **Step 2: Record refreshed artifacts in CLI trace**

In `recommend_workflow_command`, add:

```python
trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
```

and update artifact count from `2` to `5`.

- [x] **Step 3: Run focused test and confirm pass**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_recommend_workflow_writes_review_only_artifacts -q
```

Expected: pass.

### Task 3: Update engineering docs

**Files:**
- Modify: `docs/engineering/architecture.md`
- Modify: `docs/engineering/init-workflow.md`

- [x] **Step 1: Document derived evidence refresh**

Add that `recommend-workflow` writes review artifacts and refreshes derived Experience/Maturity evidence, but does not execute Runtime or apply routing changes.

- [x] **Step 2: Verify references**

Run:

```bash
rg -n "recommend-workflow|workflow recommendation|experience-index.yaml|maturity-evidence.yaml" docs/engineering src tests/integration/test_assess_improve_commands.py
```

Expected: docs, implementation, and tests are referenced.

### Task 4: Verify and commit

- [x] **Step 1: Run focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_recommend_workflow_writes_review_only_artifacts tests/unit/test_experience_index.py tests/unit/test_maturity_evidence.py -q
```

Expected: pass.

- [x] **Step 2: Run fast regression**

Run:

```bash
scripts/test-fast.sh
```

Expected: pass.

- [x] **Step 3: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-recommend-workflow-refreshes-evidence-design.md docs/superpowers/plans/2026-05-31-recommend-workflow-refreshes-evidence.md tests/integration/test_assess_improve_commands.py src/harness_builder_agent/tools/recommend_workflow.py src/harness_builder_agent/cli.py docs/engineering/architecture.md docs/engineering/init-workflow.md
git commit -m "feat: refresh evidence after workflow recommendation"
```

Expected: commit succeeds after pre-commit fast test.

### Self-Review

- Spec coverage: refreshed index/evidence, trace artifacts, review-only boundary, docs, and verification are covered.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: artifact kinds match existing trace conventions.
