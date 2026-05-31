# Init CLI 交付摘要增强设计

## 背景

本轮 Current State Gap Analysis 对照 `docs/strategy/init-north-star.md` 后，优先级最高的 CLI-first 缺口是写入完成后的终端交付摘要。

当前 `init` 已经在 CLI 中展示扫描进度、扫描发现、成熟度初评、用户补充影响和写入前 preview。上一轮也让正式 Markdown 资产吸收了扫描事实与用户补充。但 `render_init_completion_message()` 仍偏早期实现：

- 开头是英文 `Harness assets are available in ...`。
- 只展示当前成熟度、阻断项、建议下一步、Benchmark 健康度和 3 个推荐入口。
- 没有明确告诉用户“本次生成了哪些类型的资产”。
- 没有把推荐入口扩展成 3-5 个“先看什么、为什么看”的可执行清单。
- 没有在 CLI 中提示仍需人工确认的问题来源，例如 `.ai/human-input-needed.md`。
- 仍容易让用户以为交互要靠打开 Markdown 才能完成。

这与用户最新约束一致：`init` 的交互和主要展示必须 CLI-first，Markdown 是持久化资产和后续 Runtime / 审计上下文，不是交互入口。

## 用户故事

作为 Harness Maintainer，当我完成首次 `harness-builder-agent init` 写入后，我可以直接在 CLI 中看到本次生成结果、当前 L0-L4 成熟度、主要证据/缺口、Benchmark 状态、最值得先看的 3-5 个入口、仍需人工确认的问题和下一步命令，从而不用先打开 Markdown 文件也能理解这次初始化交付和下一步动作。

## Gap Analysis 摘要

| 维度 | 目标态 | 当前能力 | 缺口 | 排序理由 |
|---|---|---|---|---|
| CLI 体验 | 写入后 CLI 给出短交付摘要 | 只有较短完成消息 | 缺生成结果、入口原因、人工确认摘要 | 用户最新明确 CLI 优先，且 North Star 第一阶段候选就是写入后 summary 对齐 |
| 成熟度叙事 | CLI 先讲 L0-L4、证据、差距 | 有等级、阻断、下一步 | 缺“证据/缺口”命名和交付语境 | 小改动即可让输出更像产品交付 |
| 用户输入消费 | 用户补充进入后续资产和 CLI 摘要 | 资产已吸收，CLI completion 不展示 | 完成后用户看不到待确认项和补充影响去向 | 保护渐进式协作闭环 |
| 资产质量 | Markdown 作为持久化摘要 | `init-summary.md` 已增强 | 终端仍像文件索引 | 避免把 Markdown 作为交互入口 |
| 测试 | integration 覆盖部分 completion 文案 | 断言当前成熟度和 benchmark readiness | 缺 North Star 所列交付摘要要素 | 可通过单元和 integration 稳定验证 |

## 目标

本切片只增强 `init` 完成后的 CLI completion message，不改变扫描、LLM、成熟度评分、生成资产 schema 或已有 Harness 维护入口动作。

必须做到：

- completion message 全中文，使用稳定阶段标题 `== 初始化完成 ==`。
- 明确展示 `.ai` 输出目录和本次生成的资产类型：项目清单、命令目录、Guides、Sensors、Workflow Skills、成熟度报告、待确认项和 trace。
- 保留并强化当前成熟度 L0-L4、下一目标、主要阻断项、建议下一步。
- 展示 Benchmark 健康度和建议命令，继续说明资产生成不等于 benchmark passed。
- 展示 3-5 个优先入口，每个入口带“为什么先看”。
- 展示仍需人工确认的问题摘要：优先从 `questionnaire.yaml` 读取前 3 个问题；如果不可读，显式说明查看 `.ai/human-input-needed.md`，不静默成功。
- 明确说明 CLI 是本次交付摘要，Markdown 是持久化审查材料，不是 init 过程中的交互入口。

## 非目标

- 不新增交互问题，不把 completion 做成新的选择菜单。
- 不默认运行 benchmark。
- 不修改 `.ai/init-summary.md` 的章节契约。
- 不调整已有 Harness maintenance entry。
- 不新增机器消费文件。
- 已有 Harness 的 `exit`、`assess`、`improve`、`benchmark` 等维护动作不展示“初始化完成 / 本次已生成”的首次交付摘要；这些路径使用各自动作摘要，避免把只读退出或维护操作伪装成首次生成。

## 设计

`render_init_completion_message(ai: Path)` 继续作为唯一渲染入口，读取已有 schema 文件：

- `maturity-score.yaml` 通过 `MaturityReport` schema 校验。
- `questionnaire.yaml` 通过 `Questionnaire` schema 校验后取前 3 个待确认问题。
- 生成资产清单只检查核心路径存在与否，缺失时显示 `missing`，不伪装成功；这些缺失通常也会被测试或 benchmark 抓住。
- Benchmark 状态继续复用 `_benchmark_readiness(ai)`。

输出结构：

```text
== 初始化完成 ==
- 输出目录：...
- 本次已生成：...

当前成熟度
- 当前等级：Lx
- 下一目标：Ly
- 主要证据 / 缺口：...

建议下一步
1. ...

Benchmark 健康度
...

优先查看
1. `.ai/init-summary.md`：...
...

仍需人工确认
1. ...

说明
- 本终端摘要是本次 init 的主要交付说明；Markdown 文件用于持久化审查、团队协作和后续 Runtime 上下文。
```

## 取舍

- Superpowers brainstorming 要求人审 spec，但本线程目标明确授权“不要把用户确认作为常规节点”。因此本 spec 自主记录 assumption / decision / risk 并直接进入 plan / TDD。
- 本轮先解决写入后的 CLI 交付摘要，不继续扩 Markdown 内容，符合用户刚明确的优先级。
- `questionnaire.yaml` 已存在 schema，本轮只读消费，不新增 pending confirmation schema。

## 验收标准

- 单元测试证明 `render_init_completion_message()` 输出 `== 初始化完成 ==`、生成结果、当前成熟度、Benchmark 健康度、优先查看、仍需人工确认、CLI-first 说明。
- 集成测试证明 `init --non-interactive` 输出包含上述 CLI 交付摘要要素，并保留现有 benchmark readiness。
- guided init happy path 输出同样包含 CLI 交付摘要要素。
- existing Harness `exit` / `assess` 输出不包含 `== 初始化完成 ==` 和 `本次已生成`。
- 既有 `init-summary.md`、schema、核心资产生成测试保持通过。
- 文档同步：`docs/engineering/init-workflow.md` 和 `docs/evolution-log.md` 记录 CLI-first completion summary 边界。
