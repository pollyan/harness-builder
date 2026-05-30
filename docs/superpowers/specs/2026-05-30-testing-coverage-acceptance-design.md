# Testing Coverage and Acceptance Strategy Design

## 目标

系统性补强 Harness Builder 当前测试覆盖，重点保护后续 Asset Writer 拆分、大仓库 Evidence 增强、交互式 CLI 和 Benchmark 评分改造。

本设计只处理测试覆盖、验收脚本和测试文档策略，不改变核心业务行为。

## 当前状态

当前默认测试：

```text
unit: 28
integration: 9
e2e: 1
default total: 38
acceptance: 2 extra
```

当前默认测试能覆盖主要 happy path，但缺少足够失败路径和边界用例。

当前 hooks：

- `pre-commit` 运行默认回归。
- `pre-push` 运行默认回归。
- `post-commit` 提醒推送后检查 CI。

当前 acceptance：

- `tests/acceptance/test_real_llm_scan.py`
- `tests/acceptance/test_real_repositories_e2e.py`

Acceptance 不在默认 pytest 中运行。

## 设计原则

### 不追求固定覆盖率

第一版不设置 coverage 百分比目标。目标是覆盖高风险行为和失败路径。

### 保持快速回归可用

默认测试仍应快速运行，继续适合 pre-commit 和 CI。

### Acceptance 显式运行

真实 DeepSeek 和真实开源仓库验收应通过单独脚本显式运行。缺少 API key 或真实仓库时必须失败，不 skip。

### 测试断言要深

新增测试不能只断言文件存在，必须检查 schema、关键字段、关键章节、跨文件引用或失败原因。

## 新增测试分组

### 1. CLI 契约测试

目的：修正当前 CLI 测试命名漂移，并覆盖核心命令可见性和 `init` 默认当前目录行为。

新增或修改：

- `tests/unit/test_cli_import.py`
- `tests/integration/test_init_on_fixture_projects.py`

覆盖场景：

- CLI help 暴露 `init`、`run`、`benchmark`、`assess`、`improve`。
- `init --repo <path>` 仍然可用。
- `init` 不传 `--repo` 时默认使用当前工作目录。

说明：`init` 默认当前目录会改变 CLI 行为，因此该测试会先失败，后续实现应修改 CLI 参数默认值。

### 2. Schema 正反例测试

目的：补齐机器消费输出的 schema 防线。

新增或扩展：

- `tests/unit/test_schema_contracts.py`

覆盖 schema：

- `BenchmarkReport`
- `HarnessMap`
- `SensorReport`
- `MaturityReport`
- `ImprovementCandidateReport`
- `WeaponLibrarySelection`
- 现有 `ProjectInventory`
- 现有 `CommandCatalog`
- 现有 `HarnessConfig`

覆盖场景：

- 合法最小对象可通过。
- 缺少关键字段会失败。
- 非法 enum 会失败。
- workflow skill path、sensor result status、candidate confirmation 字段符合预期。

### 3. Weapon Library 单元测试

目的：让内置武器库选择逻辑有直接测试，不再只依赖 init/benchmark 间接覆盖。

新增：

- `tests/unit/test_weapon_library.py`

覆盖场景：

- Java Spring 选择 `common` + `java-spring`。
- .NET ASP.NET 选择 `common` + `dotnet-aspnet`。
- unknown stack 至少选择 `common`。
- guide weapon id 和 sensor weapon id 与 selected stacks 一致。
- selection source 是 `built_in_weapon_library`。

### 4. Write Assets 行为测试

目的：在拆分 `write_assets.py` 前建立行为基线。

新增：

- `tests/unit/test_write_assets.py`

覆盖场景：

- `write_initial_assets` 生成核心机器消费文件。
- 生成 guide 必需章节。
- 生成 sensor 必需章节。
- 生成 workflow skill 并保持路径可引用。
- trace artifact 记录关键产物。
- context 输入能进入 context/human confirmation 产物。
- LLM enhancement candidates 以 candidate 状态落盘。

这些测试允许使用小型 `ProjectInventory` 和 `CommandCatalog`，不依赖真实 LLM。

