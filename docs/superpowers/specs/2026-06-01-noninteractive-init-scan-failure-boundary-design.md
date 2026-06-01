# 非交互 init 扫描失败边界设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/llm-contracts.md`、近期 spec / plan 列表、`interactive_init.py`、`cli.py` 和 guided scan failure 测试。
- 按需未展开：`docs/engineering/architecture.md`、`sensor-and-gate-rules.md`，本轮不改架构、sensor 或 benchmark contract。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. `--non-interactive` 扫描失败应短错误消息和 scan trace 定位 | 新发现 / 上轮 full gate 失败观察 | 自动化 / acceptance 中 LLM、网络或 schema 扫描失败时，CLI 明确说明 scan 阶段失败、错误类型、未写正式资产，并留下 `scan failed` trace | guided `init` 已有 scan failure 友好输出和无 traceback 测试；非交互路径直接调用 `scan_repository()` | 非交互扫描异常会冒到 `cli.py`，外层记录泛化 `init failed` 并 re-raise，真实 CLI 可能展示 Python/Rich traceback，trace 阶段定位被混淆 | 保护 CI、acceptance 和目标模式自动化定位能力；符合 LLM 不可用必须显式失败且 no silent fallback | 低到中；只改错误边界，不改扫描、schema、writer 或 acceptance 语义 | integration monkeypatch `scan_repository()` 抛错，断言 CLI 输出、exit code、trace、无正式资产、无 traceback、无外层 `init failed` | 无外部依赖；不需要真实 DeepSeek | targeted RED 后 pass；`scripts/test-fast.sh` | 本轮 |
| B. full regression / push gate 继续被 DeepSeek DNS 阻塞时的运行提示 | Gate 候选 | push 前 full gate 能稳定完成或明确区分外部网络阻塞 | `.env` 已有 DeepSeek key；`scripts/test-full.sh` fast 通过后 acceptance DNS 失败 | 当前环境无法解析 `api.deepseek.com`，但这属于外部网络，不是代码行为；之前非 sandbox 外发真实仓库 evidence 未获授权 | 可以减少 push 困惑，但不能在代码内解决网络访问 | 高；涉及外部服务、权限和真实仓库 evidence | 只能通过实际 full gate / 网络验证 | 需要外部网络许可或服务可用 | 本轮无法用代码证明 | 保留为 push gate 外部前置，不作为实现 milestone |
| C. partial core 状态的自动 repair / reinit 边界 | 上轮 Gate 旁支 | partial `.ai` core 可被显式 repair 或 reinit 路由 | guided 启动已说明 partial 状态，最终 confirm 前不覆盖 | 还没有自动修复 partial `.ai` 的专家命令 | 未来提升已有 Harness 恢复能力 | 中到高；涉及正式资产覆盖策略 | integration + schema migration | 需要产品边界决策 | 后续重新拆分 | 下一轮候选 |

排序结论：

1. 选择 A。它直接服务 init North Star 的“错误与边界清晰”“CLI 友好”和自动化信任；上轮 full gate 的真实失败也暴露了该体验风险。改动边界小，可用 mock scan failure 精确验证，不依赖真实 DeepSeek。
2. B 是当前 push 阻塞的真实外部前置，但不是本轮可通过代码消除的产品 gap；仍按 AGENTS push 规则保留。
3. C 有价值，但它涉及更大的恢复 / 覆盖策略，不如 A 更独立、可验收。

## 本轮 milestone

作为 CI / acceptance 维护者，当我运行 `harness-builder-agent init --non-interactive` 且 LLM 扫描、网络或 schema 阶段失败时，我可以看到简短、中文、阶段明确的 scan 失败说明，并在 generation trace 中看到 `scan failed` 和错误类型，同时确认没有写入正式 Harness 资产，从而能快速定位外部服务或扫描契约问题，而不是被 Python traceback 或泛化 `init failed` 混淆。

## 需求

- `run_non_interactive_init()` 在 `scan_repository()` 抛出异常时捕获并处理 scan 阶段失败。
- CLI 输出必须说明：
  - `init --non-interactive` 扫描失败。
  - 阶段是 scan。
  - 错误类型和短错误摘要。
  - 未写入正式 Harness 资产。
  - 建议检查 DeepSeek / LLM 配置、网络或扫描错误。
- trace 必须：
  - 保留 `scan started`。
  - 写入 `scan failed`，details 含 `error_type` 和短错误。
  - `trace.yaml` status 为 `failed`，summary 含 `error_type` 与 `scan_error`。
  - 不额外写入外层 `init failed` 事件。
- 失败后必须以非 0 退出码结束，不能吞异常、不能 fallback、不能写正式 `.ai/project-inventory.json` 等资产。
- 输出不能包含原始 Python traceback。

## 非目标

- 不改变 guided init 的扫描失败进度展示。
- 不改变 `scan_repository()`、LLM prompt、schema、writer 或 acceptance 成功路径。
- 不为非交互模式增加 guided 进度条或交互流程。
- 不修复外部 DeepSeek DNS / 网络可达性。

## 决策

- 复用 `interactive_init.py` 内已有短错误摘要工具，避免长 traceback、长 API 响应或多行错误污染 CLI。
- 非交互路径只在扫描阶段捕获异常；写资产阶段的异常继续由外层命令处理，因为其阶段不是 scan。
- 捕获后 `raise typer.Exit(code=1)`，让 `cli.py` 的 `except (typer.Exit, typer.Abort)` 直接透传，避免重复记录 `init failed`。

## Assumptions / Risks

- 非交互自动化不需要 guided 进度契约，但失败时需要稳定、机器可审计的阶段定位。
- 短错误摘要可能截断底层异常；完整可复现定位仍依赖本地日志、trace 和重跑。
- 如果未来要统一所有命令错误渲染，应另起跨命令错误处理 milestone。

## 验收标准

- 新增 integration test 先红：mock `scan_repository()` 抛 `RuntimeError`，当前非交互路径缺少目标输出 / trace。
- 实现后 targeted test 通过：exit code 非 0，输出含 scan 阶段失败说明、错误类型、短错误、未写正式资产、建议检查 LLM / 网络；不含 `Traceback`；`result.exception` 不是原始 `RuntimeError`。
- trace 验证：`trace.yaml` failed，summary 为 scan error；`events.jsonl` 有 `scan failed`，无 `init failed`。
- 文件验证：不生成 `.ai/project-inventory.json`、`.ai/harness-config.yaml`、`.ai/init-summary.md` 等正式 Harness 资产，只允许 `.ai/runs/*` trace。
- 文档验证：`docs/engineering/init-workflow.md` 与 README 同步非交互 scan failure 边界。
