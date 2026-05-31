# Guided Init 多栈仓库组合建模 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 guided `init` 能识别并展示 Python Flask + React / TypeScript 组合栈，避免真实多栈仓库被降级为 `unknown`。

**Architecture:** 扩展 scan schema / prompt / reconciler 的 canonical 栈集合，在 reconciler 中派生 `stack_profile` 作为用户叙事；CLI 和 weapon selection 消费这个派生结果，但保留原始 `primary_stack`、`stacks`、`modules` 机器契约。

**Tech Stack:** Python、Pydantic、Typer、pytest。

---

### Task 1: 扫描契约与 Reconciler 红灯测试

**Files:**
- Modify: `tests/unit/test_llm_scan_analyzer.py`
- Modify: `tests/unit/test_scan_reconciler.py`

- [ ] **Step 1: 写 `python-flask` schema 解析测试**

在 `tests/unit/test_llm_scan_analyzer.py` 增加：

```python
def test_parse_llm_scan_response_accepts_python_flask_multistack():
    payload = json.loads(_proposal_json())
    payload["primary_stack"] = "python-flask"
    payload["stacks"] = ["python", "flask", "react", "typescript", "vite"]
    payload["modules"] = [
        {"name": "api", "path": "backend", "kind": "backend"},
        {"name": "web", "path": "frontend", "kind": "frontend"},
    ]

    proposal = parse_llm_scan_response(json.dumps(payload))

    assert proposal.primary_stack == "python-flask"
    assert proposal.stacks == ["python", "flask", "react", "typescript", "vite"]
    assert proposal.modules[0]["kind"] == "backend"
    assert proposal.modules[1]["kind"] == "frontend"
```

- [ ] **Step 2: 写多栈 reconcile 测试**

在 `tests/unit/test_scan_reconciler.py` 增加：

```python
def test_reconcile_preserves_python_flask_react_multistack_profile():
    evidence = EvidenceBundle(
        repo_name="ai4se-like",
        root_path="/tmp/ai4se-like",
        files=[
            EvidenceFile(path="pyproject.toml", kind="build", summary="flask dependency"),
            EvidenceFile(path="requirements.txt", kind="build", summary="Flask"),
            EvidenceFile(path="app.py", kind="source", summary="from flask import Flask"),
            EvidenceFile(path="frontend/package.json", kind="build", summary="react vite typescript"),
            EvidenceFile(path="frontend/src/App.tsx", kind="source", summary="React component"),
        ],
        key_files=[
            EvidenceFile(path="pyproject.toml", kind="build", summary="flask dependency"),
            EvidenceFile(path="frontend/package.json", kind="build", summary="react vite typescript"),
        ],
        source_samples=[
            EvidenceFile(path="app.py", kind="source", summary="from flask import Flask"),
            EvidenceFile(path="frontend/src/App.tsx", kind="source", summary="React component"),
        ],
    )
    proposal = LLMScanProposal(
        primary_stack="python-flask",
        stacks=["python", "flask", "react", "typescript", "vite"],
        modules=[
            {"name": "api", "path": ".", "kind": "backend"},
            {"name": "web", "path": "frontend", "kind": "frontend"},
        ],
        architecture_signals=["Flask API and React frontend"],
        risk_areas=[],
        command_candidates=[
            LLMCommandCandidate(
                id="pytest",
                command="pytest",
                type="test",
                gate="hard",
                source="pyproject.toml",
                confidence="high",
            )
        ],
        configs=[{"path": "pyproject.toml", "kind": "python"}],
        ci_files=[],
        confidence="medium",
        needs_human_confirmation=True,
        reasoning_summary="Flask backend and React frontend evidence.",
    )

    inventory, commands, metadata = reconcile_scan(evidence, proposal)

    assert inventory.primary_stack == "python-flask"
    assert inventory.modules[0]["kind"] == "backend"
    assert inventory.modules[1]["kind"] == "frontend"
    validation = inventory.stack_extensions["scan_validation"]
    assert validation["checked_claims"] == ["python-flask", "node"]
    assert validation["supported_claims"] == ["python-flask", "node"]
    assert validation["unsupported_claims"] == []
    assert inventory.stack_extensions["stack_profile"]["composition_label"] == "Python Flask 后端 + React / TypeScript 前端"
    assert commands.commands[0].gate == "hard"
    assert metadata.warnings == []
```

