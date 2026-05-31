# Init Completion User Supplements 设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`src/harness_builder_agent/tools/init_summary.py`、`tests/unit/test_init_summary.py` 和 `tests/integration/test_init_on_fixture_projects.py`。
- 按需未展开：LLM contracts、sensor / gate 规则。本轮不改 LLM、benchmark、Sensor 或机器消费 schema。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. completion message 展示本次吸收的用户补充 | init North Star / 新发现 | 写入完成后终端摘要作为主交付说明，应直接告诉用户哪些 scan / team / workflow 补充已进入交付，并提示完整细节在 `init-summary.md` / `interaction-decisions.yaml` | `init-summary.md` 已有 `## 本次吸收的用户补充`；最终确认前 CLI 也会复述用户补充 | `== 初始化完成 ==` completion message 只显示生成资产、成熟度、证据缺口、benchmark、入口和待确认，不显示本次吸收的补充 | 让用户在终端主交付摘要中直接确认输入被消费，强化 CLI-first 体验和渐进式协作闭环 | 低；只读现有 `interaction-decisions.yaml` schema，不改落盘契约 | unit 构造 `.ai/interaction-decisions.yaml` 验证 completion message；integration 验证真实 guided init 输出 | 无外部依赖 | unit + targeted guided integration + full guided integration | 本轮 |
| B. existing-Harness 维护入口继续拆模块 | 上轮 Gate / 架构规则 | 已有 Harness 维护入口状态和动作分发模块化 | `interactive_init.py` 仍很大 | 工程可维护性缺口，但用户可见价值弱于 A | 降低后续维护入口迭代风险 | 中；改动面较广 | unit / integration 行为等价 | 无外部依赖 | helper unit + existing Harness integration | 下一轮候选 |
| C. push / full regression 同步远端 | git 状态 / Gate | 完整工作包通过 full regression 后 push | `main` ahead 35；fast regression 可通过 | push 前需要真实 DeepSeek / `.benchmarks` full regression | 降低分叉风险 | 外部前置 | full regression 与 push 结果 | `DEEPSEEK_API_KEY`、真实仓库、网络 | full 通过并 push | 外部前置候选 |

排序结论：

1. 选择 A。它是首次 `init` 主旅程中的 CLI-first 交付缺口，直接服务 `init-north-star.md` 的“写入后的交付摘要”和“用户补充必须形成可审计闭环”。
2. B 是有价值的工程信任故事，但当前用户可感知价值低于 A。
3. C 受外部 full regression 前置影响，本轮不选。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 中提供 scan 修正、团队规则或 Workflow 补充并确认写入后，我可以在终端 `== 初始化完成 ==` 主交付摘要中直接看到“本次吸收的用户补充”及其事实边界，从而不用先打开 Markdown 也能确认自己的输入已经进入 Harness 交付链路。

## 验收标准

1. `render_init_completion_message(ai)` 输出稳定的 `本次吸收的用户补充：` section，位置在 `主要证据 / 缺口` 之后、`建议下一步` 之前。
2. 当 `.ai/interaction-decisions.yaml` 存在时，completion message 通过 `InteractionDecisions` schema 读取 scan notes、team rules、workflow notes 和 shown workflows，展示前几条可读摘要。
3. 有用户补充时，section 明确指向 `.ai/interaction-decisions.yaml` 与 `.ai/init-summary.md`，并说明团队规则 / Workflow note 不会被伪装成扫描事实或正式 routing policy。
4. 没有用户补充时，section 明确提示本次未提供人工补充，后续可在维护入口继续补齐。
5. 缺少 `.ai/interaction-decisions.yaml` 时不能静默伪装为成功；completion message 应显示缺失提示，帮助用户检查生成过程。
6. 不修改 `.ai` schema、不改正式资产生成、不改 Runtime 分工。
7. 单元测试覆盖有补充、无补充和缺文件；integration 覆盖 guided `init` 真实输出。

## 决策与取舍

- completion message 直接读取 `interaction-decisions.yaml`，不从 Markdown 反向解析 `init-summary.md`，保持结构化来源。
- 本轮只增强终端交付摘要；`init-summary.md` 已经有完整章节，无需重复改写。
- 展示数量保持简短，完整细节仍以 `.ai/init-summary.md` 和 `.ai/interaction-decisions.yaml` 为准。

## Assumptions / Risks

- Assumption：终端摘要显示 3-5 条用户补充足以让 Maintainer 确认输入被消费。
- Risk：completion message 变长。通过限制条数和提供完整文件入口控制长度。
- Sub agent：尝试启动 explorer 做只读审查，但当前会话返回 `agent thread limit reached`；主线程完成审查。
