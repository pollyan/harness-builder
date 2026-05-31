# Guided Init 写入前推荐项成熟度关联 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让首次 guided `init` 写入前 preview 中的 Guide / Sensor 推荐逐项说明成熟度关联、阻断项和下一阶段贡献。

**Architecture:** 只改 `interactive_init.py` 的 guided CLI preview 渲染层，复用 `build_maturity_report()` 的内存结果和 weapon tags，不改 Pydantic schema、asset writers、benchmark 或非交互路径。测试通过 guided integration 断言 transcript。

**Tech Stack:** Python、Typer、pytest、现有 maturity model 和 weapon library。

---

### Task 1: 写 RED 测试

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [ ] **Step 1: 扩展 happy path preview 断言**

在 `test_init_default_guided_mode_accepts_happy_path` 中增加：

```python
    preview = result.output[result.output.index("写入前 Harness 设计预览"):result.output.index("最终确认")]
    guides_preview = preview[preview.index("将生成的 Guides"):preview.index("将生成的 Sensors")]
    sensors_preview = preview[preview.index("将生成的 Sensors"):preview.index("Workflow routing")]
    assert "关联成熟度" in guides_preview
    assert "解决阻断" in guides_preview
    assert "下一阶段贡献" in guides_preview
    assert "Guides 上下文" in guides_preview
    assert "Risk Control 风险控制" in guides_preview
    assert "关联成熟度" in sensors_preview
    assert "解决阻断" in sensors_preview
    assert "下一阶段贡献" in sensors_preview
    assert "Sensors 验证" in sensors_preview
    assert "Verification 验证成熟度" in sensors_preview
```

- [ ] **Step 2: 运行 RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path -q
```

Expected: 失败，因为当前推荐项没有逐项成熟度关联说明。

### Task 2: 实现 preview 成熟度关联渲染

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [ ] **Step 1: 替换 Guide / Sensor preview 输出**

把 `_show_prewrite_maturity_preview()` 中 Guide / Sensor 循环改为调用：

```python
    for weapon in weapon_selection.guide_weapons[:3]:
        _show_weapon_preview_item(weapon, planned)
```

和：

```python
    for weapon in weapon_selection.sensor_weapons[:3]:
        _show_weapon_preview_item(weapon, planned, include_gate=True)
```

- [ ] **Step 2: 新增 helper 函数**

新增：

```python
def _show_weapon_preview_item(weapon, planned: MaturityReport, *, include_gate: bool = False) -> None:
    suffix = f"，建议 gate={weapon.gate}" if include_gate else ""
    typer.echo(f"- {weapon.title}：{weapon.recommended_action}{suffix}")
    typer.echo(f"  关联成熟度：{_maturity_dimension_labels(_weapon_maturity_dimension_keys(weapon))}")
    typer.echo(f"  解决阻断：{_weapon_blocker_summary(_weapon_maturity_dimension_keys(weapon), planned)}")
    typer.echo(f"  下一阶段贡献：{_weapon_next_lift_summary(_weapon_maturity_dimension_keys(weapon), planned)}")
```

并实现 `_weapon_maturity_dimension_keys()`、`_maturity_dimension_labels()`、`_weapon_blocker_summary()`、`_weapon_next_lift_summary()`。

### Task 3: 更新文档与演进记录

**Files:**
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/evolution-log.md`

- [ ] **Step 1: 更新 init workflow**

在写入前成熟度初评与设计预览规则中补充：Guide / Sensor 推荐项必须展示关联成熟度、解决阻断和下一阶段贡献。

- [ ] **Step 2: 更新 evolution log**

在顶部新增 `2026-05-31 Guided Init 推荐项成熟度关联`。

### Task 4: 验证并提交

**Files:** all changed files.

- [ ] **Step 1: 运行 targeted test**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path -q
```

Expected: `1 passed`.

- [ ] **Step 2: 运行 guided init integration**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
```

Expected: all tests passed.

- [ ] **Step 3: commit 前快速回归**

Run:

```bash
scripts/test-fast.sh
```

Expected: all tests passed.

- [ ] **Step 4: commit、full regression、push**

Run:

```bash
git add src/harness_builder_agent/tools/interactive_init.py tests/integration/test_init_on_fixture_projects.py docs/engineering/init-workflow.md docs/evolution-log.md docs/superpowers/specs/2026-05-31-guided-init-preview-maturity-linkage-design.md docs/superpowers/plans/2026-05-31-guided-init-preview-maturity-linkage.md
git commit -m "增加guided-init推荐项成熟度关联"
scripts/test-full.sh
git push --no-verify origin main
```

Expected: full regression 通过后推送。
