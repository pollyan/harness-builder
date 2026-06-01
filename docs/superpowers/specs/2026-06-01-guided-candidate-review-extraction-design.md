# Guided 候选审查边界抽取

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/architecture.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景规划开篇与 Runtime 边界、`docs/todos/README.md`、当前 `interactive_init.py`、相关 tests、近期 specs / plans 索引。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`。本轮不修改 LLM、Prompt、schema、benchmark 或 Sensor 规则。
- Todo 状态：`docs/todos` 无 open todo；本地 `main` 领先 `origin/main` 52 个提交；本轮开始时已有本 spec / plan 草稿处于未提交状态。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Guided 候选审查边界抽取 | 上轮 Gate / 架构规则 | Guide / Sensor 基线呈现、LLM 候选逐项审查和 `CandidateDecision` 构造有独立模块与 unit coverage | scan presentation、supplement presentation、prewrite preview、existing Harness action runner 已拆分 | `_review_candidates()` 仍在 `interactive_init.py` 内，同时负责 CLI 文案、prompt 输入和决策构造，只能靠 integration 间接覆盖 | 保护“候选资产 review-only -> 用户确认 / 拒绝 / 备注 / 保留”的渐进式治理链路，降低后续改善候选审查体验或引入更细候选说明时误伤主 init 状态机的风险 | 中低；行为保持型抽取，但涉及 prompt 输入与 decisions | 新 unit 模拟 prompt 选择；targeted guided integration 覆盖 transcript 和 decisions | 无 | 新模块 unit 证明四种选择与 no-candidate 行为；integration transcript / decisions 不变；`interactive_init.py` 继续缩小 | 本轮 |
| B. 团队规则输入体验增强 | init North Star / 新发现 | 团队规则输入按架构约束、测试策略、安全合规、发布约束等类别提示或收集，并更清楚影响后续生成 | 当前单段自然语言团队规则会进入 interaction decisions、Guides、human-input-needed 和 completion summary | 输入粒度低，Maintainer 仍要自己把多类约束塞进一段文字 | 用户价值更直接，能提升隐性团队约束获取质量 | 中；可能影响 interaction decisions、guides、人机 transcript 和文档 | integration + writer tests + completion tests | 需要先保持候选审查边界更清楚 | 下一轮候选 |
| C. push / 远端同步 | 交付节奏 | 完整工作包通过 full regression 后统一 push | 本地已有多个独立提交 | push 前 full regression 需要真实 DeepSeek 和 `.benchmarks/*` | 让远端获得当前阶段成果 | 高；外部凭证 / 真实仓库前置 | `scripts/test-full.sh` + push | DeepSeek key、真实仓库 | 外部前置满足后处理 | 暂不处理 |

排序结论：

1. 选择 A，因为 `_review_candidates()` 是当前 `interactive_init.py` 中剩余的高价值混合职责之一，直接保护候选审查这个 review-only 治理链路。它可小步完成、可单测、对用户 transcript 行为保持稳定。
2. B 用户价值更直接，但会改变输入体验和产物叙事；先抽取候选审查边界，后续增强团队规则和候选审查文案时更稳。
3. C 仍受 full regression 外部前置限制，不进入本轮。

本轮 milestone：

作为 Harness Builder 维护者，当我继续打磨首次 guided `init` 中 Guide / Sensor 候选审查体验时，我可以在独立候选审查模块中渲染候选、读取用户选择并构造 `CandidateDecision`，从而让主向导状态机只负责编排阶段，并降低后续调整候选治理体验时误伤 scan、团队规则、Workflow 或写入流程的风险。

## 验收标准

1. 新增 `guided_candidate_review.py`，承接：
   - Guide weapon baseline 呈现。
   - Sensor weapon baseline 和 command gate 呈现。
   - LLM candidate 逐项审查呈现。
   - 用户输入 `a` / `r` / `e` / default 的 `CandidateDecision` 构造。
   - no-candidates 提示。
2. `interactive_init.py` 不再内联 `_review_candidates()` 实现，只保留 alias / facade 调用新模块，兼容现有和隐藏测试。
3. 用户可见 transcript 和 `interaction-decisions.yaml` 行为保持不变。
4. 新 unit 直接覆盖候选审查四种决策和 no-candidate 分支。
5. targeted guided integration 证明真实 init transcript 和 candidate decisions 不漂移。
6. 不修改 schema、LLM、writer、benchmark、Runtime 分工，不创建 `.ai/task-runs`。

## 决策 / 取舍

- 本轮只抽取 review candidate 交互逻辑，不改变选项、文案或决策语义。
- 新模块允许注入 prompt 函数，unit 可以不依赖 Typer runner 直接测试输入分支；默认仍使用 `typer.prompt`。
- 不把 `build_llm_enhancement_candidates()` 或 `select_weapon_library()` 放入新模块。它们仍属于主向导阶段编排和上游候选生成。

## Assumptions / Risks

- Assumption：候选审查体验后续还会继续优化，例如候选分组、成熟度维度说明或低置信度标记，因此值得先形成模块边界。
- Risk：prompt 注入如果设计过度会偏离当前 Typer 行为；本轮只使用简单 callable，默认路径不变。

## Sub Agent

尝试启动 explorer 做只读审查，但当前会话返回 `agent thread limit reached`。本轮由主线程完成调研、实现和验证。
