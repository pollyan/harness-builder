# Maturity Driven Init Summary Design

## North Star Capability

本轮对应 Maturity & Evolution、CLI Experience、Benchmark / Review Intelligence。目标是让首次 `init` 不再只告诉用户“文件已经生成”，而是在完成时用成熟度框架解释当前等级、阻断项和下一步入口，并把同样信息写入稳定的 `.ai/init-summary.md`。

## Current State Gap Analysis

| 维度 | 目标态 | 当前已有 | 缺口 | 本轮判断 |
| --- | --- | --- | --- | --- |
| 用户工作流 | `init` 是成熟度驱动的主入口 | guided init 已有中文扫描解释、最终确认和资产写入 | 完成后仍只输出生成目录，用户需要自行找文件理解下一步 | 本轮优先 |
| 成熟度模型 | 用户能看到当前等级、阻断项和下一阶段建议 | `.ai/maturity-score.yaml`、`.ai/maturity-report.md` 已生成 | CLI 输出没有消费成熟度摘要；缺少专门的 init 完成摘要文件 | 本轮优先 |
| 资产生成 | 语义 Markdown 有稳定章节和可审计来源 | maturity report / evolution plan 已存在 | 缺少面向首次 init 旅程的“下一步入口”资产 | 本轮新增 |
| Runtime 边界 | 首次 init 不执行 self-improve 或 task runtime | 当前无 `run` 命令，init 不建 `.ai/task-runs` | 完成摘要需要明确这个边界，避免用户误解 | 本轮包含 |
| 已有 Harness 维护入口 | 再次 init 展示状态并给动作菜单 | 当前会重新走 init 写入链路 | 需要更大交互和状态机设计 | 暂缓 |
| 自动 benchmark | 首次 init 可围绕 benchmark 解释健康度 | benchmark 命令独立存在 | init 内默认 benchmark 涉及耗时和失败体验 | 暂缓 |

## Decisions

- 新增语义资产 `.ai/init-summary.md`，不是机器消费 schema。它稳定包含：`## 当前成熟度`、`## 主要阻断项`、`## 建议下一步`、`## 推荐入口文件`、`## 本次未执行的事项`。
- `write_report_assets` 直接基于已有 `MaturityReport` 生成摘要，避免重复评估成熟度。
- CLI `init` 完成后读取 `.ai/maturity-score.yaml` 和 `.ai/init-summary.md` 可验证地打印简短中文摘要；若这些文件缺失或 schema 损坏，按现有 no silent fallback 原则显式失败。
- 本轮不改变 `--non-interactive` 自动化语义，不默认运行 `self-improve`、LLM maturity review、asset candidate generation、benchmark 或 Runtime task execution。
- 本轮不实现已有 `.ai` 的再次 init 状态感知菜单；它保留在 todo 中作为后续切片。

## User Visible Behavior

`harness-builder-agent init --non-interactive --repo <repo>` 完成后输出应包含：

- 当前成熟度，例如 `当前成熟度：L2`。
- 最多 3 条阻断项摘要。
- 最多 3 条建议下一步。
- 推荐入口 `.ai/init-summary.md`、`.ai/maturity-report.md`、`.ai/human-input-needed.md`。

目标仓库 `.ai/init-summary.md` 应为人类可读 Markdown，帮助 Harness Maintainer 知道初始化后先看什么、为什么看，以及哪些能力本次没有默认执行。

## Acceptance Criteria

- Integration：Java fixture `init --non-interactive` 生成 `.ai/init-summary.md`，文件包含稳定章节、当前成熟度、阻断项、推荐下一步和推荐入口文件。
- Integration：CLI init 输出包含 `当前成熟度`、`.ai/init-summary.md`、`.ai/maturity-report.md`，不只输出生成目录。
- Guided integration：默认 guided happy path 完成后也输出成熟度摘要。
- Benchmark：新增 required file / content check，确保 `.ai/init-summary.md` 存在且包含成熟度主线章节、下一步入口和 no-runtime 边界。
- E2E：fixture end-to-end 检查 init summary 存在。
- Docs：README、init workflow、testing strategy、evolution log 同步说明该首次 init 摘要资产。

## Risks

- 摘要可能和 `maturity-report.md` 内容重复。本轮接受轻量重复，因为它面向不同用户旅程：`maturity-report` 是详细评估，`init-summary` 是初始化完成后的入口指引。
- CLI 输出依赖成熟度文件，如果未来 init 失败在写报告前中断，命令应继续按失败处理，不输出假摘要。
- 后续若 init 默认运行 benchmark，需要把 benchmark 结果整合进同一 summary，而不是新增第三份完成报告。
