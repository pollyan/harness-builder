# Context 输入与人机交互体验增强

## 状态

- 状态：open
- 优先级：medium
- 发现日期：2026-05-30
- 相关命令：`harness-builder-agent init`
- 相关工程规则：`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`

## 背景

当前 `init` 支持通过 `--context` 传入团队规则、组织规范、架构约束等文件。

这一步当前是非交互式的：

```bash
harness-builder-agent init --repo ./target-repo --context ./team-rules.md
```

命令会读取 context 文件，生成：

- `.ai/context-inputs.yaml`
- `.ai/questionnaire.yaml`
- `.ai/human-input-needed.md`

它不会在终端前台逐个提问，也不会等待用户输入。这种设计兼容 CI，但本地使用体验不够好。

## 当前现状

当前能力：

- 支持传入一个或多个 `--context` 文件。
- 读取文件摘要并记录路径、大小、截断状态。
- 生成固定问题清单，例如团队上下文、guide candidates、sensor gates。
- 在 `human-input-needed.md` 中提示后续人工确认。
- 在 CI 中不会阻塞。

当前测试覆盖：

- `read_context_inputs` 能读取并截断 context 文件。
- `build_questionnaire` 能生成基础确认问题。
- `init --context` 能把 context 内容写入 human input 文件。

## 问题

当前体验存在几个问题：

- 用户必须提前知道要传 `--context`，否则组织级规则不会进入生成过程。
- CLI 不会主动提示用户是否有团队规范、架构规范、测试规范。
- `--context` 内容目前主要进入人工确认材料，还没有充分影响 LLM 扫描和 guide/sensor 生成。
- 生成后需要用户自己记得去看 `human-input-needed.md`。
- 没有后续命令把确认结果应用回 harness。
- 本地交互和 CI 自动化还没有明确模式区分。

## 理想状态

未来应区分非交互模式和交互模式：

```bash
harness-builder-agent init
```

默认非交互模式：

- 不阻塞 CI。
- 如果未传 context，生成明确提示和待确认项。
- 输出中提示用户下一步查看哪些文件。

```bash
harness-builder-agent init --interactive
```

本地交互模式：

- 询问是否有团队规则、架构规范、测试规范。
- 允许用户输入文件路径或跳过。
- 允许用户确认/调整候选 guide 和 sensor。
- 把人工输入结构化保存，保证后续可审计。

未来还可以增加：

```bash
harness-builder-agent confirm
harness-builder-agent apply-review
```

用于把人工确认结果应用到 harness 中。

## 初步验收标准

未来实现该 todo 时，至少应满足：

- 默认 `init` 仍然非交互，不会卡住 CI。
- 本地交互必须显式通过 `--interactive` 开启。
- 未传 context 时，CLI 输出应明确提示可以通过 `--context` 或 `--interactive` 补充组织规则。
- context 内容应能影响后续 guide/sensor 生成，而不只是被记录。
- 人工确认结果应结构化落盘。
- 测试覆盖非交互、传 context、interactive mock 输入、CI 不阻塞等场景。

## 非目标

第一版不要求：

- 完整图形化向导。
- 复杂权限系统。
- 多人协作审批流。
- 在 CI 中进行交互输入。

重点是让本地用户不必完全靠记忆传 context，同时保持 CI 友好。

