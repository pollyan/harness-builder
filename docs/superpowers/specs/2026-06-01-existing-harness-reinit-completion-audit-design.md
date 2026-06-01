# Existing Harness Reinit 完成审计

## Current State Gap Analysis

事实源快照：
- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、当前 `cli.py` / `interactive_init.py` / existing Harness integration tests、最近 spec / plan / evolution log。
- 按需未展开：`docs/engineering/llm-contracts.md`、`sensor-and-gate-rules.md` 和完整 benchmark 实现；本轮不改 LLM、Sensor、benchmark 规则或 `.ai` schema。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. reinit 成功完成后保留审计并显示交付摘要 | 上轮 Gate / 新发现 | Maintainer 选择 `reinit` 并最终确认写入后，trace summary 仍能审计这是现有 Harness 重新生成，同时 CLI 仍展示首次 init 的交付摘要 | reinit 取消已保留 `existing_harness_action=reinit`；普通维护动作不会显示初始化完成摘要 | 成功路径 `trace.finish("completed", ...)` 丢失 reinit 来源；如果直接补 `existing_harness_action`，当前 `_should_render_initial_init_completion()` 会误把 reinit 完成当成普通维护动作 suppress 摘要 | 保护已有 Harness 覆盖路径的可审计性，同时不牺牲重新生成后的交付说明 | 低到中：只改 trace summary 和 CLI render 条件，但要避免 `exit` / `assess` / `benchmark` 等维护动作误显示完成摘要 | integration CLI transcript + trace summary；existing Harness action 回归 | 无外部服务；mock scan 即可 | 选择 `9. reinit` 后完成 guided init，输出含 reinit 边界和 `== 初始化完成 ==`；trace completed 且 summary 含 `existing_harness_action=reinit`、`primary_stack`、`command_count`；普通 exit 仍无完成摘要 | 本轮 |
| B. push / full regression 外部 gate | 持续 Gate | 完整工作包 push 前可运行 full regression 并通过真实 DeepSeek acceptance | fast 可运行；full 在 acceptance 请求 DeepSeek 时失败或被外发审批拒绝 | 当前无法在 sandbox 内解析 `api.deepseek.com`，非 sandbox full 会向外部服务发送本地 fixture / benchmark 内容而被拒绝 | 影响远端同步可信度，但不阻塞本地小切片继续演进 | 高：依赖网络、外部 API 和审批 | `scripts/test-full.sh`、审批结果 | DeepSeek API、网络和外发许可 | full 通过后才能 push；当前作为外部阻塞记录 | 保留 Gate 候选，不作为代码 milestone |
| C. reinit 扫描后最终取消的审计细节 | 上轮 Gate 衍生 | Maintainer 选择 reinit、完成扫描和预览后取消时，trace 能区分已扫描但未写入 | 当前 `_cancel_guided_init(... before_scan=False)` 会记录 failed + reinit action | 取消 summary 还不包含 scanned / write_skipped 等更细状态 | 提升审计细粒度，但用户价值弱于完成路径审计，且取消路径已有基本边界 | 低 | integration cancel after preview | 无 | 取消后 trace 明确 scanned=true/write_skipped=true | 下一轮候选，需重新评估 |

排序结论：
1. 选择 A，因为它直接服务 `init-north-star.md` 的“再次进入已有 Harness”和“写入后的交付摘要”：reinit 是显式覆盖/重新生成路径，完成审计和终端交付说明必须同时成立。
2. B 是 push gate，不是当前代码能力缺口；继续记录为外部前置。
3. C 有价值但只是取消审计细化；A 保护完成路径，是更核心的用户成功场景。

本轮 milestone：

作为 Harness Maintainer，当我在已有 Harness 维护入口选择 `reinit` 并最终确认重新生成时，我可以在 trace summary 中看到这次完成来自 `existing_harness_action=reinit`，同时仍看到 `== 初始化完成 ==` 交付摘要，从而既能审计覆盖来源，也不会丢失重新生成后的交付说明。

## 设计

1. 成功路径 trace summary
   - `run_guided_init()` 已通过 `_is_existing_harness_reinit_requested(trace)` 识别 reinit intent。
   - 写入成功后的 `trace.finish("completed", ...)` 在 `reinit_requested=True` 时追加 `existing_harness_action: reinit`。
   - 不改变非交互 init，也不改变已有 Harness `exit`、`assess`、`improve`、`benchmark`、`recommend-workflow`、`review-candidate`、`review-human-input`、`self-improve`、`review-initial-candidate` 等维护动作 summary。

2. CLI completion 渲染
   - `_should_render_initial_init_completion()` 继续 suppress 普通已有 Harness 维护动作。
   - 但 `existing_harness_action=reinit` 且 trace status 为 `completed` 时，应视为重新生成成功，继续渲染首次 init completion message。
   - 失败或取消的 reinit 不会进入 completion render，因为 `typer.Exit` 已提前抛出；判断仍保持稳健。

3. 文档事实源
   - README 和 `docs/engineering/init-workflow.md` 补充稳定规则：reinit 成功完成会保留 reinit trace summary，同时渲染初始化完成交付摘要。
   - `docs/evolution-log.md` 记录本轮 gap、取舍、验证和 Gate。

## 验收标准

- integration RED：选择 existing Harness `9. reinit` 并完成 guided init 时，当前 trace summary 缺少 `existing_harness_action=reinit`。
- 实现后：
  - CLI 输出包含 reinit 边界说明。
  - CLI 输出包含 `== 初始化完成 ==` 和 `本次已生成`。
  - 最新 init trace `status=completed`。
  - trace summary 包含 `existing_harness_action=reinit`、`primary_stack=java-spring` 和 `command_count=1`。
  - existing Harness `exit` 回归仍不扫描、不覆盖、不显示 `== 初始化完成 ==`。
- 文档 diff 同步 README、init workflow 和 evolution log。
- 提交前运行 `scripts/test-fast.sh`。
- push 前必须运行 `scripts/test-full.sh`；若 full gate 仍因 DeepSeek DNS / 外发审批失败，则只本地 commit，不 push。

## Assumptions / Risks

- Assumption：`existing-harness` event 的 `details.action=reinit` 是当前稳定的 reinit intent 来源，已被上一轮取消边界使用。
- Risk：如果未来新增某个 existing Harness action 也会继续进入完整 init 写入流程，需要把 completion render 条件从单个 `reinit` 扩展为白名单，而不是回到“没有 action 才显示”。
- Risk：本轮不改变 writer 覆盖策略；reinit 的正式资产写入语义沿用首次 init 最终 confirm 后写入。

## Sub Agent

本轮按目标模式尝试启动只读 explorer 交叉验证 gap，环境返回 `agent thread limit reached`。主线程继续完成调研、TDD、实现、验证和提交。