### 5. Benchmark 失败路径测试

目的：确保 benchmark 能暴露坏产物，而不是只验证 happy path。

扩展：

- `tests/integration/test_benchmark_command.py`

覆盖场景：

- 缺少必需文件时 benchmark failed。
- schema 损坏时 benchmark failed。
- guide 必需章节缺失时 benchmark failed。
- workflow skill 引用路径不存在时 benchmark failed。
- hard gate sensor failed/skipped 时 benchmark failed 并给出摘要。

实现建议：

- 复用 fixture repo。
- 先生成完整 `.ai`。
- 人为删除或破坏某个产物。
- 直接调用 benchmark 或 CLI 检查报告。

### 6. Run Task 边界测试

目的：让 runtime workflow 在 sensor 和资产缺失场景下有明确行为。

扩展：

- `tests/integration/test_task_run_workflow.py`

覆盖场景：

- sensor 返回 `failed` 时写入 `sensor-report.yaml` 和 `runtime-summary.yaml`。
- sensor 返回 `skipped` 时不伪装成 passed。
- command catalog 为空时 sensor policy 为空或明确无 hard gate。
- workflow skill 文件缺失时行为明确失败或报告缺失。
- guide 文件缺失时 `used-guides.yaml` 标记 `exists=false`。

### 7. Assess / Improve 边界测试

目的：补齐成熟度和改进候选生成的非 happy path。

扩展：

- `tests/integration/test_assess_improve_commands.py`

覆盖场景：

- command catalog 为空时 maturity 降级但仍能生成报告。
- 缺少 runtime trace 时 improve 仍能生成待确认候选或明确失败。
- improvement candidate 必须包含 `human_confirmation_required=true`。
- suggested target 必须位于 `.ai/` 下。

### 8. Acceptance 脚本和文档

目的：明确本地快速回归、完整本地验收、真实仓库验收之间的区别。

新增脚本：

- `scripts/test-fast.sh`
- `scripts/test-acceptance.sh`
- `scripts/test-full.sh`

脚本行为：

```bash
scripts/test-fast.sh
  -> .venv/bin/python -m pytest -q

scripts/test-acceptance.sh
  -> .venv/bin/python -m pytest tests/acceptance -q

scripts/test-full.sh
  -> scripts/test-fast.sh
  -> scripts/test-acceptance.sh
```

缺少 `.venv/bin/python` 时，脚本可回退到 `python`，但输出中必须说明使用的解释器。

文档更新：

- `README.md`
- `docs/engineering/testing-strategy.md`

说明：

- pre-commit/pre-push 默认跑 fast。
- full 用于发布前、目标模式完成前或 scan/LLM/acceptance 相关改动后。
- acceptance 缺 key 或缺 `.benchmarks` 时失败，不 skip。

## 不做的事情

- 不引入 coverage 工具。
- 不把 acceptance 放入默认 GitHub Actions。
- 不实现新的业务行为，除了 `init` 默认当前目录这个已经确认的 CLI 契约改进。
- 不重构 `write_assets.py`。
- 不修改 benchmark report 评分结构。

## 完成标准

子项目完成时必须满足：

- 默认测试数量明显高于 38，并覆盖上述关键模块。
- `scripts/test-fast.sh`、`scripts/test-acceptance.sh`、`scripts/test-full.sh` 可运行。
- `init` 支持不传 `--repo` 时扫描当前目录。
- 新增测试均能通过。
- README 和测试策略文档与脚本行为一致。
- `.venv/bin/python -m pytest -q` 通过。

如果执行完整验收：

```bash
scripts/test-full.sh
```

缺少 DeepSeek key、真实仓库或网络失败时，必须明确报告，不能当作成功。

## 实施顺序

1. CLI 契约测试和 `init` 默认当前目录。
2. Schema 正反例测试。
3. Weapon Library 单元测试。
4. Write Assets 行为测试。
5. Benchmark 失败路径测试。
6. Run Task 边界测试。
7. Assess / Improve 边界测试。
8. Acceptance 脚本和文档。

该顺序从低风险、强保护网开始，逐步覆盖高层链路。

