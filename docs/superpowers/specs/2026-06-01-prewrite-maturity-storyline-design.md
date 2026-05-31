# Prewrite Maturity Storyline 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`src/harness_builder_agent/tools/prewrite_preview.py`、`src/harness_builder_agent/tools/interactive_init.py`、`tests/unit/test_interactive_init_preview.py` 和 `tests/integration/test_init_on_fixture_projects.py`。
- 按需未展开：LLM contracts、sensor / gate 规则。本轮不修改 LLM、benchmark、Sensor 或机器消费 schema。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 写入前成熟度叙事主线 | init North Star / 上轮 Gate | 写入前 preview 先用 L0-L4 主线说明当前等级、写入后基线、下一等级差距、用户补充如何影响预览，以及 benchmark / Runtime 未完成边界 | 当前 preview 已展示当前 L0/L1、写入后预计等级、下一目标、阻断项、补齐动作和设计预览 | 这些信息分散；用户补充如何影响 maturity preview 只在各 section 间接表达，没有一个面向确认写入的叙事 summary | 提升首次 `init` 最终确认前的可理解性，让 Maintainer 确信补充已进入成熟度与推荐链路 | 低；CLI 文案增强，不改 schema / writer / Runtime | unit 直接验证 renderer 输出；guided integration 防 transcript 断点漂移 | 依赖上轮抽出的 `prewrite_preview.py` | 新 unit + 现有 guided integration + fast regression | 本轮 |
| B. existing-Harness 维护入口继续拆模块 | 上轮 Gate / 架构规则 | 已有 Harness 状态展示和动作分发可在独立模块中维护 | `interactive_init.py` 仍约 2100 行，维护入口逻辑较多 | 拆分会降低后续维护入口迭代成本，但本轮用户可见价值弱于 A | 工程可维护性提升 | 中；涉及多个 guided action 和较多 imports | unit / integration 行为等价 | 无外部依赖 | helper unit + existing Harness integration | 下一轮候选 |
| C. push / full regression 同步远端 | git 状态 / Gate | 本地完整工作包通过 full regression 后 push | `main` ahead 34；fast regression 可通过 | push 前需要 `scripts/test-full.sh`，真实 acceptance 依赖 DeepSeek key、网络和 `.benchmarks` | 降低分叉风险 | 外部前置；不适合作为本地代码 milestone | full regression 与 push 结果 | `DEEPSEEK_API_KEY`、真实仓库、网络 | full 通过并 push | 外部前置候选 |

排序结论：

1. 选择 A。它直接服务 `init-north-star.md` 中“成熟度是叙事主线”和“设计预览应说明推荐项对应哪个成熟度维度、解决哪个阻断项、帮助进入哪个阶段”的目标，而且上轮已经把 preview 抽成独立模块，适合小步增强。
2. B 重要但属于工程信任故事，当前没有 A 的用户可感知价值强。
3. C 仍受外部凭证和真实仓库前置影响，本轮不选。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 的最终确认前查看写入前预览时，我可以先看到一段 L0-L4 成熟度叙事，明确当前从哪里起步、确认写入后建立什么基线、用户补充如何影响成熟度与 Harness 推荐、哪些质量或 Runtime 证据仍需后续动作验证，从而更有信心决定确认、返回修改或取消。

## 验收标准

1. `show_prewrite_maturity_preview()` 在“推荐补齐动作”和“写入前 Harness 设计预览”之间输出稳定的 `成熟度叙事主线` section。
2. 该 section 必须包含当前等级、写入后基线、下一目标、预览依据、用户补充影响和未完成边界。
3. 有 scan / team rules / workflow note 输入时，section 明确说明各类输入如何进入 maturity preview、Guides / Sensors / Workflow 设计和 review-only 链路。
4. 无用户补充时，section 明确说明当前按扫描证据和内置 Harness 基线预览。
5. 不修改 `.ai` schema、正式资产生成、maturity algorithm、benchmark 或 Runtime 分工。
6. 新 unit 直接覆盖有补充和无补充的 storyline 输出；现有 guided init integration 继续通过。
7. 完成前运行相关 unit、目标 guided init integration、完整 guided init integration、`git diff --check` 和 `scripts/test-fast.sh`。

## 决策与取舍

- 本轮只增强写入前 CLI 叙事，不改变落盘产物和算法。
- 文案以 L0-L4 主线为主，维度评分仍只作为 Guide / Sensor item 的解释，不新增大段内部字段。
- 用户补充仍区分事实边界：scan 补充更新本轮预览输入，但团队规则和 Workflow note 不被伪装成已验证扫描事实或正式 routing policy。

## Assumptions / Risks

- Assumption：一段紧凑 storyline 能降低用户在最终确认前“这些补充到底影响了什么”的认知成本。
- Risk：CLI 输出继续变长。通过限制 section 为少量 bullets，避免压过后续设计预览。
- Sub agent：本轮尝试启动 explorer 做只读审查，但当前会话返回 `agent thread limit reached`，由主线程完成审查。
