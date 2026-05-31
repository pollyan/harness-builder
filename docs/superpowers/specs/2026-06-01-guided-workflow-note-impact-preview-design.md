# Guided Init Workflow 补充影响与预览设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/todos/local-unique-capability-migration.md`、`interactive_init.py` 和相关 integration tests。
- 按需未展开：`llm-contracts.md`、`sensor-and-gate-rules.md` 和 `architecture.md`，因为本轮不修改 LLM prompt/schema、benchmark gate 或模块边界。
- 当前 todo 状态：`docs/todos/README.md` 显示当前没有 open todo；`local-unique-capability-migration.md` 状态为 `implemented`，本轮不继续围绕旧 61 提交迁移。
- Sub agent：按目标模式尝试启动只读 explorer 调研 workflow note 链路，但当前环境返回 `agent thread limit reached`，本轮由主线程完成调研。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Workflow 补充即时影响与预览 | North Star / 新发现 / 上轮 Gate 同类链路 | 用户输入 workflow note 后，在进入写入前确认前立即看到系统理解、影响资产和 routing 边界；设计预览展示该约束 | `_show_workflows()` 收集 note，`interaction-decisions`、project-context、human-input-needed 会持久化，最终确认会汇总 | 收集后没有即时复述；`_show_prewrite_maturity_preview()` 不展示 workflow note，用户无法在 preview 阶段确认它只是 review-only 说明，不会直接改正式 routing policy | 补齐 scan/team rules/workflow 三类用户补充的渐进式反馈闭环，降低用户误以为自由文本直接改 routing 的风险 | 低：只改 CLI 文案和函数参数，不改 schema、不改 routing 生成 | integration CLI transcript 可断言顺序、文案、preview；现有持久化断言继续覆盖资产 | 无外部凭证 | 目标测试 + guided init 相关 tests + fast regression | 本轮 |
| B. `WorkflowConfirmation` 结构化 impact 字段 | Gate 候选 | workflow note 的影响范围成为机器可读 schema，后续 preview / summary 可统一消费 | `WorkflowConfirmation.notes` 只有自由文本 | 没有结构化 impact，文案逻辑分散 | 增强未来审计和复用 | 中：涉及 schema、writer、旧文件兼容 | unit + integration schema tests | 需要明确长期契约 | 后续候选 |
| C. Workflow note 参与 routing 候选生成 | North Star 第三阶段 | 用户补充可以影响 workflow routing candidate 或 review-only policy 建议 | 当前 note 只进入说明和人工确认，不改正式 routing | 对高价值 workflow 策略补充缺少候选化路径 | 让 workflow 设计更定制 | 高：涉及 LLM/候选治理/routing policy 边界 | 需要 schema、benchmark、review-only tests | 需要先设计 policy candidate 边界 | 后续较大 milestone |
| D. Push 前 full regression / 远端同步 | 工程治理 | 完成本地有价值批次后运行 full 并 push | 当前本地领先远端 16 个提交 | full 依赖 DeepSeek 和真实仓库，之前环境不完整 | 降低本地堆积风险 | 中：外部凭证 / benchmark 仓库 | `scripts/test-full.sh`、push 结果 | `DEEPSEEK_API_KEY`、`.benchmarks` | 不作为本轮 init 功能切片 |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 的渐进式协作要求：关键用户输入必须在相关设计决策前被复述、说明影响并进入后续预览。它与前两轮 scan supplement、team rules 的能力在同一用户故事链路上，能用一个小型 CLI transcript 切片独立验收。
2. B 不选，因为结构化 impact schema 是更长期的契约 hardening，本轮 CLI 用户价值不依赖它。
3. C 不选，因为 workflow note 直接影响 routing policy 会触及 review-only 候选治理边界，不能把自由文本静默晋升为正式策略。
4. D 不选，因为本轮目标是继续推进 init 体验；push 必须等有完整批次和 full regression 先决条件满足。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 中给推荐 Workflow 输入补充说明时，我可以在进入写入前确认前立即看到 Harness Builder 如何理解这条补充、它会进入哪些审计/人工确认资产，并在写入前 Harness 设计预览中看到它不会直接修改正式 workflow routing policy，从而确认我的 workflow 经验被记录和用于审查，但不会越过候选治理边界。

## 验收标准

1. CLI transcript：`如果工作流还有补充说明` 输入后，必须在 `当前 Harness 成熟度初评` / `写入前 Harness 设计预览` 之前出现 `Workflow 补充理解` 和 `Workflow 补充影响`。
2. CLI transcript：即时影响说明必须包含用户输入原文、`interaction-decisions.yaml`、`project-context.md`、`human-input-needed.md`、`review-only` 或后续人工确认含义，以及“不直接修改正式 workflow routing policy”的边界。
3. 写入前 preview：必须展示 `Workflow 补充约束`，包含用户输入原文，并说明补充只进入审计 / 人工确认 / 说明链路，不直接修改正式 routing policy。
4. 资产契约：现有 `interaction-decisions.yaml`、`project-context.md`、`human-input-needed.md` 中 workflow note 的持久化断言继续通过；本轮不新增 Pydantic schema。
5. 边界：无 workflow note 时不输出即时 workflow 补充区块；preview 可说明当前按内置 routing 预览。
6. 测试：先更新 integration 测试使当前代码失败，再实现；至少运行目标测试、相关 guided init tests 和 `scripts/test-fast.sh`。
7. 文档：同步 `docs/engineering/init-workflow.md`、`docs/evolution-log.md`、本 spec 和 plan；不新增 open todo。

## 决策与取舍

- 复用 `WorkflowConfirmation.notes`，不新增 schema 字段。
- preview 文案显式使用 review-only / 人工确认边界，防止用户误解自由文本可以直接改正式 routing policy。
- 不改变 `HarnessConfig.default()`、workflow routing rules 或 asset writer 的 routing 生成。
- 不增加最终确认的 `back` 目标到 workflow；这属于另一个交互控制 gap。

## Assumptions / Risks

- `WorkflowConfirmation.notes` 已通过 `accepted_interactive_decisions()` 进入 `interaction-decisions.yaml`，并由现有 writers 渲染到 project-context / human-input-needed。
- CLI 输出会略微变长，但只在用户输入 workflow note 时展示即时反馈；preview 增加一个短小节。
- 如果未来需要让 workflow note 产生 routing policy candidate，应单独设计 review-only schema 和 benchmark。
