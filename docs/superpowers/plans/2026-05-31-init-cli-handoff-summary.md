# Init CLI 交付摘要增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `init` 写入完成后的终端输出成为 CLI-first 的交付摘要，而不是只提示用户去看 Markdown 文件。

**Architecture:** 保持 `render_init_completion_message(ai)` 作为 completion message 唯一渲染入口，读取已有 `maturity-score.yaml`、`questionnaire.yaml` 和核心资产路径。只增强 CLI 文案和测试，不改生成资产 schema、不新增命令、不默认执行 benchmark。

**Tech Stack:** Python、Pydantic、Typer CLI、pytest。

---

### Task 1: 写 completion message 单元失败测试

**Files:**
- Modify: `tests/unit/test_init_summary.py`

- [x] **Step 1: 创建最小 `.ai` fixture**

在测试中写入：

```python
(ai / "maturity-score.yaml").write_text(yaml.safe_dump(_score().model_dump(mode="json")), encoding="utf-8")
(ai / "questionnaire.yaml").write_text(
    yaml.safe_dump(
        {
            "schema_version": "1.0",
            "questions": [
                {
                    "interaction_type": "context_confirmation",
                    "interaction_id": "confirm:team-context",
                    "question": "是否有团队规则需要加入 Harness？",
                    "options": ["补充", "暂缓"],
                    "confidence": "medium",
                    "reason": "团队规则会影响 Guides。",
                }
            ],
        },
        allow_unicode=True,
        sort_keys=False,
    ),
    encoding="utf-8",
)
```

- [x] **Step 2: 断言 CLI-first 摘要**

新增测试 `test_init_completion_message_is_cli_first_delivery_summary`，断言 `render_init_completion_message(ai)` 包含：

- `== 初始化完成 ==`
- `本次已生成`
- `当前成熟度`
- `主要证据 / 缺口`
- `Benchmark 健康度`
- `优先查看`
- `仍需人工确认`
- `是否有团队规则需要加入 Harness`
- `本终端摘要是本次 init 的主要交付说明`
- `.ai/init-summary.md`
- `.ai/sensors/verification.md`

- [x] **Step 3: 运行失败测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_init_summary.py::test_init_completion_message_is_cli_first_delivery_summary -q
```

Expected: FAIL，因为当前 completion message 没有这些章节。

### Task 2: 实现 completion message 渲染

**Files:**
- Modify: `src/harness_builder_agent/tools/init_summary.py`
- Modify: `src/harness_builder_agent/cli.py`

- [x] **Step 1: 导入 Questionnaire**

```python
from harness_builder_agent.schemas.human_confirmation import Questionnaire
```

- [x] **Step 2: 改写 `render_init_completion_message()`**

生成中文结构化输出，保留 `_benchmark_readiness(ai)`。

- [x] **Step 3: 增加 helper**

新增：

```python
def _generated_asset_summary(ai: Path) -> str: ...
def _priority_entry_lines(ai: Path) -> str: ...
def _pending_confirmation_lines(ai: Path) -> str: ...
```

`_pending_confirmation_lines()` 读取 `questionnaire.yaml` 并通过 `Questionnaire` schema 校验；缺失时返回查看 `.ai/human-input-needed.md` 的明确提示。

- [x] **Step 3.5: 避免维护路径误用首次交付摘要**

`src/harness_builder_agent/cli.py` 读取当前 trace summary。若存在 `existing_harness_action`，说明这是已有 Harness 维护入口动作，不打印 `render_init_completion_message()`。

- [x] **Step 4: 运行单元测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_init_summary.py -q
```

Expected: PASS。

### Task 3: 写 init CLI 集成断言

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [x] **Step 1: 扩展非交互 init 断言**

在 `test_init_generates_ai_assets_for_java_fixture` 中断言 result output 包含：

- `== 初始化完成 ==`
- `本次已生成`
- `优先查看`
- `仍需人工确认`
- `本终端摘要是本次 init 的主要交付说明`

- [x] **Step 2: 扩展 guided init happy path 断言**

选择已有 guided happy path 测试，补同样的 completion output 断言，证明 guided 路径也 CLI-first。

- [x] **Step 3: 运行失败或通过测试**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_generates_ai_assets_for_java_fixture tests/integration/test_init_on_fixture_projects.py::test_guided_init_runs_happy_path -q
```

如果 guided happy path 测试名不同，用 `rg "guided_init.*happy|扫描仓库|最终确认"` 找到对应测试。

### Task 4: 同步长期规则和演进记录

**Files:**
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/evolution-log.md`
- Modify: `docs/todos/maturity-driven-init-wizard.md`

- [x] **Step 1: 更新 init workflow**

在写入后摘要规则中说明 CLI completion message 必须是主要交付说明，并列出生成结果、成熟度、benchmark、优先入口、待确认问题和 Markdown 持久化边界。

- [x] **Step 2: 更新演进日志**

新增本轮中文条目，记录 gap analysis、用户故事、取舍、验证方式、Self-Harness Gate。

- [x] **Step 3: 更新 todo 状态**

在 `maturity-driven-init-wizard.md` 的已完成切片中追加“CLI completion summary 与 init-summary 交付语义对齐”。

### Task 5: 验证、提交和推送

- [x] **Step 1: 定向测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_init_summary.py tests/integration/test_init_on_fixture_projects.py -q
```

- [x] **Step 2: 快速回归**

Run:

```bash
scripts/test-fast.sh
```

- [ ] **Step 3: 提交**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-init-cli-handoff-summary-design.md docs/superpowers/plans/2026-05-31-init-cli-handoff-summary.md docs/engineering/init-workflow.md docs/evolution-log.md docs/todos/maturity-driven-init-wizard.md src/harness_builder_agent/cli.py src/harness_builder_agent/tools/init_summary.py tests/unit/test_init_summary.py tests/integration/test_init_on_fixture_projects.py
git commit -m "增强init完成后的CLI交付摘要"
```

- [ ] **Step 4: push 前 full**

Run:

```bash
scripts/test-full.sh
```

- [ ] **Step 5: 推送**

Run:

```bash
git push origin main
```
