# Guided Init LLM Evidence Plan 可见化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让首次 guided `init` 在 CLI 和待确认资产中展示 LLM evidence planner 的补读计划、实际读取结果和低置信度人工确认项。

**Architecture:** 复用上一轮已经进入 `ProjectInventory.stack_extensions["scan_metadata"]["evidence_expansion"]` 的审计数据。`interactive_init.py` 只负责面向用户展示；`human_confirmation.py` 负责把低置信度 evidence expansion 转成 machine-readable questionnaire；schema 扩展只新增一个 interaction type。

**Tech Stack:** Python、Typer CLI、Pydantic schema、pytest integration / unit tests。

---

## 文件结构

- 修改 `src/harness_builder_agent/schemas/human_confirmation.py`：允许新的 `evidence_expansion_confirmation` 交互类型。
- 修改 `src/harness_builder_agent/tools/interactive_init.py`：新增 LLM 深度补充分组渲染 helper，并在扫描关注点中调用。
- 修改 `src/harness_builder_agent/tools/human_confirmation.py`：当 `scan_metadata.evidence_expansion.confidence == "low"` 时追加 evidence expansion confirmation 问题。
- 修改 `tests/integration/test_init_on_fixture_projects.py`：补 guided transcript 行为测试。
- 修改 `tests/unit/test_human_confirmation.py`：补 questionnaire schema / markdown 行为测试。
- 修改 `tests/unit/test_schema_contracts.py`：补 schema 拒绝未知类型之外的新类型正向校验。
- 修改 `docs/engineering/init-workflow.md`、`docs/todos/guided-init-ai4se-real-repo-findings.md`、`docs/evolution-log.md`：同步稳定契约和本轮记录。

## Task 1: 先写失败测试

- [ ] **Step 1: integration 测试 CLI 展示 evidence expansion**

在 `tests/integration/test_init_on_fixture_projects.py` 中新增测试，复用 guided init monkeypatch scan：

```python
def test_guided_init_shows_llm_evidence_expansion_summary(tmp_path: Path, monkeypatch):
    repo = _copy_fixture(tmp_path, "mini-spring-boot")
    monkeypatch.setattr("harness_builder_agent.cli._stdin_is_tty", lambda: True)

    def scan_with_evidence_expansion(repo_path: Path):
        inventory = ProjectInventory(
            repo_name=repo_path.name,
            root_path=str(repo_path),
            primary_stack="java-spring",
            stacks=["java", "spring-boot"],
            modules=[{"name": "app", "path": ".", "kind": "backend"}],
            evidence=[{"path": "pom.xml", "reason": "build config"}],
            stack_extensions={
                "scan_metadata": {
                    "evidence_expansion": {
                        "schema_version": "1.0",
                        "planner_prompt_version": "llm-evidence-plan-v1",
                        "requested_paths": ["src/main/java/com/example/AuthService.java"],
                        "risk_focus": ["auth flow"],
                        "rationale": "认证逻辑未进入初始源码摘要。",
                        "confidence": "low",
                        "read_paths": ["src/main/java/com/example/AuthService.java"],
                        "read_file_count": 1,
                    }
                }
            },
        )
        commands = CommandCatalog(commands=[])
        return inventory, commands

    monkeypatch.setattr("harness_builder_agent.tools.interactive_init.scan_repository", scan_with_evidence_expansion)

    result = CliRunner().invoke(app, ["init", "--repo", str(repo)], input="\n\n\n\n\n\n\nconfirm\n")

    assert result.exit_code == 0, result.output
    assert "LLM 深度补充" in result.output
    assert "src/main/java/com/example/AuthService.java" in result.output
    assert "auth flow" in result.output
    assert "认证逻辑未进入初始源码摘要" in result.output
    assert "置信度：low" in result.output
```

- [ ] **Step 2: unit 测试 low confidence questionnaire**

在 `tests/unit/test_human_confirmation.py` 中新增断言：

```python
def test_build_questionnaire_includes_low_confidence_evidence_expansion():
    questionnaire = build_questionnaire(
        context_inputs={"schema_version": "1.0", "contexts": []},
        scan_metadata={
            "warnings": [],
            "evidence_expansion": {
                "requested_paths": ["src/auth/AuthService.py"],
                "risk_focus": ["auth flow"],
                "rationale": "Auth code was not sampled.",
                "confidence": "low",
                "read_paths": ["src/auth/AuthService.py"],
                "read_file_count": 1,
            },
        },
    )

    question = next(item for item in questionnaire["questions"] if item["interaction_id"] == "confirm:evidence-expansion")
    assert question["interaction_type"] == "evidence_expansion_confirmation"
    assert "src/auth/AuthService.py" in question["question"]
    assert "Auth code was not sampled." in question["reason"]
    Questionnaire.model_validate(questionnaire)
```

