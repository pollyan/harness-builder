# Init 扫描失败短错误与未写入审计设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/llm-contracts.md`、`docs/evolution-log.md`、`interactive_init.py`、`guided_scan_presentation.py` 和 scan failure 相关 integration tests。
- 按需未展开：`docs/engineering/architecture.md`、`docs/engineering/sensor-and-gate-rules.md`。本轮不修改架构、Sensor、benchmark 或 Runtime。
- Sub agent：按目标模式尝试启动只读 explorer 审查 init scan failure 输出与 trace 一致性，当前环境返回 `agent thread limit reached`；本轮由主线程完成调研、TDD、实现和验证。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. init scan failure CLI 使用短错误且 trace summary 统一记录未写入边界 | 新发现 / 上轮 Gate | guided 与 `--non-interactive` scan failure 都给 Maintainer / CI 看到短错误、scan 阶段、未写正式资产，并在 trace summary 中稳定记录 `scan_completed=false` / `formal_assets_written=false` | guided trace event / summary 已用短错误并有未写入字段；非交互 CLI 用短错误但 summary 只写 error；guided CLI 仍直接打印原始 exception | guided CLI 多行或超长 LLM / schema 错误会污染终端；非交互 trace summary 缺少和 guided 一致的未写入字段 | 保护 LLM-first 显式失败体验，降低真实 DeepSeek / schema 问题定位成本；让 scan failure 审计契约跨模式一致 | 低；只改错误展示和 summary 字段，不改扫描、LLM、writer 或 Runtime | integration mock 多行异常，断言 CLI 单行短错误、trace summary 字段、无正式资产 | 无外部依赖 | 本轮 |
| B. full regression / push gate 外部 DeepSeek 验收 | Gate | 完整工作包通过 `scripts/test-full.sh` 后 push | fast 可过；`.env` 有 key；真实 benchmark 仓库存在 | sandbox DNS 失败；非 sandbox full gate 因外发本地 fixture / benchmark 仓库内容到 DeepSeek 被拒 | 解决后才能 push，但不是代码内可修复 gap | 高；外部服务与审批 | `scripts/test-full.sh` | 网络、外部 DeepSeek、外发审批 | 保留为 push 前置 |
| C. Existing Harness action runner 失败 summary helper 抽取 | 上轮 Gate / 工程债 | action-specific failure trace 复用统一 helper，减少未来漏字段 | 多个 action 已有 action-specific trace；部分近期切片补了 reinit / review failure | helper 分散，未来维护入口继续演进时可能出现字段漂移 | 降低维护入口复杂度 | 中；跨多个 action，回归面大 | 多个 existing Harness action integration | 无外部依赖 | 下一轮候选 |

排序结论：

1. 选择 A。它直接服务 init North Star 的“错误信息包含原因、影响和下一步处理建议”“LLM 不可用必须显式失败”“终端输出可读”，并且延续上一轮 scan failure 审计线索形成完整跨模式契约。
2. B 是真实 push 阻塞，但需要外部网络和审批，不作为本轮代码 milestone。
3. C 有长期工程收益，但缺少本轮 A 这样直接用户可见的失败体验价值，继续保留为后续候选。

## 本轮 milestone

作为 Harness Maintainer 或 CI 维护者，当 `harness-builder-agent init` 在 guided 或 `--non-interactive` 扫描阶段因为 DeepSeek / LLM / schema 错误失败时，我可以看到短小、单行、阶段明确的错误摘要，并在 trace summary 中看到扫描未完成、正式资产未写入，从而能快速定位真实问题而不会被多行 Python / API 细节或模式间不一致的审计字段干扰。

## 需求

- guided scan failure CLI 的 `原因` 行必须使用 `_short_error_message()` 产生的短错误摘要，而不是直接打印原始 exception。
- guided scan failure event 和 summary 继续使用同一个短错误摘要。
- `--non-interactive` scan failure summary 也必须包含 `scan_completed=false` 和 `formal_assets_written=false`，与 guided failure 对齐。
- 两种模式都不得写入正式 Harness 资产，不得创建 Runtime 产物，不得产生外层泛化 `init failed` event。

## 非目标

- 不修改 DeepSeek 调用、LLM prompt、schema、evidence planner、scan reconcile 或 retry 策略。
- 不改变已有 reinit 成功 / 取消 / scan failure action 字段。
- 不改变 writer、benchmark、Sensor 或 Runtime。
- 不解决 full regression 的外部 DeepSeek 网络 / 审批前置。

## 决策

- 将 guided scan failure renderer 增加可选 `error_message` 参数，由 `interactive_init.py` 传入已计算的短错误。
- 保留 renderer 对旧调用的兼容：没有传 `error_message` 时仍使用 `str(exc)`。
- 非交互 summary 增加显式布尔字段，不改变 CLI 文案。

## Assumptions / Risks

- `GenerationTrace.summary` 是审计摘要，新增字段向后兼容。
- 短错误摘要折叠多行错误，可能隐藏底层长响应；这是 CLI 可读性和非敏感输出的取舍，真实定位仍可通过重跑和底层日志进行。
- 本轮不把短错误 helper 移到公共模块，避免为了一个小切片制造跨模块重构。

## 验收标准

- 新增 / 增强 integration RED：
  - guided scan failure 抛多行 `RuntimeError` 时，当前 CLI 原样展示多行原因，测试先失败。
  - `--non-interactive` scan failure trace summary 缺少 `scan_completed` 和 `formal_assets_written`，测试先失败。
- 实现后：
  - guided CLI 输出 `RuntimeError: <折叠后的短错误>`，不包含原始多行错误。
  - guided trace event 和 summary 的 `scan_error` / `error` 与 CLI 短错误一致。
  - non-interactive summary 包含 `scan_completed=false` 和 `formal_assets_written=false`。
  - 两种模式均不写正式 `.ai` 资产，无 traceback，无外层 `init failed` event。
- 运行 targeted tests、init integration 全文件、`compileall`、`git diff --check`、`scripts/test-fast.sh`；push 前尝试 `scripts/test-full.sh` 并按外部限制记录结果。
