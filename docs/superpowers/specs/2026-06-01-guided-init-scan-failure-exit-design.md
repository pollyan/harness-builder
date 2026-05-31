# Guided Init 扫描失败退出边界硬化设计

## 背景

首次 guided `init` 的扫描阶段已经会在开始、完成和失败时输出中文进度与失败边界。但当前实现路径中，`scan_repository()` 抛出的原始异常会继续向外抛出，外层 `init_command()` 的通用异常处理也可能再次记录 `init failed`。这在 Typer `CliRunner` 和真实 CLI 场景中会带来两个问题：

- 用户看到扫描失败提示后，仍可能被 Python traceback 或原始异常语义干扰。
- generation trace 中的失败语义可能同时出现 `scan failed` 和外层 `init failed`，不利于后续诊断“失败发生在哪个阶段”。

本轮目标不是改变失败策略。扫描失败仍然必须失败，不能 silent fallback，也不能写入正式 Harness 资产；本轮只让失败边界更清楚、更可审计。

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/todos/` 相关条目、上一轮 guided scan progress spec / plan、当前 dirty diff。
- 已检查代码：`src/harness_builder_agent/cli.py`、`src/harness_builder_agent/tools/interactive_init.py`、`src/harness_builder_agent/tools/generation_trace.py`、`tests/integration/test_init_on_fixture_projects.py`。
- 按需未展开：benchmark scoring、已有 Harness 维护动作、asset writer 内容质量；本轮不改变写入成功路径和生成产物。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. guided init 扫描失败退出边界硬化 | 当前 dirty diff / 上一轮 Gate / init North Star | 扫描失败时 CLI 显式说明失败阶段、未写入正式资产、无 traceback；trace 只记录 scan failed 和 failed summary | 已有扫描开始/完成/失败文案；dirty diff 已初步透传 Typer exit 并 finish trace | 测试只覆盖屏幕输出和未写正式资产，未验证 trace 契约；spec/plan/evolution 未记录退出语义 | 提升失败诊断可信度，保护真实 LLM / 网络 / schema 失败场景下的用户信任 | 低；只触碰 guided scan failure 和 CLI exception 边界 | integration 可断言 output、trace.yaml、events.jsonl、无正式资产 | 无外部凭证；复用 mock scan failure | 失败路径 integration + 文档 diff + fast regression | 本轮 |
| B. 用户自然语言补充与 self-check resolution 影响成熟度/推荐说明 | 上一轮 Gate / init North Star | 用户补充和二次自检结论能在成熟度预览、推荐解释和 init summary 中形成可审计影响链路 | 自然语言补充已落入 decisions / guides；self-check 已进入 scan metadata 和 questionnaire reason | 影响链路在 CLI/summary 中还不够集中表达 | 强化渐进式协作和智能闭环 | 中；需避免把人工补充伪装成扫描事实 | guided integration、asset Markdown 断言、summary 断言 | 需要稳定区分事实/推断/人工补充 | 后续作为纵向体验切片 | 下一轮候选 |
| C. 路径型 claim validation | 子代理候选 / 深度扫描可信度 | LLM 模块、风险、配置、CI 路径都有 supported / unknown / conflict 审计 | stack claim 和 command source 已有验证；路径型 claim 尚未统一状态化 | 用户仍可能看不出某些路径 claim 是否被 evidence 支持 | 降低 LLM 幻觉风险 | 中；新增 schema / reconciler 契约 | schema unit、reconciler unit、CLI transcript | 需要设计 claim kind/status 契约 | 独立 hardening 里程碑 | 后续 |

排序结论：

1. 选择 A。它已经在工作区形成小而明确的工程信任切片，直接服务 `init-north-star.md` 的“错误信息包含原因、影响和下一步处理建议”与“扫描失败未写入正式 Harness 资产”要求；补齐 trace 测试和文档后即可成为独立可审查 commit。
2. B 用户价值更强，但会触碰成熟度预览、推荐解释和资产摘要，范围明显大于当前 dirty diff，不适合与扫描失败边界混在同一轮。
3. C 是重要的仓库理解可信度 hardening，但需要新 schema 和 reconciler 设计，应独立进入下一轮 Gap Analysis。

本轮 milestone：

作为 Harness Maintainer，当我首次 guided `init` 一个仓库且扫描阶段因为 LLM、网络或 schema 问题失败时，我可以在 CLI 中看到清晰的扫描失败说明和“未写入正式 Harness 资产”的边界，并且后续维护者可以从 trace 中确认失败只发生在 scan 阶段，从而更快定位问题而不误以为系统生成了不可信 Harness。

## 设计

### CLI 失败边界

`run_guided_init()` 在扫描失败时：

- 记录 `scan failed` event，details 包含 `error_type` 和短错误消息。
- 输出现有中文失败说明：`扫描阶段失败`、原因、未写入正式 Harness 资产、检查 LLM 配置 / 网络 / 扫描错误。
- 调用 `trace.finish("failed", {"error_type": ..., "scan_error": ...})`，让 `.ai/runs/<run_id>/trace.yaml` 和 `decision-log.md` 可审计。
- 抛出 `typer.Exit(code=1)`，让 Typer 以 CLI 失败退出，而不是把原始 Python 异常继续展示给用户。

`init_command()` 对 `typer.Exit` 和 `typer.Abort` 直接透传，不再进入通用 `except Exception` 分支，避免外层写入额外 `init failed` event。

### 边界

- 不改变非交互 init。
- 不改变 `scan_repository()`、LLM、schema 或 fallback 策略。
- 不在扫描失败时写入正式 `.ai/project-inventory.json`、`.ai/harness-config.yaml`、Guides、Sensors 或 Workflow Skills。
- generation trace 目录可以存在，因为它是命令过程审计，不是正式 Harness 资产。

## 验收标准

1. guided scan failure CLI 输出包含扫描进度、`扫描阶段失败`、原始错误摘要、`未写入正式 Harness 资产` 和重试建议。
2. CLI 输出不包含 Python traceback，`CliRunner` 捕获到的异常不再是原始 `RuntimeError`。
3. `.ai/runs/<run_id>/trace.yaml` 状态为 `failed`，summary 包含 `error_type=RuntimeError` 和 `scan_error=synthetic scan failure`。
4. `.ai/runs/<run_id>/events.jsonl` 包含 `stage=scan`、`event_type=failed`，details 包含错误类型和错误消息。
5. `.ai/runs/<run_id>/events.jsonl` 不包含外层 `stage=init` 的 failed event，避免重复失败语义。
6. 扫描失败不写入正式 Harness 资产。
7. `docs/engineering/init-workflow.md`、spec/plan 和 `docs/evolution-log.md` 同步记录该失败边界。

## Assumptions / Risks

- `typer.Exit` 会隐藏原始 Python traceback；错误摘要仍通过 CLI 文案、trace details 和 decision log 保留。
- trace 目录在失败时存在是期望行为，因为它是审计产物，不代表正式 Harness 已生成。
- 该变更只收敛 guided CLI 失败体验；真实 DeepSeek 失败、schema 失败和网络失败仍按 no silent fallback 显式失败。
