# Default Guided Interaction Design

## 背景

`interactive-guided-cli.md` 的核心不是给 `init` 增加一个可选交互参数，而是把 Harness Builder 的默认产品形态从“命令式工具”调整为“人机协作式 Agent”。

Harness Builder 生成的是会影响后续 AI Coding 行为的工程约束、质量门禁和工作流资产。默认完全自动生成会带来信任问题：用户看不到扫描结论如何形成，也没有机会补充组织规范、修正技术栈判断、确认 guide/sensor candidate 或拒绝基础设施改动建议。

因此新的默认交互原则是：

- `harness-builder-agent init` 默认进入引导式交互。
- 自动化、CI、脚本场景必须显式传入非交互参数。
- 非 TTY 环境不应静默选择交互，也不应假装用户确认过；需要明确失败并提示使用非交互模式。

## 目标

第一版目标聚焦 `init`，让它成为默认人机引导式工作流：

1. 默认 TTY 运行 `init` 时，启动分阶段向导。
2. 用户可以在向导中确认或修正扫描结论。
3. 用户可以输入或选择团队 context，并让 context 进入后续生成输入。
4. guide/sensor candidate 能被用户接受、拒绝或保持候选。
5. 所有人机决策结构化落盘，进入 trace/decision log。
6. 需要自动化时，用户显式使用 `--non-interactive`。

## 非目标

第一版不做：

- 图形界面。
- 多人审批流。
- 完整权限体系。
- 在 CI 中进行交互式输入。
- 一次性重做 `run`、`assess`、`improve`、`benchmark` 的全部交互体验。
- 让 LLM 动态生成 workflow skill。

`confirm` / `apply-review` 可以在数据结构和命令命名上预留，但不要求第一版完整实现。

## CLI 行为

### 默认模式

```bash
harness-builder-agent init
```

当 stdout/stdin 是 TTY 时：

- 使用当前目录作为目标仓库，除非用户传入 `--repo`。
- 进入引导式向导。
- 向导会展示阶段摘要并要求用户确认或修正。
- 所有回答写入 `.ai/interaction-decisions.yaml` 和当前 run 的 `decision-log.md`。

当不是 TTY 时：

- 默认失败。
- 错误信息说明：`init` 默认需要交互式终端；自动化场景请使用 `--non-interactive`。
- 不生成部分资产，避免用户误以为已经完成确认。

### 非交互模式

```bash
harness-builder-agent init --non-interactive
```

非交互模式用于测试、CI、脚本和自动验收：

- 不询问用户。
- 仍然执行扫描、生成资产和待确认材料。
- 对缺失人工信息写入 questionnaire、human-input-needed 和 decision log。
- 不把 candidate 自动晋升为 confirmed。

### 兼容参数

```bash
harness-builder-agent init --repo <path>
harness-builder-agent init --context <file>
harness-builder-agent init --non-interactive --context <file>
```

`--context` 在两种模式下都有效：

- 交互模式：展示 context 摘要，让用户确认是否适用。
- 非交互模式：读取 context，并记录为“已提供但未人工确认”。

## 向导阶段

第一版 `init` 向导包含以下阶段。

### 1. 仓库确认

输入：

- `--repo` 或当前工作目录。

展示：

- 仓库路径。
- 是否已存在 `.ai`。
- 是否将覆盖或更新 Harness 资产。

用户动作：

- 确认继续。
- 取消。

输出：

- `decision: repo.confirmed`
- `decision: repo.cancelled`

### 2. 扫描摘要确认

输入：

- evidence collector 输出。
- LLM scan proposal。
- scan reconciler 输出。

展示：

- primary stack。
- stacks。
- modules。
- command candidates。
- scan warnings。
- evidence coverage 摘要。

用户动作：

- 接受扫描结论。
- 修正 primary stack。
- 标记需要人工后续复核。

输出：

- `scan_confirmation.status`
- `scan_confirmation.primary_stack_override`
- `scan_confirmation.notes`

第一版可以只允许修正 primary stack 和备注，不要求完整编辑 modules/commands。

### 3. 团队 Context 收集

输入：

- `--context` 文件。
- 用户在向导中输入的补充文本。

展示：

- 已加载 context 的路径、摘要、是否截断。

用户动作：

- 确认 context 可作为生成依据。
- 添加短文本 context。
- 标记某个 context 不适用。
- 跳过。

输出：

- `.ai/context-inputs.yaml` 增加 `confirmation_status`。
- `.ai/interaction-decisions.yaml` 记录 context 决策。

Context 必须参与后续生成输入：

- guide 生成应能引用 context 摘要。
- sensor/gate 建议应能看到 context 中的测试、架构或合规要求。
- LLM scan prompt 应能接收 context 摘要，作为组织规则背景，但仍不得让 context 直接绕过 evidence。

### 4. Guide/Sensor Candidate 确认

输入：