- [ ] **Step 3: 运行红灯**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_scan_analyzer.py::test_parse_llm_scan_response_accepts_python_flask_multistack tests/unit/test_scan_reconciler.py::test_reconcile_preserves_python_flask_react_multistack_profile -q
```

Expected: 两个测试失败，原因分别是 schema 不接受 `python-flask`、reconciler 没有多栈 profile。

### Task 2: 实现扫描契约、多栈验证和 profile

**Files:**
- Modify: `src/harness_builder_agent/schemas/scan.py`
- Modify: `src/harness_builder_agent/prompts/llm_first_scan_v2.md`
- Modify: `src/harness_builder_agent/tools/scan_reconciler.py`
- Modify: `tests/unit/test_llm_scan_analyzer.py`

- [ ] **Step 1: 增加 `python-flask` canonical 栈**

在 `src/harness_builder_agent/schemas/scan.py` 把 `PrimaryStack` 改为：

```python
PrimaryStack = Literal["java-spring", "dotnet-aspnet", "node", "python-flask", "unknown"]
```

- [ ] **Step 2: 更新 prompt 契约与测试断言**

在 `llm_first_scan_v2.md` 把 primary stack 枚举加入 `python-flask`，增加 Python Flask 判断规则和多栈规则。同步 `test_scan_prompt_asset_exists_and_preserves_machine_contract()` 断言 `python-flask` 存在。

- [ ] **Step 3: 实现 reconciler alias / evidence / profile**

在 `scan_reconciler.py`：

- `STACK_ALIASES` 增加 `python`、`flask`、`pyproject`、`requirements` -> `python-flask`。
- `STACK_ALIASES` 保留 React / TypeScript / Vite -> `node`。
- `_stack_has_evidence()` 增加 `python-flask` 证据判断。
- `_unsupported_stack_reason()` 增加中文或稳定英文 reason。
- `_veto_impossible_stack()` 增加 `python-flask` impossible veto。
- 新增 `_build_stack_profile()`，返回 `primary_label`、`composition_label`、`supported_stacks`、`module_roles`。
- `ProjectInventory.stack_extensions` 写入 `stack_profile`。

- [ ] **Step 4: 运行绿色测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_scan_analyzer.py::test_parse_llm_scan_response_accepts_python_flask_multistack tests/unit/test_llm_scan_analyzer.py::test_scan_prompt_asset_exists_and_preserves_machine_contract tests/unit/test_scan_reconciler.py::test_reconcile_preserves_python_flask_react_multistack_profile -q
```

Expected: PASS。

### Task 3: Weapon library 多栈消费

**Files:**
- Modify: `src/harness_builder_agent/tools/weapon_library.py`
- Modify: `tests/unit/test_weapon_library.py`

- [ ] **Step 1: 写红灯测试**

在 `tests/unit/test_weapon_library.py` 增加：

```python
def test_multistack_python_flask_react_selects_backend_and_frontend_weapons():
    inventory = ProjectInventory(
        repo_name="demo",
        root_path="/tmp/demo",
        primary_stack="python-flask",
        stacks=["python", "flask", "react", "typescript", "vite"],
        modules=[
            {"name": "api", "path": ".", "kind": "backend"},
            {"name": "web", "path": "frontend", "kind": "frontend"},
        ],
    )

    selection = select_weapon_library(inventory, _commands("pytest"))

    assert {"common", "python-flask", "node"}.issubset(set(selection.selected_stacks))
    assert any(item.startswith("python-flask.guide.") for item in selection.guide_weapon_ids)
    assert any(item.startswith("node.guide.") for item in selection.guide_weapon_ids)
    assert any(item.startswith("python-flask.sensor.") for item in selection.sensor_weapon_ids)
    assert any(item.startswith("node.sensor.") for item in selection.sensor_weapon_ids)
    assert any("已发现 pytest" in weapon.recommended_action for weapon in selection.sensor_weapons)
```

