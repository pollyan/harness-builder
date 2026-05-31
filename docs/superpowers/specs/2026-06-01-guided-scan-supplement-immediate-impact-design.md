# Guided Init 扫描补充即时影响说明设计

## 事实源快照

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、近期 `docs/evolution-log.md`、`interactive_init.py`、`interaction_decisions.py` 和 guided init integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`sensor-and-gate-rules.md` 和 `architecture.md`。本轮不修改 LLM prompt/schema、benchmark gate、模块边界或目录结构。
- sub agent：按目标模式要求尝试启动只读 explorer 审查该 gap，但当前会话返回 `agent thread limit reached`，本轮由主线程继续完成调研、实现和验证。

## Current State Gap Analysis

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 扫描补充后的即时理解回显与影响说明 | init North Star / Gate | 用户输入 scan 补充后，CLI 立即复述系统如何理解这些补充，并说明会影响成熟度、缺口判断、Guides、Sensors、Workflow 或人工确认 | 补充已写入 inventory、command catalog、`human_overrides`、interaction decisions、project-context、human-input-needed；最终确认阶段会展示“已吸收的用户补充”和“补充影响” | 复述太晚：在进入团队规则、候选审查、workflow 展示和写入前 preview 前，用户看不到补充已被结构化吸收以及会影响哪些后续判断 | 补齐渐进式协作闭环，让用户确信补充不是最终确认时的装饰文本，而是在后续设计前已被纳入决策链 | 低；主要是 CLI transcript helper 和 integration 断言，不改 schema / LLM / benchmark | guided init integration transcript；产物 schema 既有测试继续覆盖 | 无外部凭证；不依赖真实 DeepSeek | 断言补充输入后、团队规则前出现稳定“扫描补充理解 / 扫描补充影响”区块，并包含具体 module/command/risk/natural note 与 maturity/guides/sensors/workflow/human-input 影响 | 本轮 |
| B. 给 `InteractionDecisions.scan_confirmation` 增加结构化 impact 字段 | init North Star / 新发现 | machine-readable decisions 明确记录每条补充影响 maturity/guides/sensors/workflow | 当前 decisions 只记录 notes 和 primary stack override；结构化 module/command/risk 存在于 inventory `human_overrides` | 影响关系仍主要在 CLI / Markdown，自身没有独立机器字段 | 有利于后续 self-improve 或 audit 直接消费用户补充影响 | 中；涉及 Pydantic schema、writer、fixtures 和兼容读取 | schema unit、integration、fixture diff | 需要 schema 迁移设计 | 新字段通过 schema 校验并被 trace / summary 消费 | 后续候选 |
| C. 用户团队规则输入后的即时影响说明 | init North Star / 新发现 | 团队规则输入后也立即显示会影响 Guide、human-input-needed 和风险策略 | 当前最终确认阶段会复述团队规则影响；正式资产会吸收 | 与 A 类似，但输入发生在 scan 补充之后、候选审查之前，仍可更及时 | 继续提升交互低负担 | 低 | integration transcript | 无 | 团队规则输入后立即出现影响区块 | 可与 A 同源，但本轮先聚焦 scan 补充；后续按需要合并 |
| D. push 前 full regression 先决条件说明 | 当前仓库状态 | 本地 commits 能在满足全量验收条件后推送 | `scripts/test-full.sh` 当前因缺 `DEEPSEEK_API_KEY` 和 `.benchmarks` 真实仓库失败 | 无法 push 已有 14 个本地提交 | 降低远端同步不确定性 | 非代码；需要外部凭证/仓库 | full regression | 外部凭证和网络 | full 通过后 push | 暂不作为本轮功能 milestone |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 的“收到补充后立即整理理解并说明影响”硬体验目标，且当前代码已经具备后续消费链路，只差用户可见的即时闭环。
2. B 更长期、更机器化，但会扩大 schema 契约和迁移面；当前先不在同轮引入。
3. C 与 A 同类，但团队规则即时反馈可以在后续与更完整的 context input 影响模型一起做；本轮先补 scan 阶段最关键的前置决策点。
4. D 是推送条件问题，不推进 init North Star，且依赖外部凭证与真实仓库。

## 本轮 Milestone

作为 Harness Maintainer，当我在首次 guided `init` 的扫描理解阶段补充自然语言说明或结构化 `module` / `command` / `risk` 修正时，我可以在进入团队规则和设计候选前立即看到 Harness Builder 如何理解这些补充、会如何影响成熟度缺口判断和后续 Harness 推荐，从而确认交互输入已经进入决策链路，而不是只在最终确认阶段被动展示。

## 验收标准

- CLI transcript：在 `你的补充或修正` 之后、`\n团队规则` 之前，出现稳定 `扫描补充理解` 和 `扫描补充影响` 区块。
- CLI transcript：自然语言 note、结构化模块、验证命令和风险区域必须被逐项复述，且不伪装成已验证事实。
- CLI transcript：影响说明至少覆盖成熟度 / 缺口判断、Guides、Sensors、Workflow 升级或 human-input-needed 中的适用项。
- 数据契约：现有 `project-inventory.json`、`command-catalog.yaml`、`interaction-decisions.yaml`、`project-context.md`、`human-input-needed.md` 的补充吸收行为保持不退化。
- 边界：不修改 LLM schema、prompt、benchmark gate、Runtime 分工，不创建 `.ai/task-runs`，不新增 silent fallback。
- 测试：先更新 guided init integration 测试形成失败断言，再实现；提交前运行 `scripts/test-fast.sh`。
- 文档：更新 `docs/engineering/init-workflow.md` 的“用户补充复述与影响说明”规则，并在 `docs/evolution-log.md` 记录本轮 Gap Analysis、决策、验证和 Gate。

## 决策与取舍

- 本轮不新增 machine-readable impact schema。结构化 module/command/risk 已分别进入 inventory / command catalog / human_overrides；scan notes 已进入 interaction decisions。即时 CLI 反馈先复用这些现有契约。
- 本轮不重新计算第二份 maturity report 文件，只在内存态应用 scan overrides 后用中文说明影响方向；写入前 preview 仍负责展示基于更新 inventory/commands 的成熟度预测。
- 本轮不把自然语言补充改写成已验证扫描事实。CLI 文案使用“用户补充 / 将影响 / 需要后续确认”，避免越权声明。

## Assumptions / Risks

- Assumption：当前 `_apply_scan_overrides()` 在团队规则、candidate review、workflow preview 前执行，因此补充已经能影响后续 weapon selection、candidate report、maturity preview 和正式资产。
- Risk：文案过多可能让 guided CLI 变长；本轮限制为两个短区块，最多展示前若干条。
- Risk：结构化 command 的 source path 可能不存在；本轮只说明会进入 command catalog 和 Sensor/hard gate 摘要，具体 evidence 强度仍由 benchmark hard gate check 负责。

## 非目标

- 不修改 `InteractionDecisions` schema。
- 不修改 LLM scan / evidence expansion / self-check。
- 不运行或默认触发 benchmark。
- 不执行 Runtime，不生成 `.ai/task-runs`。
- 不处理已有 Harness 维护入口。
