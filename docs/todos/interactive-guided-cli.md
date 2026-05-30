# 全局交互式 CLI 与强引导式 Harness 生成

## 状态

- 状态：open
- 优先级：high
- 发现日期：2026-05-30
- 相关命令：`harness-builder-agent init`、未来的 `confirm` / `apply-review`
- 相关工程规则：`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`

## 背景

当前 Harness Builder 的 CLI 更接近“命令式工具”：用户需要知道有哪些命令、每个命令需要哪些参数、什么时候传 `--context`、生成后应该看哪些文件、哪些候选项需要确认。

这对 POC 可以接受，但不适合作为真正的 Harness Builder Agent。目标用户不应该靠记忆理解完整工作流。工具应该通过 CLI 对话和阶段性确认，引导用户补充信息、确认扫描结论、审查候选 guide/sensor，并把确认过程结构化记录下来。

这个问题不是 `--context` 单点交互问题，而是整个 Harness Builder 的产品交互形态问题。

## 当前现状

当前能力：

- `init --repo` 可以扫描仓库并生成 `.ai` 资产。
- `init --context` 可以读取用户手工传入的上下文文件。
- 系统会生成 `questionnaire.yaml` 和 `human-input-needed.md`，提示后续需要人工确认。
- LLM 产生的 guide/sensor enhancement 会以 candidate 形式落盘。
- `run`、`assess`、`improve`、`benchmark` 都是独立命令，主要依赖用户知道何时执行。

当前限制：

- CLI 不会主动询问用户是否有团队规则、架构规范、测试规范。
- 用户不传 `--context` 时，系统不会在前台引导补充。
- `--context` 当前主要被记录和展示，还没有成为 LLM scan、guide/sensor 生成、gate 判断的强输入。
- 用户即使传了 `--context`，内容也主要进入 `context-inputs.yaml`、`questionnaire.yaml`、`human-input-needed.md`，尚未真正影响后续 Harness 资产生成。
- 当前缺少对 context 文件的前台说明、加载确认、摘要展示和用户修正机会。
- 扫描结果没有阶段性前台确认，例如技术栈、模块、框架、测试命令、风险目录。
- guide/sensor candidate 没有前台确认、拒绝、修改、晋升机制。
- 对“建议引入单元测试框架”这类基础设施变更，没有强制 review 和确认。
- 生成后用户需要自己记得查看 `human-input-needed.md`、candidate 文件和 benchmark 结果。

## 核心问题

Harness Builder 生成的不是普通配置文件，而是会影响后续 AI Coding 行为的工程约束。

因此以下信息不能完全自动决定：

- 技术栈和模块边界。
- 团队架构约束。
- 编码规范。
- 测试和质量门禁。
- 是否引入新的测试框架或验证工具。
- 哪些 guide/sensor 可以成为正式规则。
- 哪些 LLM 建议只是候选项。

用户需要在关键阶段被引导确认，否则生成结果即使结构正确，也可能不被信任。

## 理想交互形态

未来 `init` 应演进为强引导式流程：

```text
启动 init
  -> 扫描仓库
  -> 展示扫描摘要
  -> 用户确认或修正技术栈/模块/命令
  -> 询问并收集团队上下文
  -> 生成 guide/sensor 候选
  -> 用户逐项接受/拒绝/修改
  -> 生成正式 Harness
  -> 记录确认过程、决策和产物
```

CLI 应同时支持两种模式：

```bash
harness-builder-agent init
```

默认非交互模式：

- 不阻塞 CI。
- 可以在没有 TTY 的环境中运行。
- 如果缺少人工信息，生成明确的待确认材料。
- 输出下一步提示，例如查看哪些文件、运行哪个确认命令。

```bash
harness-builder-agent init --interactive
```

本地交互模式：

- 通过对话方式询问组织规则、架构规范、测试规范。
- 展示扫描摘要并要求确认。
- 允许用户修正技术栈、模块、命令、风险区域。
- 对 guide/sensor candidate 逐项确认。
- 对可能引入基础设施改动的建议进行强确认。
- 把所有人工输入结构化落盘。

未来可以补充：

```bash
harness-builder-agent confirm
harness-builder-agent apply-review
```

用于在非交互 `init` 后继续处理人工确认和 candidate 晋升。

## 阶段性确认点

至少应考虑以下确认阶段：

1. 仓库基本信息确认
   - 仓库名称。
   - 主技术栈。
   - 前端/后端/脚本/配置模块。
   - 是否为 monorepo。

2. 扫描结果确认
   - 识别出的框架是否正确。
   - 架构信号是否可信。
   - 风险目录是否合理。
   - 测试命令、构建命令、lint/typecheck 命令是否真实可用。

3. 组织上下文收集
   - 是否有团队编码规范。
   - 是否有架构约束。
   - 是否有测试策略。
   - 是否有安全、合规、发布要求。
   - 是否需要加载本地文件作为 context。
   - 已加载的 context 摘要是否正确。
   - context 中哪些规则应进入正式 guide。
   - context 中哪些规则应转化为 sensor 或 gate。

4. Guide 确认
   - 哪些规则可以成为正式 guide。
   - 哪些规则只作为建议。
   - 哪些规则需要修改后再接受。

5. Sensor / Gate 确认
   - 哪些命令可以作为 hard gate。
   - 哪些只能 advisory。
   - 哪些需要先搭建基础设施。
   - 哪些失败应阻断任务。

6. 最终生成确认
   - 展示即将写入的文件。
   - 展示关键规则摘要。
   - 展示待人工后续处理项。

## Context 处理要求

`--context` 是本交互改造的一部分，不再单独维护局部 todo。

未来应满足：

- 用户可以通过 `--context` 传入规则文件，也可以在 `--interactive` 中被引导输入或选择文件。
- 已传入的 context 必须展示摘要，允许用户确认或指出不适用。
- context 必须参与 LLM scan、guide/sensor 生成和 gate 建议，而不只是被记录。
- context 中的组织规则必须区分：
  - 可直接进入 guide 的规则。
  - 可转化为 sensor/gate 的规则。
  - 需要人工确认的规则。
  - 当前无法自动处理的规则。
- context 处理结果必须结构化落盘，便于 trace 和后续 review。

## 初步验收标准

未来实现该 todo 时，至少应满足：

- `init` 默认非交互，CI 不会卡住。
- `init --interactive` 能启动前台引导流程。
- 扫描结果有阶段性摘要和确认机制。
- 用户可以修正关键扫描结论。
- `--context` 或交互输入能真正参与 LLM scan 和 guide/sensor 生成。
- guide/sensor candidate 支持接受、拒绝、修改和晋升。
- 对引入新测试框架、新质量门禁、新基础设施的建议需要明确确认。
- 人工输入和确认结果结构化落盘，并进入 trace 或 decision log。
- 测试覆盖非交互、交互 happy path、用户修正、candidate 晋升、CI 非 TTY 不阻塞。

## 非目标

第一版不要求：

- 图形界面。
- 多人审批流。
- 完整权限体系。
- 在 CI 中进行交互式输入。
- 一次性覆盖所有命令。

第一版可以优先聚焦 `init --interactive`，但设计上要为后续 `confirm` / `apply-review` 预留空间。
