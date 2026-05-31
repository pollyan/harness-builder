# LLM 规划式深度扫描 Manifest 语义增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 LLM evidence planner 在全量轻量文件索引中看到 bucket、priority 和 reason，从而能更可靠地规划未采样关键文件的深度读取。

**Architecture:** 不新增 schema，只填充 `EvidenceFile` 现有字段。Python 仍只负责轻量分类、allowlist、预算读取和 schema 校验；LLM planner 负责选择补充读取路径。

**Tech Stack:** Python、Pydantic、pytest、Markdown prompt asset。

---

## Files

- Modify: `src/harness_builder_agent/tools/evidence_collector.py`
- Modify: `src/harness_builder_agent/prompts/llm_evidence_plan_v1.md`
- Modify: `tests/unit/test_evidence_collector.py`
- Modify: `tests/unit/test_llm_evidence_planner.py`
- Modify: `tests/unit/test_scan_repo.py`
- Modify: `docs/todos/guided-init-ai4se-real-repo-findings.md`
- Modify: `docs/evolution-log.md`

## Task 1: 全量轻量 manifest 保留文件语义

- [ ] Step 1: Write failing test in `tests/unit/test_evidence_collector.py`.

```python
def test_collect_evidence_full_manifest_keeps_bucket_priority_reason_without_summary(tmp_path: Path):
    _write(tmp_path / "src" / "api" / "UserController.py", "from flask import Flask\n")
    _write(tmp_path / "src" / "auth" / "AuthService.py", "class AuthService: pass\n")
    for index in range(6):
        _write(tmp_path / "src" / f"Ordinary{index:02d}.py", "print('ordinary')\n")

    bundle = collect_evidence(tmp_path, max_source_samples=1)

    auth = next(item for item in bundle.files if item.path == "src/auth/AuthService.py")
    assert auth.summary is None
    assert auth.bucket == "risk"
    assert auth.priority == "high"
    assert auth.reason == "Security, auth, database, or migration risk area."

    controller = next(item for item in bundle.files if item.path == "src/api/UserController.py")
    assert controller.summary is None
    assert controller.bucket == "api_entrypoint"
    assert controller.priority == "critical"
    assert controller.reason == "API or application entrypoint signal."
```

- [ ] Step 2: Run failing test.

```bash
.venv/bin/python -m pytest tests/unit/test_evidence_collector.py::test_collect_evidence_full_manifest_keeps_bucket_priority_reason_without_summary -q
```

Expected: FAIL because `bundle.files` entries currently lack bucket / priority / reason.

- [ ] Step 3: Implement minimal change in `collect_evidence()`.

```python
evidence_files = [
    _evidence_file(
        path,
        root,
        "file",
        0,
        bucket=_bucket_for(path, root),
        priority=_priority_for(_bucket_for(path, root)),
        reason=_reason_for(path, root, _bucket_for(path, root)),
    )
    for path in files
]
```

If repeated `_bucket_for()` calls make the line noisy, introduce a tiny local loop that computes `bucket` once per file.

- [ ] Step 4: Re-run the targeted test.

Expected: PASS.

## Task 2: Prompt 明确消费 full manifest 语义和 coverage gap

- [ ] Step 1: Write failing test in `tests/unit/test_llm_evidence_planner.py`.

```python
def test_evidence_plan_prompt_explains_full_manifest_semantics_and_coverage_gap():
    bundle = EvidenceBundle(
        repo_name="demo",
        root_path="/tmp/demo",
        files=[
            EvidenceFile(path="src/ordinary.py", kind="file", bucket="source:.py", priority="medium", reason="Representative .py source sample."),
            EvidenceFile(path="src/auth/AuthService.py", kind="file", bucket="risk", priority="high", reason="Security, auth, database, or migration risk area."),
        ],
        source_samples=[
            EvidenceFile(path="src/ordinary.py", kind="source", bucket="source:.py", priority="medium", summary="print('ordinary')"),
        ],
        coverage={
            "detected_file_count": 2,
            "selected_evidence_count": 1,
            "bucket_coverage": [
                {
                    "bucket": "source:.py",
                    "total_count": 2,
                    "selected_count": 1,
                    "skipped_count": 1,
                    "selected_paths": ["src/ordinary.py"],
                }
            ],
            "warnings": [
                {
                    "code": "source_sampling_truncated",
                    "bucket": "source:.py",
                    "total_count": 2,
                    "selected_count": 1,
                    "skipped_count": 1,
                    "message": "source:.py skipped 1 files",
                }
            ],
        },
    )

    combined = "\n".join(message["content"] for message in build_evidence_plan_messages(bundle))

    assert "全量轻量 file manifest" in combined
    assert "bucket / priority / reason" in combined
    assert "coverage warnings" in combined
    assert "未进入初始摘要" in combined
    assert "src/auth/AuthService.py" in combined
    assert '"bucket":"risk"' in combined
    assert '"priority":"high"' in combined
```

