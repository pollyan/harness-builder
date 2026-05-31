# Guided Init 启动边界说明设计

## 用户故事

作为首次使用 Harness Builder 的 Harness Maintainer，当我运行默认 guided `init` 时，我希望在等待仓库扫描之前先看到本次流程会扫描什么、需要我确认什么、会生成什么、不会执行什么，以及何时才会写入正式 Harness 资产，这样我可以在进入耗时扫描前理解流程边界和预期产出。

## 当前问题

当前 guided `init` 在首次初始化时只输出：

- Harness Builder 将生成一套可审查、可继续修改的 `.ai` 资产。
- 目标仓库路径。
- `继续生成 Harness?`

随后才进入扫描阶段。用户在确认继续之前还不知道：

- 扫描会覆盖哪些 evidence。
- 后续需要确认哪些关键判断。
- 写入后会生成哪些 Harness 资产。
- 本次不会执行 Runtime、不创建 `.ai/task-runs`、不默认运行 benchmark。
- 正式资产只会在最终 `confirm` 后写入或覆盖。

这与 `docs/strategy/init-north-star.md` 中“启动与目标说明”的目标态不一致。

## 设计决策

首次 guided `init` 在确认继续之前增加稳定的 `== 启动说明 ==` 区块。

该区块只服务首次初始化或用户显式 `reinit` 后的生成向导；已有 Harness 的维护入口仍优先展示维护状态和动作，不追加首次初始化交付语义。

启动说明使用中文短列表，覆盖五类信息：

1. 将扫描仓库文件、构建配置、CI、测试、文档和源码样本证据。
2. 后续需要用户确认或补充技术栈、模块边界、风险区域、验证命令、团队规则和 Workflow 说明。
3. 最终确认写入后将生成 project inventory、command catalog、Guides、Sensors、Workflow Skills、成熟度报告和待确认项。
4. 本次不会执行 Runtime，不会创建 `.ai/task-runs`，不会默认运行 benchmark。
5. 在最终输入 `confirm` 前，不会写入或覆盖正式 Harness 资产；generation trace 可以从会话开始记录取消、失败和完成过程，但不属于最终确认后才开始生成的正式 Harness 资产。

## 范围边界

本轮只增强启动前 CLI 说明，不改变扫描、LLM 调用、资产 schema、成熟度评分、写入逻辑或已有 Harness 维护动作。

本轮不引入颜色、交互式菜单、立即运行 benchmark 选择，也不修改非交互 `--non-interactive` 输出语义。

## 验收标准

- 默认 guided `init` 首次初始化时，在 `扫描仓库` 之前输出 `== 启动说明 ==`。
- 启动说明包含扫描范围、用户确认范围、生成资产范围、Runtime / `.ai/task-runs` / benchmark 边界、最终 `confirm` 前不写入或覆盖正式资产。
- `--non-interactive` 路径不输出 `== 启动说明 ==`。
- 现有 guided happy path 仍能完成初始化，并保留扫描进度、成熟度初评、写入前预览和完成摘要。

## 风险与取舍

启动说明如果过长会增加用户阅读负担，因此本轮采用短列表，不展开所有文件名和底层 schema。

“不写入或覆盖正式资产”指生成向导最终确认前的边界；运行过程中仍会读取仓库和已有 `.ai` 状态，并记录 generation trace 用于审计取消、失败和完成结果，正式 Harness 资产写入仍发生在最终 `confirm` 后。

## Self-Harness Gate

本轮改善 `init` 用户旅程中的第一步：启动与目标说明。用户可见价值是进入耗时扫描前理解流程边界，降低误以为 Builder 会执行 Runtime、创建任务运行产物、默认 benchmark 或提前覆盖资产的风险。
