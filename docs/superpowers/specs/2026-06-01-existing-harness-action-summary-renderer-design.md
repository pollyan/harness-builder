# Existing Harness Action Summary Renderer 抽取设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/architecture.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/evolution-log.md`。
- 当前代码 / 测试检查：`interactive_init.py` 仍有 1800+ 行；已有 Harness 入口已拆出 `existing_harness_actions.py`、`existing_harness_status.py`、`existing_harness_signals.py`，但 action execution 分支及 action 完成摘要 helper 仍在主向导文件内；existing Harness integration 已覆盖 exit / assess / improve / benchmark / recommend-workflow / review-candidate / review-human-input / self-improve。
- 按需未展开：`docs/engineering/llm-contracts.md` 与 `sensor-and-gate-rules.md`；本轮不修改 LLM、prompt、schema、scan、Sensor 或 benchmark 规则。
- Todo 状态：`docs/todos/README.md` 当前没有 open todo；本轮从上一轮 Gate 候选和当前代码结构选择工程信任故事。
- Sub agent：本轮未使用 sub agent；当前切片为单模块低风险抽取，主线程完成代码审查、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness action summary renderer 抽取 | Gate / 当前代码 | existing Harness 各维护动作的完成摘要、候选详情和应用预览有独立 renderer 与 unit 覆盖 | signals / status / action contract 已拆出；integration 覆盖 action 行为 | `_benchmark_summary()`、`_workflow_recommendation_summary()`、`_candidate_governance_summary()`、`_human_input_governance_summary()`、`_self_improve_summary()`、`_top_improvement_candidate()` 和 candidate preview 仍内联在 `interactive_init.py` | 保护“选择维护动作 -> 看懂结果摘要”的 CLI 体验，降低后续 action execution 抽取和文案调整风险 | 低：行为等价抽取，不改 action 执行、schema、LLM 或 Runtime | 新 unit 直接覆盖 renderer；existing Harness targeted integration 验证 transcript / action 语义不漂移；fast regression | 依赖现有 Pydantic schema 和 fixture tests | 新模块可直接渲染 action summaries；`interactive_init.py` 仅调用 renderer facade；相关 integration 保持通过 | 本轮 |
| B. Existing Harness action execution 抽模块 | Gate / 架构规则 | 主向导只负责状态展示和动作选择，action 执行由独立模块承接 | 已有 action contract、status、signals 模块 | assess / improve / benchmark / recommend-workflow / review-candidate / review-human-input / self-improve 执行分支仍在主文件 | 进一步降低维护入口复杂度 | 中到高：跨 trace、artifacts、prompt、错误处理与多项 integration | 需要覆盖所有 existing Harness action integration | 无外部依赖，但改动面大 | 后续在 renderer 抽出后更容易做 | 下一轮候选 |
| C. 首次 init completion 生成清单进一步紧凑化 | Gate / init North Star | 完成摘要更短、更行动优先 | completion 已行动优先，用户补充已紧凑 | 生成清单仍略长，但属于交付确认信息 | 改善首次 init 终端可读性 | 低 | unit / integration transcript | 需要定义压缩口径 | 暂不处理 |

排序结论：

1. 选择 A，因为它直接服务已有 Harness 维护入口，风险比完整 action execution 抽模块小，又能为 B 降低改动面；同时它保护用户看到的 action 结果摘要不漂移。
2. B 暂不选，因为一次性迁出所有执行分支会触碰 trace、artifact、错误处理和多个 action 的 prompt，适合在 renderer 抽出后单独做。
3. C 暂不选，因为当前 completion 已经完成行动优先和用户补充紧凑化，用户价值低于维护入口工程边界收益。

## 本轮 Milestone

作为 Harness Builder 维护者，当我继续打磨已有 Harness 维护入口的各个维护动作时，我可以在独立 action summary renderer 模块中修改和单测 benchmark、workflow recommendation、candidate governance、human-input governance、self-improve 和 improvement candidate 摘要，从而降低触碰主 guided init 编排文件的风险，并确保 Maintainer 选择维护动作后看到的结果摘要不漂移。

## 验收标准

1. 新增 `existing_harness_action_summaries.py`，集中提供 existing Harness action result summary 和 candidate apply preview renderer。
2. `interactive_init.py` 不再内联这些 summary / preview helper，只调用新模块或薄 facade；action 执行语义、trace、artifact 和 CLI transcript 不变。
3. 新 unit 覆盖 benchmark failed summary、workflow recommendation summary、candidate detail / apply preview、human-input governance summary、self-improve summary 和 top improvement candidate。
4. Existing Harness targeted integration 覆盖 benchmark、recommend-workflow、review-candidate apply preview、review-human-input 和 self-improve 关键路径仍通过。
5. 不修改 `.ai` schema、LLM、benchmark 规则、正式资产生成或 Runtime 分工。
6. 提交前运行 `scripts/test-fast.sh`。

## 关键决策 / 取舍

- 本轮只抽取 action result renderer，不搬 action execution 分支。
- 在 `interactive_init.py` 保留 underscore facade，降低隐藏测试或旧调用方的破坏风险。
- Candidate apply preview 继续只渲染预览，不执行应用；workflow_policy 仍显示专家命令边界。

## Assumptions / Risks

- Assumption：action summaries 是执行分支里最稳定、最适合先抽出的纯渲染边界。
- Risk：candidate preview 依赖目标文件存在性，抽取时可能遗漏 `repo` 路径行为；本轮用 direct unit 和 existing Harness apply integration 验证。