- built-in weapon library selection。
- LLM enhancement candidates。
- scan warnings。
- command catalog。

展示：

- 候选 guide 列表。
- 候选 sensor 列表。
- 每个候选的 evidence、rationale、是否可能引入基础设施变更。

用户动作：

- accept：晋升为 confirmed。
- reject：拒绝。
- keep：保持 candidate。
- note：添加修改意见。

输出：

- `.ai/experience/weapon-library-candidates.yaml` 中的 candidate status 更新。
- `.ai/interaction-decisions.yaml` 记录每个 candidate 的决策。
- Markdown review 文件展示决策结果。

第一版可以先支持批量确认：

- 接受全部 guide candidates。
- 接受全部 sensor candidates。
- 全部保持 candidate。

逐项编辑留给后续版本。

### 5. 最终生成确认

展示：

- 即将写入的核心文件。
- 已确认的 context 数量。
- 保持 candidate 的项数量。
- 需要人工后续确认的问题数量。

用户动作：

- 确认写入。
- 取消。

输出：

- 完整 `.ai` 资产。
- generation trace。
- decision log。

## 数据契约

新增机器消费产物：

```text
.ai/interaction-decisions.yaml
```

建议结构：

```yaml
schema_version: "1.0"
mode: interactive | non_interactive
repo:
  path: /path/to/repo
  confirmed: true
scan_confirmation:
  status: accepted | amended | needs_review | not_confirmed
  primary_stack_override: null
  notes: []
context_confirmation:
  status: confirmed | partially_confirmed | not_provided | not_confirmed
  confirmed_paths: []
  rejected_paths: []
  inline_contexts: []
candidate_decisions:
  - candidate_id: llm-guide-risk-001
    decision: accepted | rejected | kept
    notes: ""
final_confirmation:
  status: confirmed | cancelled | not_confirmed
```

Schema 要放在 `src/harness_builder_agent/schemas/` 中，并由测试覆盖。

## 模块设计

新增或调整模块：

```text
src/harness_builder_agent/tools/interactive_init.py
  编排 init 的交互式向导，不直接写复杂资产。

src/harness_builder_agent/tools/interaction_decisions.py
  决策 schema 构建、默认值、合并和 Markdown 摘要。

src/harness_builder_agent/schemas/interaction_decision.py
  Pydantic schema。

src/harness_builder_agent/tools/human_confirmation.py
  扩展 context confirmation 信息。

src/harness_builder_agent/tools/write_assets.py
  接收 interaction decisions，把它传给 human confirmation/candidate writer。
```

`cli.py` 只负责：

- 判断是否 TTY。
- 解析 `--non-interactive`。
- 调用 interactive 或 non-interactive init 编排。

业务判断不应堆进 CLI。

## 错误处理

必须失败：

- 默认 `init` 在非 TTY 中运行且未传 `--non-interactive`。
- 用户在交互过程中取消最终确认。
- context 文件读取失败。
- LLM/DeepSeek/schema 失败。

可以成功但必须记录风险：

- 用户跳过 context。
- 用户保持 candidate 不晋升。
- 用户标记扫描结论需要复核。
- 用户没有确认 hard gate 长期可靠。

## 测试策略

Unit：

- `InteractionDecisions` schema 正反例。
- 非交互默认决策结构。
- context confirmation 合并逻辑。
- candidate decision 状态更新逻辑。

Integration：

- TTY 模拟下 `init` 默认进入向导并生成 `.ai/interaction-decisions.yaml`。
- 用户接受默认扫描结论、跳过 context、保持 candidate 时，产物正确。
- 用户传 `--context` 后，context 摘要进入 decisions 和 guide。
- 非 TTY 默认运行失败，并提示 `--non-interactive`。
- `--non-interactive` 在非 TTY 下继续生成现有完整资产。

E2E：

- Java fixture 默认交互 happy path。
- .NET fixture 非交互模式保持兼容。

Acceptance：

- 真实 DeepSeek / 真实开源仓库仍用 `--non-interactive`，避免真实验收阻塞在 TTY。
- Acceptance 仍要求生成 questionnaire、candidate、trace、benchmark report。

## 设计决策

### 为什么默认交互，而不是 `--interactive`

Harness Builder 的价值不是“快生成一堆文件”，而是帮助用户建立可信、可审计、可演进的 AI Coding Harness。默认交互能让用户在关键节点确认事实和规则，符合 Agent 产品形态。

### 为什么还保留 `--non-interactive`

测试、CI、脚本和 acceptance 必须可重复运行。显式 `--non-interactive` 表示用户接受“未人工确认”的风险，系统会把缺失确认写入产物，而不是假装已经完成。

### 为什么第一版不完整实现 `confirm`

`confirm` / `apply-review` 是后续自然演进，但第一版先把 init 的默认交互、决策落盘和非交互兼容做稳。否则会同时改太多命令面，增加测试和行为风险。

