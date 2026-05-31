# 成熟度叙事中文化设计

## Current State Gap Analysis

| 候选 gap | 目标态 | 当前能力 | 缺口 | 价值 | 风险 / 复杂度 | 可测试性 | 排序 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 成熟度英文叙事中文化 | CLI、`init-summary.md`、`maturity-report.md` 中的 blocker、evidence summary、next step 均为中文，围绕 L0-L4 解释 | guided init 已有成熟度初评和 preview，但 `maturity_model.py` 仍返回英文 blocker / requirement | 用户界面泄漏内部英文表达，削弱首次 init 可信度 | 直接提升 CLI-first 体验和客户试跑专业性 | 低到中；主要是文案和测试，需避免改 schema | unit + integration 可覆盖 | P0 |
| LLM-planned deep scan | LLM 基于 manifest 主导深读计划 | 已有 planner 和 coverage warning | planner 还不是扫描主线 | 提升仓库理解深度 | 高 | 需 acceptance | P1 |

本轮选择成熟度中文叙事。它来自 `docs/todos/guided-init-ai4se-real-repo-findings.md`，也是上一轮 Self-Harness Gate 的首选下一 gap。

## 用户故事

作为 Harness Maintainer，当我在首次 guided `init`、已有 Harness 维护入口或生成的成熟度报告中查看当前 L0-L4 等级、主要阻断项和下一步建议时，我可以看到中文、面向工程影响的成熟度解释，而不是英文内部句子，从而理解当前等级为什么成立、下一等级差什么以及应该先补齐什么。

## 范围

- 在 `maturity_model.py` 源头把 `MaturityEvidence.summary`、`MaturityBlocker.reason`、`next_level_requirements` 和 blocking cap reason 改为中文。
- 在 maturity report 渲染层把维度 key 映射为中文标签，并把 `evidence:` / `blockers:` 替换为中文展示标签。
- 保留 blocker id、dimension key、schema 字段名、source path 等机器稳定标识。
- 不做“全局无英文”断言，因为 `Guides`、`Sensors`、`Workflow`、`Runtime`、文件路径、命令名仍是合理产品术语。
- 不改 maturity schema、等级算法、dimension key 或 LLM review schema。

## 设计

`MaturityReport` 是 CLI、report writer、assess、init summary、improve candidate 的共同事实源。把文案翻译放在渲染层会造成出口漏翻，也会让 `maturity-score.yaml` 继续包含英文用户叙事。因此本轮在源头改写 user-facing strings。渲染层只负责中文展示标签和维度 label，不改变机器 key。

翻译原则：

- 保留稳定技术名词：`Guides`、`Sensors`、`Workflow`、`Runtime`、`hard gate`。
- 英文完整句替换为中文完整句，例如 `Guides are structured...` 改为 `Guides 已结构化，但还没有按任务风险和上下文动态加载。`
- 证据摘要使用中文短句，例如 `Workflow routing 规则数量：3。`
- 下一步建议使用动作式中文，例如 `用全部 resolved 的 Runtime task-run 证据验证 Workflow routing。`
- `blocking_caps` 也要中文化，因为它同样进入机器报告和用户解释。

## 验收标准

- `build_maturity_report()` 的 `blocking_reasons` 与 `recommended_next_steps` 不再包含已知英文句子，并包含中文 blocker / next step。
- runtime failed sensor 场景仍阻止 L3，但 blocker 变为中文。
- `maturity-score.yaml` 的 workflow evidence 和 next level requirements 变为中文。
- guided init happy path 的“扫描后的成熟度初评”和“当前 Harness 成熟度初评”不再出现已知英文 blocker / next step。
- `.ai/maturity-report.md` 不再出现 `evidence:` / `blockers:` 这类英文展示标签，并用中文维度标签保留机器 key。
- 不改变 maturity schema、dimension id、blocker id 或等级计算。

## Assumptions / Risks

- 这些字段目前同时服务机器消费和用户审查；中文内容不会破坏 Pydantic schema，但可能影响依赖英文字符串的测试，因此测试应改为验证语义与 id。
- LLM maturity reviewer 读取 maturity evidence / score 时能处理中文；本仓库文档要求过程与 spec 文档中文化，这与产品方向一致。

## Sub Agent 使用情况

本轮已派出一个只读子代理审查 maturity 出口和测试风险。子代理建议“源头翻译为主，渲染层补标签映射”，本轮采纳该边界。