- [ ] **Step 3: 运行红灯测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_human_confirmation.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_llm_evidence_expansion_summary -q
```

Expected: 失败。schema 尚不接受 `evidence_expansion_confirmation`，CLI 尚不展示分组。

## Task 2: 实现最小代码

- [ ] **Step 1: 扩展 Questionnaire schema**

在 `QuestionnaireQuestion.interaction_type` 的 Literal 中加入 `"evidence_expansion_confirmation"`。

- [ ] **Step 2: 追加低置信度问题**

在 `build_questionnaire()` 中读取 `scan_metadata.get("evidence_expansion")`。当它是 dict 且 `confidence == "low"` 时，追加：

```python
requested = _format_paths(evidence_expansion.get("requested_paths", []))
read = _format_paths(evidence_expansion.get("read_paths", []))
focus = _format_list(evidence_expansion.get("risk_focus", []))
questions.append({
    "interaction_type": "evidence_expansion_confirmation",
    "interaction_id": "confirm:evidence-expansion",
    "question": f"LLM 深度补充读取的路径是否代表真实关键模块或风险边界？{requested}",
    "options": ["确认这些路径可作为关键 evidence", "人工补充或修正关键路径"],
    "confidence": "low",
    "reason": f"规划原因：{rationale}；关注点：{focus}；实际读取：{read}",
})
```

新增小 helper 时只放在 `human_confirmation.py` 内部，避免跨模块抽象过早。

- [ ] **Step 3: CLI 渲染 helper**

在 `interactive_init.py` 中新增：

```python
def _show_llm_evidence_expansion(inventory: ProjectInventory) -> None:
    expansion = _evidence_expansion(inventory)
    if not expansion:
        return
    typer.echo("\nLLM 深度补充")
    ...
```

在 `_show_scan_attention_summary()` 开头调用，放在风险区域之前。

- [ ] **Step 4: 运行绿灯测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_human_confirmation.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_llm_evidence_expansion_summary -q
```

Expected: 通过。

## Task 3: 补契约测试和文档

- [ ] **Step 1: schema 正向测试**

在 `tests/unit/test_schema_contracts.py` 中新增 `Questionnaire.model_validate()` 正向测试，覆盖 `evidence_expansion_confirmation`。

- [ ] **Step 2: integration 断言 human-input-needed**

扩展 CLI 展示测试，读取 `.ai/questionnaire.yaml` 和 `.ai/human-input-needed.md`，断言：

- schema 通过。
- `confirm:evidence-expansion` 存在。
- Markdown 包含 `confirm:evidence-expansion` 和补读路径。

- [ ] **Step 3: 文档同步**

更新：

- `docs/engineering/init-workflow.md`：说明 guided init 会展示 `evidence_expansion`，低置信度进入 questionnaire / human input。
- `docs/todos/guided-init-ai4se-real-repo-findings.md`：新增已完成切片。
- `docs/evolution-log.md`：新增本轮中文演进记录。

- [ ] **Step 4: 运行相关测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_schema_contracts.py tests/unit/test_human_confirmation.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_shows_llm_evidence_expansion_summary tests/integration/test_init_on_fixture_projects.py::test_guided_init_groups_scan_risks_uncertainties_and_validation_gaps -q
```

Expected: 全部通过。

## Task 4: 验证与提交

- [ ] **Step 1: diff 检查**

Run:

```bash
git diff --check
```

Expected: 无输出，exit 0。

- [ ] **Step 2: 快速回归**

Run:

```bash
scripts/test-fast.sh
```

Expected: 通过。

- [ ] **Step 3: 本地提交**

Run:

```bash
git add src/harness_builder_agent/schemas/human_confirmation.py src/harness_builder_agent/tools/interactive_init.py src/harness_builder_agent/tools/human_confirmation.py tests/unit/test_human_confirmation.py tests/unit/test_schema_contracts.py tests/integration/test_init_on_fixture_projects.py docs/engineering/init-workflow.md docs/todos/guided-init-ai4se-real-repo-findings.md docs/evolution-log.md docs/superpowers/specs/2026-06-01-guided-init-evidence-plan-visibility-design.md docs/superpowers/plans/2026-06-01-guided-init-evidence-plan-visibility.md
git commit -m "展示LLM证据补充计划"
```

Expected: 创建中文本地 commit。不 push；当前 deep scan 工作包仍未整体完成。

## Self-Review

- Spec 覆盖：本 plan 覆盖 CLI transcript、schema、questionnaire、human input、文档记录和验证。
- Placeholder scan：无 TBD / TODO / 以后再说。
- 类型一致性：使用现有 `scan_metadata.evidence_expansion` 字段名，不新增 scan schema。
