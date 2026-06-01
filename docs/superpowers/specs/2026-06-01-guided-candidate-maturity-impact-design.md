# Guided 候选审查成熟度影响提示

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划开篇与产品边界、`docs/engineering/init-workflow.md`、`docs/engineering/architecture.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、当前 `guided_candidate_review.py`、`prewrite_preview.py`、`llm_enhancement_candidates.py`、`WeaponLibraryCandidate` schema 和相关 tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`。本轮不修改 LLM prompt / schema、Sensor 规则或 benchmark。
- Todo 状态：`docs/todos` 无 open todo；上一轮 Gate 候选包括候选审查成熟度解释增强、push / 远端同步。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. LLM 候选审查成熟度影响提示 | 上一轮 Gate / init North Star | Maintainer 审查每个 LLM Guide / Sensor 候选时，能看到它预计补齐的成熟度维度和 review-only 边界 | 写入前 preview 已对内置 weapon 展示关联成熟度、阻断和下一阶段贡献；LLM candidate 审查已抽出独立模块 | LLM candidate 审查只展示类型、作用和 evidence，没有说明它与 Guides / Risk Control / Sensors / Verification 成熟度差距的关系 | 让候选审查更接近 maturity-driven preview，降低用户把候选当作普通列表或模板项的风险 | 中低；只改 CLI 文案，不改 schema / candidate generation / writer | unit 覆盖 guide/risk/sensor/no-enhancement 推断；integration 覆盖 guided init transcript | 无 | 本轮 |
| B. 候选 report 持久化成熟度字段 | 新发现 | `.ai/experience/weapon-library-candidates.yaml` 机器契约也包含 maturity impact | 当前 schema 没有 maturity 字段 | 机器可消费性更强，但需要 schema 迁移和 writer/benchmark 影响评估 | 中高；schema 和历史兼容风险 | schema unit + writer/integration/benchmark | 需要单独设计 | 下一轮候选 |
| C. push / 远端同步 | 交付节奏 | 完整工作包通过 full regression 后 push | 本地 `main` 已领先远端 54 个提交 | push 前 full regression 需要真实 DeepSeek 与 `.benchmarks/*` | 让远端获得当前阶段成果 | 高；外部凭证 / 真实仓库前置 | `scripts/test-full.sh` + push | DeepSeek key、真实仓库 | 外部前置满足后处理 | 暂不处理 |

排序结论：

1. 选择 A，因为它直接服务 init North Star 的“成熟度驱动 Harness 设计预览”和“可解释候选审查”，且在上一轮抽出 `guided_candidate_review.py` 后可以低风险完成。
2. B 暂不选，因为 schema 迁移会扩大范围；先验证 CLI 叙事价值，再决定是否进入机器契约。
3. C 继续受 full regression 外部前置限制。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 中逐项审查 LLM 提出的 Guide / Sensor 候选时，我可以看到每个候选预计补齐的成熟度维度、对下一阶段基线的贡献和 review-only 边界，从而更有依据地决定接受、拒绝、备注或保持候选。

## 验收标准

1. `guided_candidate_review.py` 在每个 LLM candidate 下新增稳定的“成熟度影响”输出。
2. Guide candidate 默认提示补齐 `Guides 上下文`；风险类 guide candidate 还提示 `Risk Control 风险控制`。
3. Sensor candidate 默认提示补齐 `Sensors 验证` 和 `Verification 验证成熟度`。
4. `llm-guide-no-enhancement-001` 这类无明确增强项候选必须说明主要用于保留审计边界，不伪装成成熟度提升。
5. 输出必须明确候选保持 review-only，接受也只是记录确认，不自动写入正式 Guide / Sensor。
6. 不修改 `WeaponLibraryCandidate` schema、不修改 LLM candidate generation、不修改 writer、benchmark 或 Runtime 分工。
7. Unit 和 guided integration 覆盖新增 transcript，原有 decision 行为不漂移。

## 决策 / 取舍

- 本轮使用确定性映射从 `candidate_type`、`id`、`title` 和 `evidence` 推导用户可读成熟度影响，不新增 schema 字段。
- 风险类识别只用于 CLI 提示，不作为机器契约；更正式的 candidate maturity fields 留给后续 schema milestone。
- “接受”候选仍只影响候选状态和 interaction decisions，不自动晋升正式资产。

## Assumptions / Risks

- Assumption：在候选审查阶段先解释成熟度影响，会提高 Maintainer 对候选的判断质量。
- Risk：确定性映射可能过粗；通过 conservative wording 和 review-only 边界降低误导。

## Sub Agent

本轮未使用 sub agent。前几轮连续遇到 `agent thread limit reached`；当前切片范围窄、可由主线程完成。