- [ ] Step 2: Run failing test.

```bash
.venv/bin/python -m pytest tests/unit/test_llm_evidence_planner.py::test_evidence_plan_prompt_explains_full_manifest_semantics_and_coverage_gap -q
```

Expected: FAIL because prompt does not yet explain full manifest semantics.

- [ ] Step 3: Update `src/harness_builder_agent/prompts/llm_evidence_plan_v1.md`.

Add explicit Chinese instructions:

```markdown
- 输入 JSON 的 `files[]` 是全量轻量 file manifest；这些条目通常没有 summary，但包含 path、size、bucket、priority、reason，用于判断哪些未采样文件值得深入读取。
- 当 `coverage.warnings` 或 bucket coverage 显示 source bucket 被截断时，必须主动检查 `files[]` 中未进入初始摘要的高优先级、风险、API 入口、测试、核心业务目录或异常命名文件。
- 选择补充文件时，不要只围绕已在 `source_samples` 中出现的文件；优先补足会影响 stack、module、command、risk、maturity 判断的 coverage gap。
```

- [ ] Step 4: Re-run targeted prompt test.

Expected: PASS.

## Task 3: scan_repository 纵向证明 planner 可选未采样语义文件

- [ ] Step 1: Extend `tests/unit/test_scan_repo.py::test_scan_repository_uses_llm_evidence_plan_before_final_scan`.

Inside `planner_caller`, assert:

```python
content = messages[-1]["content"]
assert '"path":"src/zz_RefundRiskService.java"' in content
assert '"bucket":"source:.java"' in content
assert '"reason":"Representative .java source sample."' in content
assert "全量轻量 file manifest" in content
```

- [ ] Step 2: Run targeted test.

```bash
.venv/bin/python -m pytest tests/unit/test_scan_repo.py::test_scan_repository_uses_llm_evidence_plan_before_final_scan -q
```

Expected: PASS after Task 1 and Task 2. If it fails, inspect the prompt payload formatting before changing assertions.

## Task 4: 更新 todo 与演进记录

- [ ] Step 1: Update `docs/todos/guided-init-ai4se-real-repo-findings.md`.

Add completed slice:

```markdown
- `2026-06-01 LLM 规划式深度扫描 Manifest 语义增强`：全量轻量 `files[]` manifest 为每个文件保留 bucket、priority、reason，让 LLM evidence planner 在 coverage gap 下能主动选择未采样但高价值的风险、入口、测试或业务文件深度读取；仍不无限制读取全仓。
```

Keep `LLM-planned deep scan` open because plan metadata、claim validation、二次 self-check / 用户确认仍未完成.

- [ ] Step 2: Add `docs/evolution-log.md` entry with Gap Analysis summary, user story, decisions, assumptions, sub agent use, validation, Self-Harness Gate and next candidate gaps.

## Task 5: 验证与提交

- [ ] Step 1: Run targeted tests.

```bash
.venv/bin/python -m pytest tests/unit/test_evidence_collector.py tests/unit/test_llm_evidence_planner.py tests/unit/test_scan_repo.py -q
```

- [ ] Step 2: Run fast regression before commit.

```bash
scripts/test-fast.sh
```

- [ ] Step 3: Stage and commit.

```bash
git add src/harness_builder_agent/tools/evidence_collector.py src/harness_builder_agent/prompts/llm_evidence_plan_v1.md tests/unit/test_evidence_collector.py tests/unit/test_llm_evidence_planner.py tests/unit/test_scan_repo.py docs/todos/guided-init-ai4se-real-repo-findings.md docs/evolution-log.md docs/superpowers/specs/2026-06-01-llm-planned-deep-scan-manifest-design.md docs/superpowers/plans/2026-06-01-llm-planned-deep-scan-manifest.md
git commit -m "增强LLM深度扫描文件索引"
```

本轮不 push；该 todo 的 LLM-planned deep scan 主线尚未整体完成，仍需后续切片。
