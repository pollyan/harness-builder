# Scan Follow-up Self-check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `ScanMetadata.followup_questions` 被一轮 review-only LLM self-check 消费，并把结论写入 scan metadata、guided CLI 和 questionnaire。

**Architecture:** 新增独立 LLM tool `llm_scan_self_checker.py`，通过 prompt registry 加载集中管理的机器 prompt。`scan_repository()` 在 reconcile 后、存在 follow-up 且真实 LLM 或显式 mock caller 可用时运行 self-check，再把 `ScanMetadata.self_check` 回填到 inventory；CLI 和 questionnaire 只展示/透传，不自动修正正式扫描结论。

**Tech Stack:** Python、Pydantic、Typer CLI、pytest、现有 prompt registry / DeepSeek caller 注入。

---

## 文件结构

- 修改 `src/harness_builder_agent/schemas/scan.py`：新增 `ScanSelfCheckResolution`、`ScanSelfCheckReport`，并把 `self_check` 挂到 `ScanMetadata`。
- 新增 `src/harness_builder_agent/tools/llm_scan_self_checker.py`：构建 prompt messages、调用 LLM、解析 JSON、校验 interaction id 和 evidence source allowlist。
- 新增 `src/harness_builder_agent/prompts/llm_scan_self_check_v1.md`：集中管理 self-check prompt。
- 修改 `src/harness_builder_agent/prompts/registry.py`：登记新 prompt。
- 修改 `src/harness_builder_agent/tools/scan_repo.py`：在 follow-up 存在时运行 self-check 并发出 progress event。
- 修改 `src/harness_builder_agent/tools/interactive_init.py`：展示“LLM 二次自检”。
- 修改 `src/harness_builder_agent/tools/human_confirmation.py`：把 self-check resolution 追加到 follow-up confirmation reason。
- 修改测试：`tests/unit/test_schema_contracts.py`、新增 `tests/unit/test_llm_scan_self_checker.py`、`tests/unit/test_scan_repo.py`、`tests/unit/test_human_confirmation.py`、`tests/integration/test_init_on_fixture_projects.py`。
- 修改文档：`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/todos/guided-init-ai4se-real-repo-findings.md`、`docs/evolution-log.md`。

## Task 1: Schema 与 LLM Parser

**Files:**
- Modify: `src/harness_builder_agent/schemas/scan.py`
- Create: `src/harness_builder_agent/tools/llm_scan_self_checker.py`
- Create: `src/harness_builder_agent/prompts/llm_scan_self_check_v1.md`
- Modify: `src/harness_builder_agent/prompts/registry.py`
- Test: `tests/unit/test_schema_contracts.py`
- Test: `tests/unit/test_llm_scan_self_checker.py`

- [ ] **Step 1: 写 schema 失败测试**

在 `tests/unit/test_schema_contracts.py` 增加 `test_scan_metadata_accepts_self_check_report`，构造 `ScanMetadata(self_check={...})`，断言 `review_status == "pending_harness_maintainer_review"`、resolution status 和 evidence source 保留。

- [ ] **Step 2: 运行 schema 测试确认失败**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_scan_metadata_accepts_self_check_report -q
```

Expected: FAIL，因为 `ScanMetadata` 还没有 `self_check` 字段或相关 schema。

- [ ] **Step 3: 实现 schema**

在 `schemas/scan.py` 新增：

```python
ScanSelfCheckStatus = Literal[
    "supported_by_current_evidence",
    "needs_human_confirmation",
    "needs_targeted_scan",
    "conflict_detected",
]

class ScanSelfCheckResolution(BaseModel):
    schema_version: str = "1.0"
    interaction_id: str
    trigger: ScanFollowupTrigger
    status: ScanSelfCheckStatus
    rationale: str
    evidence_sources: list[str] = Field(default_factory=list, max_length=8)
    suggested_next_action: str
    confidence: Confidence = "medium"

class ScanSelfCheckReport(BaseModel):
    schema_version: str = "1.0"
    prompt_version: str
    review_status: Literal["pending_harness_maintainer_review"] = "pending_harness_maintainer_review"
    overall_risk: Literal["low", "medium", "high"] = "medium"
    summary: str
    resolutions: list[ScanSelfCheckResolution] = Field(default_factory=list)
