# 扫描后成熟度初评前置 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让首次 guided `init` 在扫描发现后、用户补充前展示基于当前扫描结果的 L0-L4 成熟度初评和补充方向。

**Architecture:** 复用现有 `build_maturity_report()`、`HarnessConfig.default()` 和 `select_weapon_library()` 生成一次内存态 planned maturity，只作为 guided CLI transcript。正式 maturity schema、评分规则、资产写入和非交互路径保持不变。

**Tech Stack:** Python、Typer、pytest、现有 Pydantic schema。

---

### Task 1: 写 RED 测试

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`

- [x] **Step 1: 扩展 guided happy path transcript 断言**

在 `test_init_default_guided_mode_accepts_happy_path` 中增加断言：

```python
    assert "扫描后的成熟度初评" in result.output
    assert "按当前扫描写入后预计建立" in result.output
    assert "主要差距" in result.output
    assert "建议优先补充" in result.output
    assert "hard gate 命令" in result.output
    assert "模块边界" in result.output
    assert "风险区域" in result.output
    assert "团队规则、架构边界或测试策略" in result.output
    assert result.output.index("扫描发现") < result.output.index("扫描后的成熟度初评")
    assert result.output.index("扫描后的成熟度初评") < result.output.index("需要你补充或修正的地方")
    assert result.output.index("扫描后的成熟度初评") < result.output.index("当前 Harness 成熟度初评")
```

- [x] **Step 2: 扩展非交互边界断言**

在 `test_init_non_interactive_generates_existing_assets` 中增加：

```python
    assert "扫描后的成熟度初评" not in result.output
```

- [x] **Step 3: 运行 RED**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path tests/integration/test_init_on_fixture_projects.py::test_init_non_interactive_generates_existing_assets -q
```

Expected: guided happy path 失败，因为当前没有前置成熟度初评。

### Task 2: 实现 guided scan maturity snapshot

**Files:**
- Modify: `src/harness_builder_agent/tools/interactive_init.py`

- [x] **Step 1: 在 scan supplement 前调用新 helper**

把 `run_guided_init()` 中扫描发现后的片段改为：

```python
    _show_scan_findings(inventory, commands)
    _show_scan_maturity_snapshot(repo, inventory, commands)
    scan_overrides = _collect_scan_supplement(inventory)
```

- [x] **Step 2: 新增 `_show_scan_maturity_snapshot()`**

在 `_show_scan_attention_summary()` 附近新增：

```python
def _show_scan_maturity_snapshot(repo: Path, inventory: ProjectInventory, commands: CommandCatalog) -> None:
    config = HarnessConfig.default()
    weapon_selection = select_weapon_library(inventory, commands)
    planned = build_maturity_report(
        ai=None,
        inventory=inventory,
        commands=commands,
        config=config,
        weapon_selection=weapon_selection,
    )
    typer.echo("\n扫描后的成熟度初评")
    if _has_existing_partial_harness(repo):
        typer.echo("- 当前从 L1 起步：已发现部分 `.ai` 资产，但还不足以构成完整项目级 Harness。")
    else:
        typer.echo("- 当前从 L0 起步：尚未发现项目级 `.ai` Harness，后续 AI Coding 仍主要依赖临时 prompt 和个人经验。")
    typer.echo(f"- 按当前扫描写入后预计建立：{planned.overall_level} 基线。")
    typer.echo(f"- 下一目标：{planned.target_next_level or planned.overall_level}。")
    typer.echo("- 说明：这是基于当前扫描结果的写入前预测，不代表正式 Harness 已经写入或 benchmark 已经通过。")

    typer.echo("\n主要差距")
    for blocker in planned.blocking_reasons[:3] or ["暂无明确阻断项；仍建议通过 benchmark 和真实任务运行验证。"]:
        typer.echo(f"- {blocker}")

    typer.echo("\n建议优先补充")
    for line in _scan_maturity_followup_lines(planned):
        typer.echo(f"- {line}")
```

- [x] **Step 3: 新增 `_scan_maturity_followup_lines()`**

```python
def _scan_maturity_followup_lines(planned: MaturityReport) -> list[str]:
    return [
        "真实可执行的 hard gate 命令，以及哪些命令只能作为 soft signal。",
        "主要模块边界、入口目录和职责，避免 Guides 过于泛化。",
        "高风险区域，例如权限、数据迁移、配置、支付或核心状态变更路径。",
        "团队规则、架构边界或测试策略，这些会影响成熟度判断和后续 Harness 推荐。",
    ]
```

`planned` 参数保留用于后续按 blocker 动态排序，当前版本不引入复杂策略。

### Task 3: 文档和演进记录

**Files:**
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/evolution-log.md`

- [x] **Step 1: 更新 init workflow**

在 Scan reconcile 或成熟度预览规则中补充：首次 guided `init` 必须在扫描发现后、用户 scan 补充前展示扫描后的成熟度初评，说明 L0 起点、按当前扫描预计建立的基线、下一等级差距和用户补充影响范围。

- [x] **Step 2: 更新 evolution log**

新增 `2026-05-31 Guided Init 扫描后成熟度初评前置`，记录 North Star 模块、gap、用户故事、取舍、验证方式和下一轮候选。

### Task 4: 验证并提交

**Files:** all changed files.

- [x] **Step 1: targeted tests**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path tests/integration/test_init_on_fixture_projects.py::test_init_non_interactive_generates_existing_assets -q
```

Expected: `2 passed`.

- [x] **Step 2: guided integration**

Run:

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
```

Expected: all passed.

- [x] **Step 3: fast / commit**

Run:

```bash
scripts/test-fast.sh
git add src/harness_builder_agent/tools/interactive_init.py tests/integration/test_init_on_fixture_projects.py docs/engineering/init-workflow.md docs/evolution-log.md docs/superpowers/specs/2026-05-31-scan-maturity-snapshot-design.md docs/superpowers/plans/2026-05-31-scan-maturity-snapshot.md
git commit -m "前置guided-init扫描后成熟度初评"
```

Expected: fast regression passed and local commit created.

- [x] **Step 4: 修正 full regression 暴露的 LLM evidence plan 契约问题**

Full regression 第一次运行时，RuoYi-Vue self-improve acceptance 失败，DeepSeek evidence planner 请求了未出现在 `files[].path` 的近似路径。补充 TDD：

```bash
.venv/bin/python -m pytest tests/unit/test_llm_evidence_planner.py::test_plan_evidence_expansion_retries_once_on_allowlist_validation_error -q
```

Expected: 先失败，再实现一次显式契约修正重试，随后 `tests/unit/test_llm_evidence_planner.py tests/unit/test_prompt_assets.py` 通过。

- [ ] **Step 5: full / push**

Run:

```bash
scripts/test-full.sh
git push --no-verify origin main
```
