# Todo Implementation Roadmap Design

> 历史说明：本路线图记录 2026-05-30 当时的 active todo 集合。当前待办入口以 `docs/todos/README.md` 为准。

## 目标

将 `docs/todos/` 中积累的 5 个 open todo 拆解为一组可按 Superpowers 流程逐个推进的子项目，明确每个子项目的边界、依赖顺序、完成标准和验证方式。

本设计不是功能实现计划；它是后续 spec、implementation plan 和 TDD 实施的总控路线图。

## 当前 Todo 范围

当前 active todo：

1. `docs/todos/testing-coverage-and-acceptance-strategy.md`
2. `docs/todos/asset-writer-refactor.md`
3. `docs/todos/evidence-depth-for-large-repositories.md`
4. `docs/todos/interactive-guided-cli.md`
5. `docs/todos/benchmark-quality-scoring.md`

这些 todo 共同目标是把 Harness Builder 从“可演示 POC”推进到“更可信、可维护、可交互、可验收的 CLI Agent”。

## 总体拆分原则

每个 todo 必须独立升级为一个子项目，并按以下流程推进：

1. 使用 `superpowers:brainstorming` 完善需求和设计。
2. 写入 `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`。
3. 使用 `superpowers:writing-plans` 生成 implementation plan。
4. 使用 TDD 执行，每个行为变化先写失败测试。
5. 小步提交，每个提交聚焦一个可验证变化。
6. 完成后运行对应测试和默认回归。

不要把 5 个 todo 合并成一个大型实现分支。

## 推荐执行顺序

```text
1. 测试覆盖深度与 Acceptance 策略增强
2. Asset Writer 拆分重构
3. 大仓库 Evidence 扫描深度增强
4. 全局交互式 CLI 与强引导式 Harness 生成
5. Benchmark 质量评分细化
```

### 顺序理由

测试覆盖必须先做。当前默认测试只有 38 个，很多失败路径和边界行为没有保护。后续 writer 拆分、evidence schema 增强和 interactive CLI 都会触碰核心链路，如果没有更厚的测试网，重构风险过高。

Asset Writer 拆分应排在交互式 CLI 之前。`write_assets.py` 当前负责过多产物，交互式确认、context 深度参与生成和 candidate 晋升都会继续扩大 writer 复杂度。先拆出清晰边界，可以降低后续功能实现风险。

Evidence 增强应排在交互式 CLI 之前。交互式确认依赖可解释的扫描摘要、coverage、priority 和 missing evidence 信息；如果扫描层仍然只是简单采样，交互流程只能确认薄弱结论。

Benchmark 质量评分应排在后面。它需要利用增强后的 evidence、writer、interactive confirmation 和更完整测试策略，才能成为有解释力的质量评估器。

## 子项目 1：测试覆盖深度与 Acceptance 策略增强

### 范围

补齐当前测试体系中的关键缺口，重点覆盖：

- `write_assets.py` 或拆分前的资产生成行为。
- `benchmark.py` 失败路径。
- `run_task.py` 传感器失败、跳过、缺 guide、缺 skill 等场景。
- `weapon_library.py` 选择逻辑。
- 主要 schema 正反例。
- `init` 默认当前目录运行。
- acceptance 运行策略、脚本和文档。

### 非范围

- 不实现 interactive CLI。
- 不拆分 writer。
- 不增强 evidence schema。
- 不改变 benchmark report 的评分结构。

### 完成标准

- 默认测试数量明显增加，覆盖关键失败路径。
- 新测试能保护后续 writer 拆分。
- README、`docs/engineering/testing-strategy.md`、hooks/脚本策略一致。
- 默认回归通过。

## 子项目 2：Asset Writer 拆分重构

### 范围

将 `write_assets.py` 中不同产物类型的生成逻辑拆成小模块，同时保持外部行为不变。

建议模块：

- `asset_writers/core.py`
- `asset_writers/guides.py`
- `asset_writers/sensors.py`
- `asset_writers/reports.py`
- `asset_writers/human_confirmation.py`
- `asset_writers/candidates.py`
- `asset_writers/skills.py`

### 非范围

- 不改变 `.ai` 产物格式。
- 不新增交互式 CLI。
- 不改变 LLM scan 行为。

### 完成标准

