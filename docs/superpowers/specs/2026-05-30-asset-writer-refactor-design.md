# Asset Writer Refactor Design

## 目标

在不改变 `init` 对外行为和 `.ai` 产物契约的前提下，将 `write_assets.py` 中过重的资产生成逻辑拆分为职责清晰的小模块，为后续 context 深度参与生成、candidate 晋升和交互式 CLI 改造降低风险。

## 当前状态

`src/harness_builder_agent/tools/write_assets.py` 当前同时负责：

- 文件写入工具函数。
- `write_initial_assets` 编排。
- core JSON/YAML 产物。
- human confirmation 产物。
- scan/maturity/evolution 报告。
- guides 和 task templates。
- sensors。
- workflow skills 复制。
- LLM enhancement candidates 和 review 文件。
- trace artifact 记录。
- 多个 Markdown 内容构造函数。

当前已有保护测试：

- `tests/unit/test_write_assets.py`
- `tests/integration/test_init_on_fixture_projects.py`
- `tests/e2e/test_fixture_end_to_end.py`
- `tests/integration/test_benchmark_command.py`

## 设计原则

### 行为不变

本重构不改变：

- `write_initial_assets(repo, inventory, commands, trace=None, context_paths=None)` 签名。
- `.ai` 文件路径。
- JSON/YAML schema。
- Markdown 必需章节。
- Workflow Skill 模板来源。
- trace artifact 记录语义。

### 编排和内容生成分离

`write_assets.py` 保留对外入口和高层编排，具体产物写入交给 `asset_writers/` 下的小模块。

### 共享写入工具集中

低层文件写入函数统一放到一个 shared 模块，避免每个 writer 自己实现 `_write_text`、`_write_yaml`、`_write_json`。

### 私有内容构造跟随所属 writer

例如 guide 的 Markdown builder 放在 `asset_writers/guides.py`，sensor 的 Markdown builder 放在 `asset_writers/sensors.py`，避免继续堆在总入口文件里。

## 目标目录结构

```text
src/harness_builder_agent/tools/write_assets.py
src/harness_builder_agent/tools/asset_writers/__init__.py
src/harness_builder_agent/tools/asset_writers/shared.py
src/harness_builder_agent/tools/asset_writers/core.py
src/harness_builder_agent/tools/asset_writers/human_confirmation.py
src/harness_builder_agent/tools/asset_writers/reports.py
src/harness_builder_agent/tools/asset_writers/guides.py
src/harness_builder_agent/tools/asset_writers/sensors.py
src/harness_builder_agent/tools/asset_writers/skills.py
src/harness_builder_agent/tools/asset_writers/candidates.py
```

## 模块职责

### `write_assets.py`

保留：

- `write_initial_assets`
- `select_weapon_library` 调用
- `HarnessConfig.default()` 调用
- `scan_metadata`、context、questionnaire、candidate 的准备
- trace stage event
- 按顺序调用各 writer
- 返回 `.ai` 路径

不再保留：

- Markdown 内容构造函数
- 具体产物写入细节
- skill copy 细节

### `asset_writers/shared.py`

提供：

- `write_text(path, content)`
- `write_json(path, payload)`
- `write_yaml(path, payload)`
- `record_artifact(trace, path, kind)`

### `asset_writers/core.py`

负责写：

- `.ai/project-inventory.json`
- `.ai/command-catalog.yaml`
- `.ai/harness-config.yaml`
- `.ai/scan-metadata.yaml`
- `.ai/llm-scan-proposal.json`
- `.ai/weapon-library-selection.yaml`

同时拥有：

- `scan_metadata(inventory)`
- `llm_scan_proposal(inventory)`

### `asset_writers/human_confirmation.py`

负责写：

- `.ai/context-inputs.yaml`
- `.ai/questionnaire.yaml`
- `.ai/human-input-needed.md`

不负责读取 context 文件；读取仍由现有 `tools/human_confirmation.py` 提供。

### `asset_writers/reports.py`

负责写：

- `.ai/scan-report.md`
- `.ai/maturity-report.md`
- `.ai/maturity-score.yaml`
- `.ai/evolution-plan.md`

### `asset_writers/guides.py`

负责写：

- `.ai/guides/project-context.md`
- `.ai/guides/coding-rules.md`
- `.ai/guides/architecture.md`
- `.ai/guides/task-templates/bugfix.md`
- `.ai/guides/task-templates/lightweight-feature.md`

同时拥有：

- guide frontmatter builder
- weapon match lines
- guide rule lines
- task template builder

### `asset_writers/sensors.py`

负责写：

- `.ai/sensors/verification.md`
- `.ai/sensors/test-strategy.md`

同时拥有：

- verification sensor Markdown builder
- test strategy Markdown builder
- missing sensor lines

### `asset_writers/skills.py`

负责复制：

- `.ai/skills/lightweight/SKILL.md`
- `.ai/skills/bugfix/SKILL.md`

### `asset_writers/candidates.py`

负责写：

- `.ai/experience/pending-improvements.md`
- `.ai/experience/weapon-library-candidates.yaml`
- `.ai/review/llm-enhancement-candidates.md`
- `.ai/review/candidate-guides.md`
- `.ai/review/candidate-sensors.md`

## 调用顺序

`write_initial_assets` 调用顺序保持当前语义：

1. 准备 `ai`、config、weapon selection、scan metadata、context inputs、questionnaire、enhancement candidates。
2. 写 weapon-selection trace event。
3. 写 asset-write started trace event。
4. 写 core assets。
5. 写 human confirmation assets。
6. 写 human-confirmation completed trace event。
7. 写 reports。
8. 写 guides。
9. 写 sensors。
10. 写 skills。
11. 写 candidates。
12. 写 asset-write completed trace event。
13. 返回 `.ai` 路径。

## 测试策略

已有 `tests/unit/test_write_assets.py` 作为整体行为基线，重构后必须保持通过。

新增单元测试：

- `tests/unit/test_asset_writer_core.py`
- `tests/unit/test_asset_writer_guides.py`
- `tests/unit/test_asset_writer_sensors.py`
- `tests/unit/test_asset_writer_reports.py`
- `tests/unit/test_asset_writer_candidates.py`
- `tests/unit/test_asset_writer_skills.py`

每类 writer 测试至少断言：

- 文件路径。
- 关键字段或章节。
- artifact kind。

不要为每个私有 helper 写脆弱测试。测试应围绕 writer 的公开函数。

## 非目标

本次不做：

- context 深度参与生成。
- candidate 晋升。
- interactive CLI。
- benchmark 质量评分。
- 文件格式调整。
- 新增产物。

## 完成标准

- `write_initial_assets` 对外签名保持兼容。
- 默认回归测试通过。
- `scripts/test-fast.sh` 通过。
- `tests/unit/test_write_assets.py` 通过。
- 新增 writer 单元测试通过。
- `tests/integration/test_init_on_fixture_projects.py` 通过。
- `tests/e2e/test_fixture_end_to_end.py` 通过。
- `docs/todos/asset-writer-refactor.md` 标记为 implemented 并记录结果。

