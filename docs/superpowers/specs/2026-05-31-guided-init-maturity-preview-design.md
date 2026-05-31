# Guided Init 写入前成熟度预览设计

## 当前状态与差距分析

North Star 要求 `init` 在扫描理解后立即进入成熟度初评和差距解释，并在正式写入 `.ai/` 前展示 maturity-driven Harness 设计预览。当前 guided `init` 已经能扫描、收集用户补充、审查候选、写入资产和输出最终摘要，但成熟度叙事主要发生在写入完成之后。用户在输入 `confirm` 前看不到当前仓库从 L几起步、写入后预计建立什么 Harness 基线、下一阶段缺口是什么，也看不到 `standard` workflow 和 routing policy 如何参与高风险任务治理。

候选 gap 排序：

1. 写入前成熟度初评和 Harness 设计预览：直接改善首次 `init` 主旅程，让用户在确认写入前理解价值、边界和差距。
2. 用户自然语言补充后的复述和影响说明：能改善协作感，但依赖更细的输入归类，适合作为下一轮。
3. 扫描阶段进度反馈：能减少等待焦虑，但对生成资产深度和成熟度叙事推进较间接。

本轮选择第 1 项，因为它最贴近用户刚反馈的“init 交互扫描和产出内容深度不足”，并且能用现有 maturity model、weapon library 和 config 契约小步实现。

## 用户故事

作为 Harness Maintainer，当我第一次对一个遗留仓库运行 guided `init`，并准备确认写入 `.ai/` 前，我可以先看到当前仓库的 AI Coding Harness 从 L0 起步、写入后预计建立的成熟度基线、下一等级缺口，以及本次将生成哪些 Guides、Sensors 和 Workflows 来补齐这些缺口，从而在写入前判断这套 Harness 是否值得接管和继续完善。

## 关键决策

- 不提前写入 `.ai/` 文件。预览只在内存中基于扫描结果、命令目录、默认 `HarnessConfig` 和 `select_weapon_library()` 计算。
- 区分“当前状态”和“写入后预计基线”。首次仓库没有正式 `.ai/project-inventory.json` 和 `.ai/harness-config.yaml` 时，当前 Harness 成熟度明确从 L0 起步；预览中的 planned maturity 使用现有 `build_maturity_report(ai=None, ...)` 说明写入后预计建立的基线。
- 预览必须发生在“最终确认”之前，避免把写入后的交付摘要伪装成交互式确认。
- 预览优先使用 L0-L4 语言解释整体成熟度；维度评分只作为支撑说明，不直接把 schema 字段当主界面。
- Workflow 预览必须包含 `lightweight`、`bugfix` 和 `standard`，并解释 routing rule 如何根据 bugfix intent、低风险和高风险升级选择工作流。
- 本轮不实现扫描阶段 progress callback、不重构 scan pipeline、不增强自然语言理解。用户补充后的复述和阶段化扫描进度作为下一轮候选 gap。

## 可执行验收标准

- guided `init` happy path 输出中，`当前 Harness 成熟度初评` 出现在 `最终确认` 之前。
- 首次仓库预览明确说明当前从 `L0` 起步，写入后预计建立某个 L1/L2 基线，并展示下一目标等级。
- 预览展示主要阻断项和推荐补齐动作，且不直接暴露 `primary_stack` 这类内部字段。
- 预览展示将生成的 Guides、Sensors 和 Workflow routing，至少包含 `standard` workflow 及其高风险升级语义。
- 写入后的 `.ai/` 产物、schema、trace、`interaction-decisions.yaml` 和现有 guided happy path 保持通过。
- 文档同步说明：首次 guided `init` 应在写入前展示成熟度初评和设计预览。

## 假设与风险

- `build_maturity_report(ai=None, ...)` 表示“按当前扫描结果写入后预计形成的 Harness 基线”，不是当前仓库已经具备的 Harness 成熟度。因此 CLI 必须同时显示当前 L0 和 planned baseline，避免误导。
- 当前 preview 只消费结构化修正后的 inventory / commands；自然语言补充已经进入后续资产，但本轮不做更细语义归因。
- 如果用户在最终确认阶段返回修改 scan，本轮会刷新武器库选择和候选报告，并让最终确认前的 preview 基于当前 inventory / commands 重新渲染；已做出的候选审查决策仍保持用户原选择，不在本轮自动重问。
