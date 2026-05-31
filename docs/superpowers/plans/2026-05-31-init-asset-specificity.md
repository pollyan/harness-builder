# Init 资产仓库特异性增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `init` 生成的 Guide、Sensor 和 init-summary 明确吸收仓库扫描事实、用户补充和成熟度缺口。

**Architecture:** 保持现有 writer 分层，只扩展函数签名和 Markdown 渲染辅助函数。`write_initial_assets()` 继续负责串联数据流，语义资产 writer 只消费已校验的 Pydantic 对象和交互决策，不新增机器消费 schema。

**Tech Stack:** Python、Pydantic schema、Typer CLI、pytest。

---

### Task 1: 写 Guide 资产失败测试

**Files:**
- Modify: `tests/unit/test_asset_writer_guides.py`

- [x] **Step 1: 扩展 fixture**

在 `_inventory()` 中加入 `stack_extensions.risk_areas` 和 `human_overrides`，增加 `_commands()` 返回 `CommandCatalog`。

- [x] **Step 2: 增加断言**

在 `test_write_guide_assets_writes_guides_templates_and_records_trace` 中调用新签名：

```python
write_guide_assets(ai, _inventory(tmp_path), _commands(), _weapon_selection(), trace=trace)
```

断言 `project-context.md` 包含：

- `## 风险区域`
- `## 验证入口`
- `## 成熟度缺口关联`
- `src/main/resources/application.yml`
- `mvn test`

- [x] **Step 3: 运行失败测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_guides.py::test_write_guide_assets_writes_guides_templates_and_records_trace -q
```

Expected: FAIL，因为 `write_guide_assets()` 尚未接收 commands，也没有新章节。

### Task 2: 实现 Guide 资产渲染

**Files:**
- Modify: `src/harness_builder_agent/tools/asset_writers/guides.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`

- [x] **Step 1: 扩展签名**

`write_guide_assets(ai, inventory, commands, weapon_selection, context_inputs=None, interaction_decisions=None, trace=None)`。

- [x] **Step 2: 增加渲染辅助函数**

新增 `_risk_area_lines()`、`_validation_entry_lines()`、`_maturity_gap_lines()`。

- [x] **Step 3: 写入新章节**

在 `project-context.md` 中追加 `## 风险区域`、`## 验证入口`、`## 成熟度缺口关联`。

- [x] **Step 4: 更新编排调用**

`write_initial_assets()` 将 `commands` 传给 `write_guide_assets()`。

- [x] **Step 5: 运行测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_guides.py::test_write_guide_assets_writes_guides_templates_and_records_trace -q
```

Expected: PASS。

### Task 3: 写 Sensor 和 Summary 失败测试

**Files:**
- Modify: `tests/unit/test_asset_writer_sensors.py`
- Modify: `tests/unit/test_init_summary.py`

- [x] **Step 1: Sensor 测试增加 inventory**

新增 `_inventory()`，调用：

```python
write_sensor_assets(ai, _commands(), _weapon_selection(), inventory=_inventory(tmp_path), trace=trace)
```

断言 `verification.md` 包含 `## 风险与验证映射`、`## 成熟度缺口关联`、风险路径和 `mvn test`。

- [x] **Step 2: Summary 测试增加上下文**

构造 `ProjectInventory`、`CommandCatalog` 和 `accepted_interactive_decisions()`，调用：

```python
build_init_summary_markdown(_score(), ai=ai, inventory=inventory, commands=commands, interaction_decisions=decisions)
```

断言包含 `## 本仓库关键事实`、`## 本次吸收的用户补充`、`## 资产如何补齐缺口`、风险路径、命令和用户补充。

- [x] **Step 3: 运行失败测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_sensors.py::test_write_sensor_assets_writes_sensor_docs_and_records_trace tests/unit/test_init_summary.py -q
```

Expected: FAIL，因为 production code 尚未扩展。

### Task 4: 实现 Sensor 和 Summary 渲染

**Files:**
- Modify: `src/harness_builder_agent/tools/asset_writers/sensors.py`
- Modify: `src/harness_builder_agent/tools/asset_writers/reports.py`
- Modify: `src/harness_builder_agent/tools/init_summary.py`
- Modify: `src/harness_builder_agent/tools/write_assets.py`

- [x] **Step 1: Sensor 增加 inventory 参数**

`write_sensor_assets(..., inventory=None, trace=None)`，`_sensor_doc()` 读取风险区域并渲染映射章节。

- [x] **Step 2: Summary 增加可选上下文**

`write_init_summary()` 和 `build_init_summary_markdown()` 增加 `inventory=None`、`commands=None`、`interaction_decisions=None`。

- [x] **Step 3: Report 编排传递上下文**

`write_report_assets()` 增加 `interaction_decisions=None`，传给 `write_init_summary()`。

- [x] **Step 4: write_initial_assets 串联**

`write_initial_assets()` 将 `decisions` 传给 `write_report_assets()`，将 `inventory` 传给 `write_sensor_assets()`。

- [x] **Step 5: 运行测试**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_sensors.py tests/unit/test_init_summary.py -q
```

Expected: PASS。

### Task 5: 集成验收和文档

**Files:**
- Modify: `tests/integration/test_init_on_fixture_projects.py`
- Modify: `tests/unit/test_write_assets.py`
- Modify: `docs/engineering/init-workflow.md`
- Modify: `docs/evolution-log.md`

- [x] **Step 1: 更新 guided init 集成测试**

在 `test_guided_init_structured_scan_corrections_update_modules_commands_and_risks` 断言 `verification.md` 和 `init-summary.md` 包含 `frontend/package.json`、`npm test`、`前端依赖需要单独确认`。

- [x] **Step 2: 更新 write_assets 集成式单元测试**

断言 `project-context.md`、`verification.md`、`init-summary.md` 都包含风险路径和验证命令。

- [x] **Step 3: 更新工程规则**

在 `docs/engineering/init-workflow.md` 的语义资产规则中记录：正式 Guide/Sensor/Summary 必须复用扫描事实、命令和用户补充。

- [x] **Step 4: 记录演进日志**

在 `docs/evolution-log.md` 增加本轮中文条目，说明完成内容和后续缺口。

- [x] **Step 5: 运行定向测试和快速回归**

Run:

```bash
.venv/bin/python -m pytest tests/unit/test_asset_writer_guides.py tests/unit/test_asset_writer_sensors.py tests/unit/test_init_summary.py tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_structured_scan_corrections_update_modules_commands_and_risks -q
scripts/test-fast.sh
```

Expected: 全部通过。

### Task 6: 提交和推送前验证

- [ ] **Step 1: 检查工作区**

Run:

```bash
git status --short
```

- [ ] **Step 2: 提交**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-init-asset-specificity-design.md docs/superpowers/plans/2026-05-31-init-asset-specificity.md docs/engineering/init-workflow.md docs/evolution-log.md src/harness_builder_agent/tools/write_assets.py src/harness_builder_agent/tools/asset_writers/guides.py src/harness_builder_agent/tools/asset_writers/sensors.py src/harness_builder_agent/tools/asset_writers/reports.py src/harness_builder_agent/tools/init_summary.py tests/unit/test_asset_writer_guides.py tests/unit/test_asset_writer_sensors.py tests/unit/test_init_summary.py tests/unit/test_write_assets.py tests/integration/test_init_on_fixture_projects.py
git commit -m "增强init资产仓库特异性"
```

- [ ] **Step 3: push 前全量验证**

Run:

```bash
scripts/test-full.sh
```

- [ ] **Step 4: 推送**

Run:

```bash
git push origin main
```
