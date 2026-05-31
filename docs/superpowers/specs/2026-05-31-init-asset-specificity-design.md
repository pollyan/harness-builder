# Init 资产仓库特异性增强设计

## 背景

当前 `init` 已经能在 guided 模式中展示扫描发现、成熟度初评和用户补充影响，但写入后的正式语义资产仍偏模板化：

- `.ai/guides/project-context.md` 主要记录模块和证据，验证命令与风险区域表达不足。
- `.ai/sensors/verification.md` 只消费 `CommandCatalog` 和 weapon selection，缺少模块、风险区域和成熟度缺口上下文。
- `.ai/init-summary.md` 只消费 `MaturityReport`，没有把本仓库关键模块、风险区域、验证入口和用户补充串成初始化交付摘要。

这会让用户在完成 guided init 后难以确认自己的补充是否真正影响了 Harness 资产。

## 用户故事

作为 Harness Maintainer，当我在 `init` 中补充或确认模块、风险区域、验证命令和团队规则后，我希望在正式生成的 `project-context.md`、`verification.md` 和 `init-summary.md` 中看到这些信息如何进入 Harness 资产并关联成熟度缺口，从而确认生成结果是面向当前仓库定制，而不是模板拼装。

## 目标

本切片只增强首次 `init` 产物深度，不引入新的机器消费 schema，不改变 workflow routing policy，也不自动应用 review-only candidate。

必须做到：

- `project-context.md` 保留现有稳定章节，并新增风险区域、验证入口和成熟度缺口关联叙事。
- `verification.md` 保留现有稳定章节，并新增风险与验证映射、成熟度缺口关联叙事。
- `init-summary.md` 保留现有稳定章节，并新增本仓库关键事实、本次吸收的用户补充、资产如何补齐缺口。
- guided init 中结构化补充的 `module`、`command`、`risk` 能出现在上述正式资产中。
- 非交互 `init` 路径继续兼容，缺少用户补充时显示明确的“未提供/未确认”语义，而不是静默忽略。

## 非目标

- 不改 LLM 扫描 prompt。
- 不改成熟度评分规则。
- 不改 benchmark 的质量评分口径；仅通过现有质量检查和新增生成测试约束本次行为。
- 不生成 `.ai/task-runs`，也不把 Runtime 过程数据写入 Builder。

## 设计

`write_initial_assets()` 作为编排层，把已经存在的 `inventory`、`commands` 和 `interaction_decisions` 传给语义资产 writer。

`guides.py` 增加只读渲染辅助函数：

- 从 `inventory.modules` 渲染关键模块。
- 从 `inventory.stack_extensions.risk_areas` 渲染风险区域。
- 从 `commands.commands` 渲染验证入口。
- 从 `interaction_decisions` 渲染用户 scan/team/workflow 补充。
- 根据风险、命令、用户补充生成简短成熟度缺口关联。

`sensors.py` 增加可选 `inventory` 参数，用于把风险区域映射到验证策略：有风险区域时说明命中这些路径应优先运行 hard gate 或记录 skipped/人工下一步；无风险区域时说明当前扫描未确认风险路径。

`init_summary.py` 增加可选 `inventory`、`commands`、`interaction_decisions` 参数，用同一批事实生成初始化交付摘要。`assess` 继续可以只传 `score`，因此这些新章节在没有上下文时显示保守占位，不破坏维护入口。

## 验收

- 单元测试覆盖 guide/sensor/init-summary 对模块、风险、命令、用户补充和成熟度缺口关联的渲染。
- 集成测试覆盖 guided init 的结构化补充能进入 `project-context.md`、`verification.md` 和 `init-summary.md`。
- `scripts/test-fast.sh` 通过后才提交。
- push 前运行 `scripts/test-full.sh`。
