# 目标模式运行手册

本文是 Codex/GPT 在目标模式下持续演进 Harness Builder 的运行手册。它沉淀稳定执行原则、选题策略和节奏控制，用于减少目标提示词长度，并避免每轮重复口头约定。

`Goal Mode Playbook` 比“提示词”更合适：提示词是一次性输入，运行手册是可版本化、可审查、可持续更新的团队工作方式。

## 每轮读取顺序

每轮目标模式开始时，先读取：

1. `AGENTS.md`
2. `README.md`
3. `docs/strategy/README.md`
4. `docs/strategy/goal-mode-playbook.md`
5. 与当轮改动相关的 `docs/engineering/` 专题文档
6. 与当轮方向相关的 North Star / todo / 已有 spec / plan

不要用上一轮记忆替代当前文件。文件内容冲突时，以当前代码、`AGENTS.md`、`docs/engineering/` 和 `docs/strategy/` 的最新事实为准，并在 spec 中记录取舍。

## 选题原则

1. 每轮选择新 milestone 前，先检查 `docs/todos/` 中未完成事项。
2. 如果 open todo 符合当前 North Star 和用户最新优先级，优先消化 todo。
3. 只有没有合适 todo 时，才从新的 Current State Gap Analysis 中新增话题。
4. milestone 必须写成用户故事或工程信任故事，说明角色、真实场景、完整动作、独立价值。
5. 技术债、契约 hardening、测试或重构也必须说明保护的用户工作流和降低的风险。

## Milestone 粒度

milestone 的边界是完整用户价值，不是最小代码改动。

应该合并的情况：

- 同一 todo 下的多个小问题服务同一个用户故事。
- 它们共享同一条数据流或同一个 CLI 旅程阶段。
- 可以在一次 spec / plan / TDD 中清楚验收。
- 合并后仍能在一个小型 commit 组内完成。

应该拆分的情况：

- 跨越不同用户旅程，例如首次 init 和已有 Harness 维护入口。
- 需要不同验收语义，例如 CLI transcript、schema 迁移、benchmark 策略分别独立。
- 会触碰高风险 schema / prompt / benchmark / runtime 契约迁移。
- 范围变成“顺手把相关东西都重构一下”。

经验规则：一个 milestone 可以包含 2-4 个紧密相关的小修复，但必须围绕一个可讲清楚的用户故事。

## Superpowers 使用方式

目标模式仍遵循 Superpowers 的工程纪律，但不把流程成本浪费在过小切片上。

- brainstorming：用于形成当轮 spec，但自动目标模式下不等待用户确认；把 assumptions / decisions / risks 写入 spec。
- writing-plans：用于多步骤实现计划；计划应具体到文件、测试和命令。
- test-driven-development：生产行为变更先写失败测试，再实现。
- systematic-debugging：测试失败或行为异常时先定位根因，不降低断言。
- verification-before-completion：完成前必须用命令结果证明，而不是凭感觉宣称完成。
- requesting-code-review：较大、高风险或跨模块改动后使用。

如果只是沉淀稳定流程规则或文档索引，可以保持轻量，不为避免小成本而制造更大的过程文档。

## Sub Agent 使用

有可用 sub agent 时，优先用于并行的只读调研和风险审查：

- 代码路径定位
- 测试覆盖审查
- gap analysis 交叉验证
- 方案边界审查
- 高风险改动的独立 review

主线程负责拆分边界、整合结论、避免冲突编辑、最终验证和提交。子代理不应重复主线程正在做的阻塞工作。

## 提交与 Push 节奏

本地 commit 可以按独立切片或阶段性检查点创建；push 不跟随每个 commit。

- 创建本地 commit 前运行 `scripts/test-fast.sh`。
- 一个 todo / 工作包可以包含多个本地 commit。
- 只有完整 todo、完整工作包或已经产生独立用户价值的功能批次完成后，才统一考虑 push。
- push 前必须运行 `scripts/test-full.sh`。
- 降低 push 频率不豁免 push 前全量验证，只减少触发次数。

## Self-Harness Gate

每轮完成后检查：

- 长期文档是否需要更新。
- init North Star 是否被服务。
- `docs/todos/` 是否需要新增、更新或归档。
- fixture / integration / e2e / acceptance / benchmark 是否需要补齐。
- `.ai` 资产 schema、章节和跨文件引用是否有测试覆盖。
- CLI transcript、成熟度叙事、用户输入消费链路、生成前 preview 是否有验收缺口。
- 是否存在重复代码、边界混乱、规则散落或只断言文件存在的测试。
- sub agent 使用是否充分。

Gate 缺口若影响后续迭代质量，优先作为下一轮 milestone；若很小且与当前轮强相关，可当前轮补齐；若较大，记录到 `docs/todos/`。

## 目标提示词精简建议

目标模式提示词可以只保留：

- 当前大目标和授权边界。
- 必须读取 `AGENTS.md`、`README.md`、`docs/strategy/README.md` 和本手册。
- 本轮优先级或最新用户指令。
- 停止条件和权限边界。

稳定执行规则、粒度策略、提交 / push 节奏和 Gate 细节应优先沉淀到本文件，而不是不断塞回目标提示词。
