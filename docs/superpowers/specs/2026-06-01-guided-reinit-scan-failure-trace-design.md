# Guided Reinit 扫描失败 Trace 审计设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/llm-contracts.md`、`docs/evolution-log.md`、近期 scan failure / reinit 相关 spec、`interactive_init.py`、`guided_scan_presentation.py` 和 `tests/integration/test_init_on_fixture_projects.py`。
- 按需未展开：`docs/engineering/architecture.md`、`docs/engineering/sensor-and-gate-rules.md`。本轮不修改架构、writer、Sensor、benchmark check 或 Runtime 契约。
- Sub agent：按目标模式尝试启动只读 explorer 审查 guided reinit scan failure，当前环境返回 `agent thread limit reached`，因此本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. guided `reinit` 扫描失败应保留维护动作与未写入审计 | 新发现 / 上轮 Gate | Maintainer 选择 `reinit` 后如果 LLM / 网络 / schema 扫描失败，CLI 明确失败且 trace summary 说明这是 reinit 扫描失败、扫描未完成、正式资产未写入 | guided scan failure 已输出“扫描阶段失败”；reinit 启动取消、写入前取消和完成路径已保留 `existing_harness_action=reinit` | `run_guided_init()` 的 scan exception summary 只写 `error_type` 和 `scan_error`，丢失 `existing_harness_action=reinit`；也没有 `scan_completed=false` / `formal_assets_written=false` | 保护已有 Harness 重新生成的高信任失败边界；避免排查时把 reinit scan failure 误判为普通首次 init 失败或覆盖失败 | 低；只补失败 trace summary 和短错误一致性，不改扫描、LLM、writer 或 Runtime | integration mock `scan_repository()` 抛错，断言 CLI、trace summary/events 和正式资产 snapshot | 无外部依赖；不需要真实 DeepSeek | 本轮 |
| B. full regression / push gate 仍受真实 DeepSeek 网络与外发审批限制 | Gate | 完整工作包通过 `scripts/test-full.sh` 后再 push | `.env` 已配置 DeepSeek key，本地 fast 可运行；full gate 在 sandbox 内曾因 DNS 失败 | 需要真实外部 API 与真实仓库 evidence 外发许可；这不是代码内可消除的 init gap | 明确远端同步边界，避免误 push | 高；外部服务 / 权限 | `scripts/test-full.sh` 和 push 结果 | 网络、外部服务、审批 | 作为 push 前置，不进入本轮实现 |
| C. Existing Harness action runner 继续拆分错误边界 helper | 工程债 / 多轮 Gate | action-specific failure trace 复用统一 helper，减少每个 action 手写 summary 的漂移 | 已有多个维护动作和 reinit 路径各自写 trace summary | helper 分散，未来可能再次漏字段 | 降低维护入口演进成本 | 中；跨多个 action，回归面更大 | action-specific integration 回归 | 无外部依赖 | 下一轮候选 |

排序结论：

1. 选择 A。它直接服务 `init-north-star.md` 的“再次进入已有 Harness”“错误与边界”“不会在未确认时覆盖正式资产”和 LLM-first 显式失败原则；范围小、可测试、对用户审计价值独立。
2. B 是当前 push gate 的真实外部前置，但无法用本轮代码修改证明解决；继续保留为 push 判断条件。
3. C 有工程价值，但应在更多 action 漂移或重构收益明确时独立推进，不和 reinit scan failure 的用户故事混在一起。

## 本轮 milestone

作为 Harness Maintainer，当我在已有 Harness 维护入口选择 `reinit` 后重新扫描失败时，我可以在 CLI 中看到扫描阶段失败且未写入正式 Harness 资产，并在 trace summary 中看到这是 `existing_harness_action=reinit` 的扫描失败、`scan_completed=false`、`formal_assets_written=false`，从而能安全定位 DeepSeek / 网络 / schema 问题而不误判为普通首次 init 失败或覆盖失败。

## 需求

- guided scan failure 继续输出：
  - `扫描阶段失败`。
  - 错误类型和短错误摘要。
  - `未写入正式 Harness 资产`。
  - 检查 LLM 配置、网络或扫描错误的建议。
- trace event `scan failed` 必须包含 `error_type` 和短错误摘要。
- trace summary 必须包含：
  - `error_type`。
  - `scan_error`。
  - `scan_completed=false`。
  - `formal_assets_written=false`。
  - 如果本轮来自 existing Harness `reinit`，还必须包含 `existing_harness_action=reinit`。
- reinit scan failure 不得覆盖已有正式 Harness 资产，不得创建 Runtime 产物，不得展示 `== 初始化完成 ==`。
- 普通首次 guided scan failure 也应获得 `scan_completed=false` 和 `formal_assets_written=false` 的同类 summary 字段，保持失败审计一致。

## 非目标

- 不改变 `scan_repository()`、LLM prompt、schema、evidence expansion、self-check 或 scan reconcile 行为。
- 不改变已有 Harness `reinit` 成功写入语义，也不增加备份 / rollback 机制。
- 不修改 writer、benchmark、Sensor、Runtime task-run 或 action runner 架构。
- 不解决 `scripts/test-full.sh` 的外部 DeepSeek 网络 / 审批前置。

## 决策

- 复用 `_is_existing_harness_reinit_requested(trace)` 判断 reinit intent，避免改变 action runner 返回类型。
- guided scan failure 与非交互 scan failure 一样使用 `_short_error_message(exc)` 写 trace，避免多行异常或底层响应污染 summary。
- 失败 summary 使用显式布尔字段表达扫描未完成和正式资产未写入；正式 `.ai` 资产是否真的未改由 integration snapshot 断言。
- 保持 `raise typer.Exit(code=1)` 的失败边界，避免外层 `init failed` 事件混淆 scan 阶段定位。

## Assumptions / Risks

- `GenerationTrace.summary` 当前是 YAML 审计摘要，不是 Pydantic 机器契约；新增字段是向后兼容的审计增强。
- `reinit` intent 继续来自 `existing-harness` trace event 的 `details.action=reinit`，与前几轮已实现的启动取消、写入前取消和成功完成路径一致。
- 失败 summary 里的 `formal_assets_written=false` 是本阶段的过程事实；测试通过正式资产 snapshot 证明没有覆盖，而不是只相信字段。

## 验收标准

- 新增 integration RED：已有 Harness 选择 `9. reinit`、确认继续扫描后 mock scan failure，当前 trace summary 缺少 `existing_harness_action` / `scan_completed` / `formal_assets_written`。
- 实现后 targeted test 通过：
  - exit code 为 1。
  - 输出包含 reinit 启动边界、`扫描阶段失败`、错误摘要、未写正式 Harness 资产。
  - 输出不包含 `== 初始化完成 ==` 或 traceback。
  - 现有 `.ai/project-inventory.json`、`.ai/harness-config.yaml`、Guides、Sensors、Skills 等正式资产 snapshot 不变。
  - trace failed summary 包含 `existing_harness_action=reinit`、`scan_completed=false`、`formal_assets_written=false`、`error_type` 和 `scan_error`。
  - `events.jsonl` 只有 scan failed 阶段定位，不额外出现泛化 `init failed`。
- 回归普通 guided scan failure summary 字段、reinit cancel / completion 相关测试。
- 文档验证：README 和 `docs/engineering/init-workflow.md` 同步 reinit scan failure 审计规则。
