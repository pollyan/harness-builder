# Guided 团队规则输入引导增强

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md` 中团队规则 / 用户补充 / 写入前预览契约、`docs/engineering/architecture.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md` 中低负担交互和团队规则上下文要求、`docs/todos/README.md`、当前 `interactive_init.py`、相关 guided init integration tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`。本轮不修改 LLM、Prompt、Sensor、benchmark 或质量门禁。
- Todo 状态：`docs/todos` 无 open todo；上一轮 Gate 候选包括团队规则输入体验增强、push / 远端同步。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 团队规则输入引导分组 | 上一轮 Gate / init North Star | Maintainer 在输入团队规则前看到架构边界、测试策略、安全合规、发布回滚、只读区域等分组提示，能低成本补充隐性约束 | 当前 `_collect_team_rules()` 支持自然语言输入，输入后会复述并进入 `interaction-decisions.yaml`、`project-context.md`、`human-input-needed.md` | 输入前提示仍是一句宽泛例子，用户需要自己想起哪些约束值得补充；该 helper 仍内联在 `interactive_init.py`，缺少 direct unit | 提高首次 init 的团队上下文获取质量，并让后续 Guides / human-input-needed 获得更具体的人类约束 | 中低；只改 CLI 引导和模块边界，不改 schema / writer | 新 unit 捕获引导文案与空输入 / 有输入返回；integration 证明分组提示出现在团队规则理解前，产物链路不漂移 | 无 | 本轮 |
| B. 候选审查成熟度解释增强 | init North Star / 新发现 | LLM candidate 审查时说明候选关联成熟度阻断或下一阶段贡献 | 已有候选审查模块和写入前 preview 中的 baseline weapon maturity 解释 | LLM candidate 本身仍只展示 title / rationale / evidence | 用户价值明确，但可能需要扩展 candidate schema 或从 maturity report 生成映射 | 中；可能牵涉 schema / LLM candidate report | unit + guided integration + candidate report schema tests | 需要更细设计 | 下一轮候选 |
| C. push / 远端同步 | 交付节奏 | 完整工作包通过 full regression 后 push | 本地 `main` 已领先远端 53 个提交 | push 前 full regression 需要真实 DeepSeek 与 `.benchmarks/*` | 让远端获得当前阶段成果 | 高；外部凭证 / 真实仓库前置 | `scripts/test-full.sh` + push | DeepSeek key、真实仓库 | 外部前置满足后处理 | 暂不处理 |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 的低负担交互和团队规则上下文获取要求，且能形成可见 CLI 改善、可单测、风险小。
2. B 需要更细的候选成熟度语义设计，可能触碰 schema 或 candidate generation，不适合跟 A 混在同轮。
3. C 仍受 push 前 full regression 外部前置限制。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 的团队规则阶段准备补充组织约束时，我可以看到按架构边界、测试策略、安全合规、发布回滚和只读区域分组的输入引导，并继续用一段自然语言提交，从而更容易补充会影响 Guides 与 human-input-needed 的隐性团队规则。

## 验收标准

1. 新增 `guided_team_rules.py`，承接团队规则阶段的 CLI 引导和 prompt 采集。
2. 团队规则阶段必须展示稳定分组：
   - 架构边界 / 模块分层。
   - 测试策略 / 必跑验证。
   - 安全合规 / 数据权限。
   - 发布回滚 / 环境限制。
   - 禁止修改 / 只读区域。
3. 原 prompt 文案“可以输入一段规则说明；暂时没有则直接回车”保持，避免现有 integration 和用户肌肉记忆漂移。
4. 有输入时仍返回单条自然语言团队规则；空输入仍返回空列表。
5. `interactive_init.py` 不再内联 `_collect_team_rules()` 实现，只保留 alias / facade 兼容。
6. 现有 `context_confirmation` schema、impact scopes、policy effect、Guides、human-input-needed 和 completion summary 行为不变。

## 决策 / 取舍

- 本轮只增强输入前引导，不把团队规则拆成多个 schema 字段。当前 `ContextConfirmation.inline_contexts` 已能承载自然语言，继续避免把尚未审核的人类规则伪装成正式 policy。
- 不新增多轮问答。多 prompt 虽然能提高结构化程度，但会增加 guided init 负担；本轮保持“一段自然语言”入口。
- 抽出模块是为了给后续团队规则交互继续演进留出边界，不把更多文案堆回 `interactive_init.py`。

## Assumptions / Risks

- Assumption：分组提示能帮助 Maintainer 想起更具体的隐性团队约束，但不需要立即改变机器契约。
- Risk：提示变长可能增加终端信息量；通过保持分组短句和原 prompt 不变控制负担。

## Sub Agent

尝试启动 explorer 做只读审查，但当前会话返回 `agent thread limit reached`。本轮由主线程完成调研、实现和验证。