```

并在 `ScanMetadata` 增加 `self_check: ScanSelfCheckReport | None = None`。

- [ ] **Step 4: 写 parser 失败测试**

新增 `tests/unit/test_llm_scan_self_checker.py`，覆盖：

- `test_parse_scan_self_check_response_accepts_known_followups_and_sources`
- `test_parse_scan_self_check_response_rejects_unknown_interaction_id`
- `test_parse_scan_self_check_response_rejects_unknown_evidence_source`
- `test_build_scan_self_check_messages_uses_registered_prompt`

- [ ] **Step 5: 运行 parser 测试确认失败**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_scan_self_checker.py -q
```

Expected: FAIL，因为模块和 prompt 还不存在。

- [ ] **Step 6: 实现 prompt、registry 和 parser**

新增 prompt 文件，包含 `## System Message`、`## User Message`、固定 JSON schema 字段、review-only 边界、不得修改正式资产、只能引用输入中的 interaction id 和 evidence source。

新增 `llm_scan_self_checker.py`，提供：

- `SCAN_SELF_CHECK_PROMPT_VERSION`
- `build_scan_self_check_messages(evidence, metadata)`
- `review_scan_followups_with_llm(evidence, metadata, caller=None, config=None)`
- `parse_scan_self_check_response(content, allowed_interaction_ids, allowed_evidence_sources)`

parser 使用与现有 LLM tools 一致的 fenced JSON 提取逻辑，schema 或 allowlist 失败时抛 `ValueError`。

- [ ] **Step 7: 运行 Task 1 测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_scan_metadata_accepts_self_check_report tests/unit/test_llm_scan_self_checker.py tests/unit/test_prompt_assets.py -q
```

Expected: PASS。

## Task 2: scan_repository 调用链路

**Files:**
- Modify: `src/harness_builder_agent/tools/scan_repo.py`
- Test: `tests/unit/test_scan_repo.py`

- [ ] **Step 1: 写 scan repo 失败测试**

在 `tests/unit/test_scan_repo.py` 增加：

- `test_scan_repository_runs_self_check_for_followup_questions`
- `test_scan_repository_skips_self_check_without_followup_questions`

第一条构造 unknown stack / no modules 或 coverage gap 场景触发 follow-up，显式传 `scan_self_check_caller`，断言 calls 包含 `self-check`，metadata 有 `self_check`，progress 有 `scan-self-check`。

- [ ] **Step 2: 运行 scan repo 测试确认失败**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_scan_repo.py::test_scan_repository_runs_self_check_for_followup_questions tests/unit/test_scan_repo.py::test_scan_repository_skips_self_check_without_followup_questions -q
```

Expected: FAIL，因为 `scan_repository()` 还没有 `scan_self_check_caller` 参数和 self-check 阶段。

- [ ] **Step 3: 实现 scan repo 调用**

给 `scan_repository()` 增加 keyword-only 参数：

```python
scan_self_check_caller: Callable[[list[dict[str, str]]], str] | None = None
```

在 reconcile 后：

- 如果 `metadata.followup_questions` 为空，跳过。
- 如果 `scan_self_check_caller is not None or llm_caller is None`，运行 `review_scan_followups_with_llm()`。
- 发出 `scan-self-check` started/completed progress。
- 用 `metadata.model_copy(update={"self_check": self_check})` 生成新 metadata。
- 用 `inventory.model_copy(update={"stack_extensions": updated_extensions})` 回填 `scan_metadata`。

- [ ] **Step 4: 运行 Task 2 测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_scan_repo.py -q
```

Expected: PASS。

## Task 3: CLI 与 questionnaire 展示

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`
- Modify: `src/harness_builder_agent/tools/human_confirmation.py`
- Test: `tests/unit/test_human_confirmation.py`
- Test: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: 写展示失败测试**

在 human confirmation unit 中新增 self-check resolution 场景，断言 `scan_followup_confirmation.reason` 包含 `LLM 二次自检`、status 和 suggested next action。

在 guided init integration 中扩展已有 follow-up mock scan metadata，加入 `self_check`，断言输出包含：

