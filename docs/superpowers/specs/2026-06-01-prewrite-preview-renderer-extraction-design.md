# Prewrite Preview Renderer Extraction 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`src/harness_builder_agent/tools/interactive_init.py`、`tests/unit/test_interactive_init_preview.py`、`tests/integration/test_init_on_fixture_projects.py` 和最新演进记录。
- 按需未展开：LLM contracts、sensor / gate 专题。本轮不改 LLM、Sensor、benchmark 或机器消费 schema。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 写入前预览渲染抽模块并补直接 unit | Self-Harness Gate / 架构规则 | 写入前 maturity preview / scan supplement / team rules / workflow notes / Guide / Sensor / routing 预览可以在独立模块中维护和单测，主向导只负责编排 | 预览功能已完整，但渲染函数、scan supplement section、weapon maturity helper 全在 `interactive_init.py`，测试主要靠 integration transcript 和少量 helper unit | 后续每次调整 preview 都要改主向导大文件并依赖较慢集成测试定位；模块边界不利于继续打磨 init 第一性体验 | 降低后续 init 体验迭代成本，保护“用户补充 -> 设计预览 -> 确认写入”关键旅程 | 中低；行为等价重构，需避免 CLI transcript 漂移和 circular import | 新 unit 直接调用新 renderer helper；完整 guided init integration 防行为漂移 | 依赖现有 `GuidedScanOverrides`、maturity model、weapon selection schema | 新模块 unit 通过；existing integration 仍通过；`interactive_init.py` 行为等价 | 本轮 |
| B. push / full regression 同步远端 | Gate / git 状态 | 本地 ahead 提交形成完整工作包后通过 full regression 并 push | 本地 `main` 已 ahead 33，fast regression 可通过 | full regression 需要真实 DeepSeek key 和 `.benchmarks` 真实仓库 | 降低长期分叉风险 | 外部前置，不适合作为本地实现 milestone | `scripts/test-full.sh` 与 push 结果 | `DEEPSEEK_API_KEY`、网络、真实仓库 | full 通过并 push | 外部前置候选 |
| C. 首次 init maturity preview 叙事继续强化 | init North Star | maturity preview 更清楚把“当前 L0、写入后基线、下一等级差距、用户补充影响”串成一段用户可读叙事 | 当前已有 L0/L1、planned baseline、blockers、next steps 和设计预览 | 叙事仍分散在多个 section，后续可进一步统一 | 提升首次初始化体验 | 低到中；主要 CLI 文案但需防过长 | integration transcript | 依赖当前 preview renderer | 下一轮候选 |

排序结论：

1. 选择 A。连续多轮都在修改写入前预览和已有 Harness 维护入口，`interactive_init.py` 已承载过多 UI 渲染细节；抽出 prewrite preview renderer 是保护后续 init North Star 迭代的工程信任故事。
2. B 受外部凭证和真实仓库前置影响，本轮不选。
3. C 是用户体验增强，但在继续加文案前先把预览渲染边界收窄，后续改起来更稳。

本轮 milestone：

作为 Harness Builder 维护者，当我继续打磨首次 guided `init` 的写入前成熟度与设计预览时，我可以在独立的 prewrite preview renderer 模块中修改和单测 scan 补充、团队规则、Workflow 补充、Guide / Sensor 推荐和 routing 预览，从而降低修改主向导编排文件的风险，并让后续体验迭代更快、更可审查。

## 验收标准

1. 新增独立模块承载 `GuidedScanOverrides`、写入前预览渲染、scan supplement preview、weapon maturity helper 和 partial Harness 判断。
2. `interactive_init.py` 只调用新模块，不再内联 `_show_prewrite_maturity_preview()`、`_show_scan_supplement_preview_section()`、`_show_weapon_preview_item()`、`_weapon_*()` 和 `_has_existing_partial_harness()` 的实现。
3. 新 unit 测试直接验证 scan supplement preview 在有补充和无补充时的输出，不依赖完整 guided init integration。
4. 既有从 `interactive_init.py` 导入 helper 的 unit 测试保持兼容，或同步迁移到新模块。
5. 用户可见 CLI transcript 行为不变：目标 integration 和完整 guided init integration 通过。
6. 不修改 `.ai` schema、不改正式资产生成、不改 Runtime 边界。
7. 完成前运行新/相关 unit、目标 integration、完整 guided init integration、`git diff --check` 和 `scripts/test-fast.sh`。

## 决策与取舍

- 本轮是行为等价重构，不借机调整 preview 文案或成熟度算法。
- 新模块仍使用 `typer.echo`，保持现有 CLI 输出机制；不引入复杂渲染抽象。
- 为兼容现有测试，可以从 `interactive_init.py` 重新导出部分 helper 名称，但实现来源应在新模块。

## Assumptions / Risks

- Assumption：先抽出 prewrite preview 这条边界，比整体拆分 `interactive_init.py` 更小且更容易验收。
- Risk：`interactive_init.py` 仍然很大；本轮只降低一个高频修改区域的复杂度，完整拆分仍作为后续候选。
- Sub agent：按目标模式尝试使用 sub agent，但当前会话此前多次返回 agent thread limit；若本轮仍不可用，在演进记录中说明。
