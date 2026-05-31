# Scan Follow-up Questions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 coverage gap、unsupported stack claim、unknown stack、模块边界缺失和测试 evidence 缺失转成结构化扫描补救追问，并在 guided CLI、questionnaire 和 human-input 中可见。

**Architecture:** 在 scan schema 中新增可选 `ScanFollowupQuestion`，由 `scan_reconciler` 基于现有 warnings / validation 生成并写入 `ScanMetadata`。`interactive_init` 只负责展示；`human_confirmation` 只负责把 follow-up 转成 questionnaire。保持 LLM 调用链路不变。

**Tech Stack:** Python、Pydantic、Typer CLI、pytest。

---

## 文件结构

- 修改 `src/harness_builder_agent/schemas/scan.py`：新增 `ScanFollowupQuestion` 和 `ScanMetadata.followup_questions`。
- 修改 `src/harness_builder_agent/schemas/human_confirmation.py`：新增 `scan_followup_confirmation` interaction type。
- 修改 `src/harness_builder_agent/tools/scan_reconciler.py`：根据 coverage warnings、stack validation、unknown stack、空 modules 生成 follow-up questions。
- 修改 `src/harness_builder_agent/tools/interactive_init.py`：展示 `深度追问` 分组。
- 修改 `src/harness_builder_agent/tools/human_confirmation.py`：将 follow-up questions 写入 questionnaire。
- 修改 `tests/unit/test_schema_contracts.py`、`tests/unit/test_scan_reconciler.py`、`tests/unit/test_human_confirmation.py`、`tests/integration/test_init_on_fixture_projects.py`。
- 修改 `docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/todos/guided-init-ai4se-real-repo-findings.md`、`docs/evolution-log.md`。

## Task 1: 写失败测试

- [ ] **Step 1: ScanMetadata schema 测试**

在 `tests/unit/test_schema_contracts.py` 中新增：

```python
def test_scan_metadata_accepts_followup_questions():
    metadata = ScanMetadata(
        prompt_version="scan-v2",
        evidence_file_count=42,
        followup_questions=[
            {
                "interaction_id": "confirm:scan-followup:coverage-source-java",
                "trigger": "coverage_gap",
                "question": "哪些 Java 目录、入口文件或高风险路径需要补充扫描？",
                "reason": "source:.java 抽样不足，可能影响模块和风险判断。",
                "evidence": ["source:.java"],
                "confidence": "low",
                "affects": ["maturity", "guides", "sensors"],
            }
        ],
    )

    assert metadata.followup_questions[0].trigger == "coverage_gap"
```

- [ ] **Step 2: reconciler 测试**

在 `tests/unit/test_scan_reconciler.py` 中新增测试，构造有 coverage warning、unsupported node claim、unknown stack / no modules 的场景，断言 `metadata.followup_questions` 和 `inventory.stack_extensions["scan_metadata"]["followup_questions"]` 存在稳定 ids。

- [ ] **Step 3: human confirmation 测试**

在 `tests/unit/test_human_confirmation.py` 中新增测试，传入 `scan_metadata.followup_questions`，断言 questionnaire 包含 `scan_followup_confirmation`。

- [ ] **Step 4: guided CLI integration 测试**

在 `tests/integration/test_init_on_fixture_projects.py` 中新增或扩展 guided scan 测试，构造 `scan_metadata.followup_questions`，断言输出包含 `深度追问`、问题、影响范围，并断言 `.ai/questionnaire.yaml` / `.ai/human-input-needed.md` 包含 follow-up id。

- [ ] **Step 5: 运行红灯**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_scan_metadata_accepts_followup_questions tests/unit/test_scan_reconciler.py::test_reconcile_generates_scan_followup_questions tests/unit/test_human_confirmation.py::test_build_questionnaire_includes_scan_followup_questions tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_scan_followup_questions -q
```

Expected: 失败，因为 schema、reconciler、CLI 和 questionnaire 尚未支持。

## Task 2: 实现 schema 和 reconciler

- [ ] **Step 1: scan schema**

在 `schemas/scan.py` 新增：

```python
ScanFollowupTrigger = Literal[
    "coverage_gap",
    "stack_claim_without_evidence",
    "unknown_stack",
    "module_boundary_unclear",
    "test_evidence_missing",
]