- `LLM 二次自检`
- `pending_harness_maintainer_review`
- resolution 的 status 或中文状态
- 下一步建议

- [ ] **Step 2: 运行展示测试确认失败**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_human_confirmation.py::test_build_questionnaire_includes_scan_self_check_resolution tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_scan_followup_questions -q
```

Expected: FAIL，因为 CLI 和 questionnaire 还没消费 `self_check`。

- [ ] **Step 3: 实现展示**

在 `interactive_init.py`：

- `_show_scan_attention_summary()` 中在 `_show_scan_followup_questions()` 后调用 `_show_scan_self_check()`.
- `_scan_self_check(inventory)` 从 metadata 取 `self_check`。
- 展示“LLM 二次自检”，包含 summary、overall risk、review status、前 5 条 resolution 和 review-only 边界说明。
- `_SCAN_PROGRESS_LABELS` 增加 `scan-self-check`。

在 `human_confirmation.py`：

- 建立 `resolution_by_interaction_id`。
- 生成 follow-up question reason 时，如果存在 resolution，追加 `LLM 二次自检：<status>；建议：<suggested_next_action>；理由：<rationale>`。

- [ ] **Step 4: 运行 Task 3 测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_human_confirmation.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_scan_followup_questions -q
```

Expected: PASS。

## Task 4: 文档、演进记录与验证

**Files:**
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/engineering/llm-contracts.md`
- Modify: `docs/todos/guided-init-ai4se-real-repo-findings.md`
- Modify: `docs/evolution-log.md`

- [ ] **Step 1: 更新工程文档**

在 init workflow 和 LLM contracts 中说明：

- `ScanMetadata.self_check` 是 review-only 二次自检报告。
- 它消费 `followup_questions`。
- 它不自动修正 inventory / commands / assets。
- 失败时显式失败，不 fallback。

- [ ] **Step 2: 更新 todo 和 evolution log**

在 ai4se todo 已完成切片中新增本轮，并保留剩余 LLM-planned deep scan / claim-level validation open。

在 evolution log 顶部新增本轮记录，包含 Gap Analysis 摘要、用户故事、sub agent 使用、验证结果和下一轮候选 gap。

- [ ] **Step 3: 运行 targeted 测试和 diff 检查**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_scan_metadata_accepts_self_check_report tests/unit/test_llm_scan_self_checker.py tests/unit/test_scan_repo.py tests/unit/test_human_confirmation.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_scan_followup_questions tests/unit/test_prompt_assets.py -q
git diff --check
```

Expected: PASS。

- [ ] **Step 4: commit 前快速回归**

Run:

```bash
scripts/test-fast.sh
```

Expected: PASS。

- [ ] **Step 5: 本地提交**

Run:

```bash
git add src/harness_builder_agent/schemas/scan.py src/harness_builder_agent/tools/llm_scan_self_checker.py src/harness_builder_agent/prompts/llm_scan_self_check_v1.md src/harness_builder_agent/prompts/registry.py src/harness_builder_agent/tools/scan_repo.py src/harness_builder_agent/tools/interactive_init.py src/harness_builder_agent/tools/human_confirmation.py tests/unit/test_schema_contracts.py tests/unit/test_llm_scan_self_checker.py tests/unit/test_scan_repo.py tests/unit/test_human_confirmation.py tests/integration/test_init_on_fixture_projects.py docs/engineering/init-workflow.md docs/engineering/llm-contracts.md docs/todos/guided-init-ai4se-real-repo-findings.md docs/evolution-log.md docs/superpowers/specs/2026-06-01-scan-followup-self-check-design.md docs/superpowers/plans/2026-06-01-scan-followup-self-check.md
git commit -m "增加扫描追问二次自检"
```

Expected: 创建中文本地 commit；不 push，除非当前工作包达到统一发布边界并先运行 `scripts/test-full.sh`。

## Self-review

- Spec coverage：覆盖 schema、LLM parser、scan repo 调用、CLI、questionnaire、文档和验证。
- Placeholder scan：无 TBD / TODO / later。
- Type consistency：`ScanSelfCheckReport` / `self_check` / `scan-self-check` 命名在 schema、tool、CLI、metadata 中一致。