- [ ] **Step 2: 运行红灯**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_weapon_library.py::test_multistack_python_flask_react_selects_backend_and_frontend_weapons -q
```

Expected: FAIL，因为当前只有 common / Java / .NET weapons。

- [ ] **Step 3: 增加 Python / Node weapons 和多栈选择**

在 `WEAPON_LIBRARY` 增加 `python-flask.guide.*`、`python-flask.sensor.*`、`node.guide.*`、`node.sensor.*`。`select_weapon_library()` 从 `primary_stack` 与 `stacks` 规范化出 selected stacks，`unknown` 只保留 common。`_promote_matching_hard_gates()` 支持 `pytest` 和 `npm test`。

- [ ] **Step 4: 运行绿色测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_weapon_library.py -q
```

Expected: PASS。

### Task 4: Guided CLI 多栈表达

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: 写 guided integration 红灯测试**

新增 fake scan 返回 `ProjectInventory(primary_stack="python-flask", stacks=["python", "flask", "react", "typescript", "vite"], modules=[backend, frontend], stack_extensions={"stack_profile": {...}})` 和 pytest / npm test commands。断言：

- output 包含 `Python Flask 后端 + React / TypeScript 前端`。
- output 包含 `stack=python-flask`。
- output 包含 `可以直接用自然语言说明多栈、噪声目录或真实主模块`。
- `project-inventory.json` 保留 `primary_stack=python-flask`、frontend module 和 `stack_profile.composition_label`。
- `weapon-library-selection.yaml` 包含 `python-flask` 和 `node`。

- [ ] **Step 2: 运行红灯**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_explains_python_flask_react_multistack -q
```

Expected: FAIL，因为 CLI 仍只展示单栈标签，补充提示不允许 `python-flask`。

- [ ] **Step 3: 实现 CLI helper**

在 `interactive_init.py` 新增 `_stack_summary_label(inventory)`，优先使用 `stack_extensions.stack_profile.composition_label`，否则退回 `_stack_label(primary_stack)`。替换 scan complete、scan findings、existing harness、final confirm 中的用户可见技术栈展示。扩展 `_collect_scan_supplement()` 允许 `stack=python-flask`，并增加自然语言多栈说明。

- [ ] **Step 4: 运行绿色测试**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_explains_python_flask_react_multistack -q
```

Expected: PASS。

### Task 5: 文档、Self-Harness Gate 和回归

**Files:**
- Modify: `docs/todos/guided-init-ai4se-real-repo-findings.md`
- Modify: `docs/evolution-log.md`

- [ ] **Step 1: 更新 todo**

在已完成切片中追加本轮多栈建模，剩余 open 改为成熟度中文叙事和 LLM-planned deep scan。

- [ ] **Step 2: 更新演进记录**

在 `docs/evolution-log.md` 顶部新增本轮记录，包含 gap、用户故事、关键决策、验证方式、sub agent 使用情况和 Self-Harness Gate。

- [ ] **Step 3: 跑 focused tests**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_llm_scan_analyzer.py tests/unit/test_scan_reconciler.py tests/unit/test_weapon_library.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_explains_python_flask_react_multistack -q
```

Expected: PASS。

- [ ] **Step 4: 提交前 fast 回归**

Run:

```bash
scripts/test-fast.sh
```

Expected: PASS。

- [ ] **Step 5: 本地提交**

Run:

```bash
git add src/harness_builder_agent/schemas/scan.py src/harness_builder_agent/prompts/llm_first_scan_v2.md src/harness_builder_agent/tools/scan_reconciler.py src/harness_builder_agent/tools/weapon_library.py src/harness_builder_agent/tools/interactive_init.py tests/unit/test_llm_scan_analyzer.py tests/unit/test_scan_reconciler.py tests/unit/test_weapon_library.py tests/integration/test_init_on_fixture_projects.py docs/todos/guided-init-ai4se-real-repo-findings.md docs/evolution-log.md docs/superpowers/specs/2026-05-31-guided-init-multistack-modeling-design.md docs/superpowers/plans/2026-05-31-guided-init-multistack-modeling.md
git commit -m "支持init多栈仓库表达"
```

Expected: commit succeeds.

