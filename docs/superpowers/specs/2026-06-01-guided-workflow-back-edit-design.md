# Guided Init Workflow 补充返回修改设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`interactive_init.py` 和 guided init integration tests。
- 按需未展开：`llm-contracts.md`、`sensor-and-gate-rules.md`、`architecture.md`，因为本轮不修改 LLM、benchmark、schema、目录结构或模块边界。
- 当前 todo 状态：`docs/todos/README.md` 显示没有 open todo，旧本地独有能力迁移包已 `implemented`。
- Sub agent：尝试启动只读 explorer 审查 back 流程，但当前环境返回 `agent thread limit reached`，本轮由主线程完成调研。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 最终确认可返回修改 Workflow 补充 | 新发现 / 上轮 Gate | 用户在最终确认看到 workflow note 错误时，可以只返回 workflow 阶段修改并重新预览，最终只持久化最新 note | final summary 支持 `back` 到 scan/rules/candidates；workflow note 已即时复述并进入 preview | `back` 提示不包含 workflow，用户不能修改刚刚展示的 workflow note，只能 cancel 重来或接受错误说明 | 补齐 workflow note 的低负担纠错闭环，避免错误人工说明进入正式资产 | 低：只改 CLI 控制流和测试，不改 schema / routing | integration 测试可断言 back->workflow、旧 note 不落盘、新 note 落盘 | 无外部依赖 | 本轮 |
| B. Workflow note 结构化 impact schema | 上轮 Gate | workflow note 影响范围机器可读，后续 preview / summary 统一消费 | 当前 `WorkflowConfirmation.notes` 只保存自由文本 | impact 文案仍分散在 CLI | 强化契约和审计 | 中：schema 和兼容性 | unit + integration schema tests | 需要契约设计 | 后续候选 |
| C. Workflow note 生成 review-only routing candidate | North Star 第三阶段 | 用户 workflow 经验可转为待审 routing policy candidate | 当前 note 只进入说明和人工确认 | 无法形成策略候选 | 更定制的 workflow 设计 | 高：触及 LLM / candidate governance / routing policy | 需要 schema、benchmark、治理测试 | 需要先设计安全边界 | 后续较大 milestone |
| D. Push 前 full regression / 远端同步 | 工程治理 | 本地有价值批次统一 full regression 后 push | 当前本地 ahead 17 | full 依赖真实 DeepSeek 和 `.benchmarks` | 降低分支堆积 | 中：外部凭证 / 仓库 | `scripts/test-full.sh` 和 push 结果 | DeepSeek key / benchmark repo | 不作为本轮 init 体验切片 |

排序结论：

1. 选择 A，因为它直接接在上一轮 Workflow 补充即时反馈之后：用户现在能看到 workflow note 的影响，但如果发现错误还不能低成本修正。这是同一条 CLI 用户旅程上的完整纠错闭环，风险低、可测试、可独立验收。
2. B 和 C 留作后续，因为它们涉及长期 schema / candidate governance，不应和小型 CLI 控制流修复混在一起。
3. D 仍是工程治理候选，但不是本轮 init 体验推进。

本轮 milestone：

作为 Harness Maintainer，当我在最终确认阶段发现 Workflow 补充写错或需要清空时，我可以输入 `back` 并选择 `workflow` 只返回 Workflow 补充步骤，重新输入后看到即时影响和设计预览刷新，并且最终 `.ai` 资产只保存最新 Workflow 补充，从而不用取消整次 init 或接受错误人工说明。

## 验收标准

1. 最终确认的返回提示必须包含 `workflow=Workflow补充`。
2. 输入 `back` -> `workflow` 后，CLI 必须重新询问 workflow note，并在有新 note 时再次展示 `Workflow 补充理解` / `Workflow 补充影响`。
3. 重新预览必须展示最新 `Workflow 补充约束`。
4. 写入后的 `interaction-decisions.yaml`、`project-context.md` 和 `human-input-needed.md` 只包含最新 workflow note，不包含被替换的旧 note。
5. 如果用户返回 workflow 并直接回车，应允许清空 note，最终不持久化旧 note。
6. 不修改 workflow routing policy、schema、LLM prompt 或 asset writer routing 逻辑。
7. 先写失败 integration 测试，再实现；运行目标测试、相关 guided init tests 和 `scripts/test-fast.sh`。

## 决策与取舍

- 复用现有 `WorkflowConfirmation` 数据结构，通过重新调用 `_show_workflows()` 替换内存态。
- `back` 菜单仅增加 `workflow` 目标，不新增更多导航状态。
- 不重新跑 candidate review 或 weapon selection，因为 workflow note 当前是 review-only 人工说明，不参与正式 routing 生成。
- 清空 workflow note 使用空输入表达，符合 `_show_workflows()` 现有语义。

## Assumptions / Risks

- workflow note 尚未进入正式资产前只存在于内存态 `workflow_confirmation`，因此替换它不会产生迁移或回滚问题。
- 用户可能希望返回 workflow 后也改 workflow routing policy；本轮明确不支持，仍通过文案和候选治理边界处理。