class ScanFollowupQuestion(BaseModel):
    schema_version: str = "1.0"
    interaction_id: str
    trigger: ScanFollowupTrigger
    question: str
    reason: str
    evidence: list[str] = Field(default_factory=list)
    confidence: Confidence = "low"
    affects: list[str] = Field(default_factory=list)
```

并在 `ScanMetadata` 添加：

```python
followup_questions: list[ScanFollowupQuestion] = Field(default_factory=list)
```

- [ ] **Step 2: reconciler 生成 follow-ups**

在 `scan_reconciler.py` 中新增 `_build_followup_questions(evidence, proposal, warnings, scan_validation)`，并传入 `ScanMetadata(followup_questions=followups)`。

规则：

- 对每个 `source_sampling_truncated` warning 生成 coverage follow-up。
- 对每个 unsupported stack claim 生成 stack follow-up。
- primary stack unknown 生成 unknown follow-up。
- modules 为空生成 module follow-up。
- `test_evidence_not_found` warning 生成 test evidence follow-up。

id 使用 `_slug()` helper 保持稳定，例如 `confirm:scan-followup:coverage-source-java`。

- [ ] **Step 3: 运行 schema / reconciler 测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py::test_scan_metadata_accepts_followup_questions tests/unit/test_scan_reconciler.py::test_reconcile_generates_scan_followup_questions -q
```

Expected: 通过。

## Task 3: 实现 CLI 和 questionnaire 消费

- [ ] **Step 1: human schema**

在 `QuestionnaireQuestion.interaction_type` Literal 中加入 `scan_followup_confirmation`。

- [ ] **Step 2: questionnaire 生成**

在 `build_questionnaire()` 中读取 `scan_metadata.get("followup_questions", [])`，每个问题追加：

```python
{
    "interaction_type": "scan_followup_confirmation",
    "interaction_id": followup["interaction_id"],
    "question": followup["question"],
    "options": ["补充或修正相关信息", "暂时接受当前不确定性"],
    "confidence": followup.get("confidence", "low"),
    "reason": f"{followup['reason']} 影响：{...}",
}
```

- [ ] **Step 3: guided CLI 展示**

在 `interactive_init.py` 的 scan attention summary 中新增 `_show_scan_followup_questions(inventory)`，非空时输出：

```text
深度追问
- ...（原因：...；影响：...）
```

放在 `LLM 深度补充` 后、`风险区域` 前。

- [ ] **Step 4: 运行 CLI / questionnaire 测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_human_confirmation.py::test_build_questionnaire_includes_scan_followup_questions tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_scan_followup_questions -q
```

Expected: 通过。

## Task 4: 文档、验证、提交

- [ ] **Step 1: 文档更新**

更新：

- `docs/engineering/init-workflow.md`：说明 `ScanMetadata.followup_questions` 和 guided CLI `深度追问`。
- `docs/engineering/llm-contracts.md`：说明 coverage gap / conflict / unknown 先结构化为 follow-up，不伪装成 resolved。
- `docs/todos/guided-init-ai4se-real-repo-findings.md`：新增完成切片，保留二次 self-check / claim-level validation open。
- `docs/evolution-log.md`：新增本轮记录。

- [ ] **Step 2: targeted verification**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_scan_reconciler.py tests/unit/test_human_confirmation.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_scan_followup_questions tests/integration/test_init_on_fixture_projects.py::test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps -q
```

Expected: 通过。

- [ ] **Step 3: diff check**

Run:

```bash
git diff --check
```

Expected: exit 0。

- [ ] **Step 4: 快速回归与提交**

Run:

```bash
scripts/test-fast.sh
git add ...
git commit -m "生成扫描补救追问"
```

Expected: 快速回归通过，创建本地中文 commit。不 push，因为 deep scan 工作包仍未整体完成。

## Self-Review

- Spec coverage：覆盖 metadata、CLI、questionnaire、human-input、文档和测试。
- Placeholder scan：无 TBD / TODO。
- Type consistency：`followup_questions` 只存在于 scan metadata；human confirmation 使用 `scan_followup_confirmation`，不复用 warning 类型。
