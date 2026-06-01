# Existing Harness Reinit 边界设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、近期 spec / plan 列表、`interactive_init.py`、`existing_harness_action_runner.py` 和 existing Harness integration tests。
- 按需未展开：`docs/engineering/architecture.md`、`llm-contracts.md`、`sensor-and-gate-rules.md`，本轮不改架构、LLM、Sensor 或 benchmark contract。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Existing Harness `reinit` 后应明确重新生成边界并保留取消审计 | 新发现 / init North Star 再次进入已有 Harness | Maintainer 显式选择 `reinit` 后，CLI 告知将重新扫描现有 Harness、最终 confirm 前不会覆盖；若取消，trace 保留 `existing_harness_action=reinit` | 已有 Harness 维护入口有菜单，`reinit` 返回首次 init 流程；最终 confirm 前才写入 | 选择 `9. reinit` 后没有 reinit 专属边界说明；取消时 trace summary 只有 `cancelled`，丢失选择 reinit 的审计语义 | 保护已有 Harness 不被误解为立即覆盖；提升再次进入维护入口的信任 | 低；只改 guided CLI 文案、trace summary 和取消出口，不改 writer、schema 或扫描 | integration：已有 Harness 选择 `9` 后取消，断言不扫描、不覆盖、输出 reinit 边界、trace failed 且 summary 含 reinit | 无外部依赖 | targeted RED 后 pass；fast regression | 本轮 |
| B. guided init 普通取消也应避免 Typer `Aborted!` 并输出正式资产边界 | 新发现 / CLI 失败边界 | 任意 guided cancel 都给出中文取消摘要和未写资产说明 | 启动说明已说可取消；trace 记录 cancelled | 当前 `typer.Abort()` 可能输出通用英文 aborted，取消摘要不够产品化 | 改善取消体验 | 低，但覆盖所有 cancel 出口，范围略宽 | integration cancel before scan / final cancel | 无 | 可并入 A 的 helper，但不扩大为独立全链路重构 | 作为 A 的强相关小修复处理 |
| C. full regression / push gate 仍受 DeepSeek DNS 和外发审批限制 | Gate 候选 | push 前 full gate 完成 | fast 可过；full acceptance 需要 DeepSeek | 当前 sandbox DNS 失败，非 sandbox 被拒绝因外发本地仓库内容 | 影响同步远端，不影响本轮本地实现 | 外部权限 / 服务 | `scripts/test-full.sh` | 需要网络 / 外发许可 | 记录，不用代码规避 | 保留为 push gate 外部前置 |

排序结论：

1. 选择 A，并把 B 中“取消出口中文摘要”作为同一用户故事的紧密边界处理。`reinit` 是已有 Harness 维护入口中最容易触及正式资产覆盖语义的动作，必须比普通首次 init 更清楚地说明不会在最终确认前覆盖。
2. C 是真实阻塞，但不适合用代码绕过，也不能降低 acceptance 要求。

## 本轮 milestone

作为 Harness Maintainer，当我在已有 Harness 维护入口显式选择 `reinit` 准备重新生成时，我可以在继续扫描前看到重新生成现有 Harness 的边界说明，并且如果我取消，CLI 与 trace 都明确记录这是 reinit 取消且未扫描、未覆盖正式资产，从而能安全地决定是否继续重新生成。

## 需求

- 选择 existing Harness `reinit` 后，在第一次重新扫描确认前输出 reinit 专属说明：
  - 已选择重新生成现有 Harness。
  - 接下来会重新扫描并重新生成候选资产。
  - 最终 `confirm` / `确认` 前不会覆盖正式 `.ai` Harness 资产。
  - 如需保留现有 Harness，可取消并备份。
- 用户在 reinit 后第一次确认处取消：
  - 不调用 `scan_repository()`。
  - 不覆盖 `.ai/project-inventory.json`、`.ai/harness-config.yaml`、`.ai/init-summary.md` 等正式资产。
  - CLI 输出中文取消摘要，说明未扫描、未覆盖正式资产、未创建 Runtime 产物。
  - trace status 为 `failed`，summary 至少包含 `cancelled=true` 和 `existing_harness_action=reinit`。
- 普通 guided cancel 可复用中文取消摘要，但不伪造 reinit action。

## 非目标

- 不改变 `--non-interactive` 自动重新生成语义。
- 不改变 writer 覆盖策略、`.ai` schema、LLM scan、benchmark 或 Runtime contract。
- 不新增 partial Harness repair / backup / dry-run 命令。
- 不在用户确认前自动备份或修改正式资产。

## 决策

- 用 trace events 判断本轮是否已经选择 `existing-harness` `action=reinit`，避免改变 `run_existing_harness_action()` 的返回类型。
- 新增 guided cancel helper，统一 finish trace 和中文取消输出。
- `reinit` action 仍只表示显式继续到重新生成流程，不在 action runner 内执行扫描或写入。

## Assumptions / Risks

- 选择 `reinit` 的 Maintainer 已表达“可能重新生成”的意图，但仍需要一次继续扫描确认和最终写入确认。
- 通过 trace events 推断 reinit intent 依赖当前 stable event details；若未来 trace event schema 调整，需要同步 helper 测试。
- 中文取消摘要会替代 Typer 默认 aborted 体验；这是产品化 CLI 的期望行为。

## 验收标准

- 新增 integration test 先红：已有 Harness 选择 `9` 后取消，当前缺少 reinit 专属说明和 trace summary action。
- 实现后 targeted test 通过：输出包含 reinit 边界和中文取消摘要；输出不包含初始化完成；scan mock 未被调用；正式资产 snapshot 未变；trace failed 且 summary 含 `existing_harness_action=reinit`。
- 回归普通 partial Harness 启动取消：仍不扫描、不覆盖，trace failed，不伪造 reinit。
- 文档验证：`docs/engineering/init-workflow.md` 和 README 同步 reinit 边界。