- `write_initial_assets` 对外签名保持兼容。
- 现有 integration/e2e/benchmark 继续通过。
- 每类 writer 至少有对应单元测试或强集成断言。
- trace artifact 不丢失。

## 子项目 3：大仓库 Evidence 扫描深度增强

### 范围

将 evidence collector 从简单文件采样升级为更适合大仓库的可审计扫描输入层。

重点能力：

- 全量轻量索引文件路径和元信息。
- 按语言、模块、目录类型、测试/源码/配置/CI/文档分层采样。
- evidence priority 和 reason。
- scan coverage 信息。
- 截断、跳过、缺失证据的显式记录。

### 非范围

- 不引入向量数据库。
- 不承诺 100% 不遗漏业务细节。
- 不支持所有语言和框架。
- 不实现完整多轮 LLM follow-up，第一版可以只设计 schema 和 coverage 基础。

### 完成标准

- 大仓库 fixture 证明不再只取前 N 个源码文件。
- LLM prompt 能看到 coverage 和 priority 信息。
- `scan-metadata.yaml` 能表达覆盖度和遗漏风险。
- 测试覆盖多模块、测试目录不规范、配置分散等场景。

## 子项目 4：全局交互式 CLI 与强引导式 Harness 生成

### 范围

把 `init` 从纯命令式工具演进为可选的强引导式 CLI。

第一版重点：

- `init` 默认非交互，CI 不阻塞。
- `init --interactive` 进入本地交互流程。
- 阶段性展示扫描摘要。
- 用户可以确认或修正技术栈、模块、命令、风险区域。
- 用户可以输入或确认 context。
- context 真正参与 LLM scan、guide/sensor 生成和 gate 建议。
- guide/sensor candidate 支持接受、拒绝、修改和晋升。
- 人工确认结果结构化落盘，并进入 trace 或 decision log。

### 非范围

- 不做图形界面。
- 不做多人审批。
- 不在 CI 中交互。
- 不一次性改造所有命令。

### 完成标准

- 非交互和交互模式都有测试。
- CI 非 TTY 不会卡住。
- 用户修正能影响最终 Harness。
- candidate 晋升后正式 guide/sensor 产物发生可验证变化。
- context 不再只是记录，而是真正参与生成。

## 子项目 5：Benchmark 质量评分细化

### 范围

将 benchmark 从结构门禁升级为带解释的质量评估。

建议评分维度：

- scan quality
- guide quality
- sensor quality
- command reliability
- workflow trace quality

每项评分必须有扣分原因和建议下一步。

### 非范围

- 不引入额外 LLM 做二次评分。
- 不建立复杂评分模型。
- 不追求绝对客观语义评审。

### 完成标准

- `benchmark-report.yaml` 包含质量评分。
- 评分规则可测试。
- 低质量 guide/sensor/command 会得到 degraded 或 failed 信号。
- README 和测试策略说明评分含义。

## 横向约束

### TDD

所有行为变更必须先写失败测试，验证失败原因正确后再写实现。

### 提交

每个子项目必须小步提交。推荐提交粒度：

- 设计 spec
- implementation plan
- 一组测试
- 对应实现
- 文档更新

### 验证

最低验证：

```bash
.venv/bin/python -m pytest -q
```

涉及真实 LLM、scan、acceptance、发布前验收时，需要显式运行：

```bash
.venv/bin/python -m pytest tests/acceptance -q
```

如果 acceptance 因缺少 API key、真实仓库或网络失败，必须明确说明，不得当作默认通过。

## 风险与处理

### 风险：范围过大

处理：每个 todo 独立 spec 和 plan，不跨子项目混做。

### 风险：交互式 CLI 过早实现导致结构混乱

处理：先补测试，再拆 writer，再增强 evidence，最后做 interactive。

### 风险：测试数量增加但断言仍然浅

处理：测试覆盖子项目必须明确断言字段、章节、schema、失败路径和跨文件引用。

### 风险：benchmark 评分变成主观文本

处理：评分规则必须可测试，第一版使用确定性规则，不引入 LLM 二次评分。

## 下一步

第一个进入详细设计的子项目是：

`docs/todos/testing-coverage-and-acceptance-strategy.md`

原因：它是后续所有重构和功能改造的保护网。
