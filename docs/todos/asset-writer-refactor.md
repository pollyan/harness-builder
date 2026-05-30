# Asset Writer 拆分重构

## 状态

- 状态：open
- 优先级：medium
- 发现日期：2026-05-30
- 相关模块：`src/harness_builder_agent/tools/write_assets.py`
- 相关工程规则：`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`

## 背景

当前 `write_assets.py` 承担了 `init` 资产生成的大部分职责。POC 阶段这种集中实现有利于快速打通链路，但随着 guide、sensor、context、candidate、benchmark、interactive 等能力增加，该文件会越来越难维护。

当前文件已经同时处理机器消费产物、Markdown 报告、guide、sensor、workflow skill、human confirmation、LLM enhancement candidate、artifact 记录和多个私有 Markdown builder。

## 当前现状

当前 `write_assets.py` 负责：

- 写 `.ai/project-inventory.json`。
- 写 `.ai/command-catalog.yaml`。
- 写 `.ai/harness-config.yaml`。
- 写 `.ai/scan-metadata.yaml`。
- 写 `.ai/llm-scan-proposal.json`。
- 写 `.ai/weapon-library-selection.yaml`。
- 写 context、questionnaire、human input。
- 写 scan report、maturity report、maturity score、evolution plan。
- 写 guides 和 task templates。
- 写 sensors。
- 复制 workflow skills。
- 写 pending improvements 和 LLM enhancement candidate review 文件。
- 记录 trace artifacts。

## 问题

当前主要问题：

- 单文件职责过多。
- 修改 guide 生成逻辑可能影响 sensor 或 report。
- 单元测试难以精准覆盖各类 writer。
- 未来交互式确认、context 深度参与生成、candidate 晋升都会继续加重该文件。
- Markdown 生成函数和文件写入编排混在一起。

## 理想拆分

未来可以拆成：

```text
src/harness_builder_agent/tools/write_assets.py
  只负责编排和向后兼容入口

src/harness_builder_agent/tools/asset_writers/core.py
  inventory / command catalog / config / metadata

src/harness_builder_agent/tools/asset_writers/guides.py
  guides / task templates

src/harness_builder_agent/tools/asset_writers/sensors.py
  verification / test strategy

src/harness_builder_agent/tools/asset_writers/reports.py
  scan report / maturity / evolution

src/harness_builder_agent/tools/asset_writers/human_confirmation.py
  context inputs / questionnaire / human input

src/harness_builder_agent/tools/asset_writers/candidates.py
  LLM enhancement / weapon library candidates / review assets

src/harness_builder_agent/tools/asset_writers/skills.py
  workflow skill copy
```

## 初步验收标准

未来实现该 todo 时，至少应满足：

- `write_initial_assets` 对外签名保持兼容。
- 产物路径和内容不出现无意变化。
- 每类 writer 有独立单元测试。
- integration/e2e 继续通过。
- trace artifact 记录不丢失。
- 拆分后文件职责清晰，不出现新的大杂烩模块。

## 非目标

第一版不要求：

- 改变生成产物格式。
- 改变 `init` CLI 行为。
- 顺手实现 interactive 或 candidate 晋升。

这是重构任务，应以行为不变为基本原则。

