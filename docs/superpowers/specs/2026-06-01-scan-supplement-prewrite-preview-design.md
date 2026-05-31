# Scan Supplement Prewrite Preview 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`src/harness_builder_agent/tools/interactive_init.py`、`tests/integration/test_init_on_fixture_projects.py`、`tests/unit/test_interactive_init_preview.py` 和最新演进记录。
- 按需未展开：LLM contracts、sensor / gate 专题和架构专题。本轮不修改 LLM、benchmark、sensor、schema 或目录结构。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. scan 补充进入写入前设计预览 | init North Star / 上轮 Gate | 用户在写入前预览中能看到本轮 scan 补充如何作为 Harness 设计输入影响 project inventory、command catalog、risk hints、Guides、Sensors、Workflow 升级和人工确认 | scan 补充会即时复述、更新内存态 inventory / command catalog，并在最终确认摘要中展示影响 | `写入前 Harness 设计预览` 只展示团队规则约束和 Workflow 补充约束，没有专门展示 scan 补充约束；用户需要从后续 Guide / Sensor 列表间接推断补充已进入设计 | 补齐“用户补充 -> 设计预览 -> 确认写入”的可见闭环，提升渐进式协作可信度 | 低；只调整 CLI preview 文案和参数传递，不改产物 schema 或正式资产生成 | integration CLI transcript 覆盖 scan 补充 section；返回 scan 替换场景覆盖最终 preview 只显示当前补充 | 依赖现有 `GuidedScanOverrides`、`_scan_state_with_overrides()` 和 guided init tests | preview 中出现 `扫描补充约束`、模块 / 命令 / 风险 / 自然语言补充和影响说明；无补充时明确按扫描基线生成 | 本轮 |
| B. push / full regression 同步远端 | Gate / git 状态 | 本地 ahead 提交形成完整工作包后通过 full regression 并 push | 本地 `main` 已 ahead 32，fast regression 可通过 | full regression 需要真实 DeepSeek key 和 `.benchmarks` 真实仓库 | 降低长期分叉风险 | 外部前置，不适合作为本地实现 milestone | `scripts/test-full.sh` 和 push | `DEEPSEEK_API_KEY`、网络、真实仓库 | full 通过并 push | 外部前置候选 |
| C. `interactive_init.py` 过大导致维护风险 | Self-Harness Gate / 技术债 | guided init 的状态、渲染和动作处理更易审查、测试和演进 | 当前已有大量单元和集成覆盖，但文件聚合了扫描展示、维护入口、candidate apply、human input、preview 等多类职责 | 后续每个 init 小功能都要改同一大文件，冲突和认知成本上升 | 降低后续目标模式迭代成本 | 中；重构需要保持大量 transcript 不漂移 | 全量 guided init integration、unit、diff review | 需要先设计模块边界 | 重构后行为等价且测试全绿 | 下一轮候选 / todo 候选 |

排序结论：

1. 选择 A。它直接服务 `init-north-star.md` 的“渐进式协作”和“成熟度驱动的 Harness 设计预览”：用户补充应在确认写入前被作为设计输入显式展示，而不是只在即时复述或最终摘要出现。
2. B 受外部凭证和真实仓库前置影响，本轮不选。
3. C 有工程价值，但不是直接用户旅程；在当前仍能小步推进 init 体验时，不先做较大重构。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 中补充或修正技术栈、模块、验证命令、风险区域或自然语言 scan 说明时，我可以在写入前 Harness 设计预览中看到这些 scan 补充被列为明确约束，并看到它们将影响哪些 Harness 设计决策，从而在最终确认前确信系统不是只把我的输入记录下来，而是用它来生成当前这版 Harness。

## 验收标准

1. `_show_prewrite_maturity_preview()` 接收当前 `GuidedScanOverrides`，在 `写入前 Harness 设计预览` 中先展示 `扫描补充约束`。
2. 当存在 scan 补充时，preview 至少展示：技术栈修正、自然语言补充、结构化模块、结构化验证命令、结构化风险区域中存在的项。
3. preview 明确说明 scan 补充会影响 project inventory、command catalog、risk hints、Guides、Sensors、Workflow 升级或人工确认；同时说明它仍是用户补充，不会伪装成已验证扫描事实。
4. 当用户在最终确认阶段返回 scan 并替换补充时，最终一次 preview 只展示当前生效补充，不展示上一版补充。
5. 当没有 scan 补充时，preview 显示当前按扫描基线继续，不制造虚假的用户补充。
6. 不修改 `.ai` 机器消费 schema、不修改正式资产生成策略、不执行 Runtime、不创建 `.ai/task-runs`。
7. 完成前运行目标 integration、完整 guided init integration、`git diff --check` 和 `scripts/test-fast.sh`。

## 决策与取舍

- 本轮只增强 CLI preview，不改 `ProjectInventory`、`CommandCatalog`、`interaction-decisions.yaml` 的契约；这些链路已经由现有测试覆盖。
- preview 中使用用户可读文案，不直接暴露内部字段名。
- scan 补充 section 放在团队规则 / Workflow 约束之前，因为 scan 补充影响更基础的 inventory、commands 和 risk hints。

## Assumptions / Risks

- Assumption：展示前 5 条各类补充足以让用户确认系统理解；完整内容仍在最终确认摘要和生成产物中保留。
- Risk：CLI 输出继续变长；本轮只在用户确实补充 scan 信息时展开详细项，无补充时使用一行基线说明。
- Sub agent：尝试启动 explorer 做只读审查，但当前线程上限返回 `agent thread limit reached`，本轮由主线程完成审查。
