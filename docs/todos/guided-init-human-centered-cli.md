# 面向用户的 guided init 交互体验增强

## 状态

- 状态：implemented
- 优先级：high
- 发现日期：2026-05-31
- 相关命令：`harness-builder-agent init`
- 相关工程规则：`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`

## 背景

当前 `init` 已经有第一版 guided interactive mode：TTY 环境默认进入向导，非 TTY 必须显式传 `--non-interactive`，并且会记录 `interaction-decisions.yaml`、human input、candidate 决策和 generation trace。

但当前交互仍偏工程参数确认，而不是面向普通项目维护者的产品化引导。CLI 会展示类似 `primary_stack`、`stacks`、`commands`、`context`、`Guide/Sensor` 这类内部概念，用户需要理解 Harness Builder 的术语，才知道自己正在确认什么。

理想的 guided `init` 应该用中文、解释性语言和开放式补充来推进。用户不应只是在 yes/no 问题里被动确认，而应该能理解扫描结论、补充团队规则、审查 Guide/Sensor/Workflow 建议、修改前面输入，并在最终写入前看到完整摘要。

## 当前现状

当前已有能力：

- `init` 默认 guided mode，`--non-interactive` 用于自动化。
- CLI 会展示仓库路径、扫描结论、候选 Guide/Sensor 数量和最终写入确认。
- 用户可以输入 inline 团队上下文摘要。
- 用户可以选择候选增强全部接受或保持 candidate。
- 交互结果会结构化落盘，并进入 trace artifact。

当前限制：

- 扫描摘要仍以内部字段为主，例如 `primary_stack`、`stacks`、`commands`。
- “接受扫描结论?” 是封闭式 yes/no；用户选否后流程直接 abort，不能修正技术栈、模块、命令或风险区域。
- 团队上下文提问仍偏 `context` 概念，没有用用户熟悉的“团队代码规范、架构规范、测试策略、安全合规要求”等语言来引导。
- Guide/Sensor 候选只展示数量，没有解释每条规则控制什么、每个 Sensor 验证什么、哪些来自现有命令、哪些是建议新增能力。
- 当前缺少 Workflow 展示：用户看不到系统建议未来采用哪些工作流、每个工作流包含哪些步骤、适合什么复杂度或风险等级。
- 最终写入前缺少完整 summary，用户不能一次性看到已确认的技术栈、模块、团队规则、Guide、Sensor、Workflow 和待人工处理项。
- 缺少回退修改能力：用户在后续阶段发现前面输入不准确时，不能返回修改。
- CLI 输出的层次、分组、选项和说明还没有作为终端界面体验系统设计。

## 核心问题

Harness Builder 生成的 `.ai` 资产会影响后续 AI Coding 行为。用户需要确认的不是字段值，而是工程判断：

- 这个仓库主要是什么技术栈。
- 模块和边界是否符合真实架构。
- 哪些团队规范应该进入 Guide。
- 哪些验证能力可以作为 Sensor。
- 哪些命令可以作为 hard gate。
- 哪些新增 Sensor 或质量门禁需要团队接受。
- 未来 AI coding runtime 应该按什么 Workflow 执行任务。

如果 CLI 只展示内部参数和数量，用户即使选择了确认，也不一定真正理解确认内容。这个问题会降低生成 Harness 的可信度。

## 理想交互形态

未来 guided `init` 应以中文解释式对话推进，避免让用户理解内部字段名。

扫描结论展示应类似：

```text
我扫描了这个仓库，初步判断它主要是一个 Java 后端项目，并且使用了 Spring / Spring Boot 相关框架。

我看到的主要依据包括：
- `pom.xml` 中存在 Maven 项目配置。
- `src/main/java/...` 下存在 Spring Controller 或启动类。
- 当前发现了 `mvn test` 这样的测试命令候选。

我识别到的模块：
- 后端应用模块：`.`，包含主要 Java 源码和 Maven 配置。

这些判断是否符合你的理解？如果有补充或修正，可以直接输入；如果没有补充，直接回车继续。
```

团队规则收集应类似：

```text
除了仓库本身能扫描出来的信息，你们团队是否还有需要 AI 遵守的规则？

例如：
- 团队代码规范。
- 组织级架构约束。
- 测试策略或必须执行的质量门禁。
- 安全、合规、发布流程要求。
- 哪些目录或模块禁止随意修改。

可以输入一段说明，或提供规则文件路径；如果暂时没有，直接回车继续。
```

Guide/Sensor 展示应逐项解释：

```text
我建议生成以下 Guide：
- Controller 分层规则：控制接口层不要直接写业务逻辑，业务逻辑应进入 Service。
- 配置变更规则：修改配置文件时需要说明影响环境和回滚方式。

我建议生成以下 Sensor：
- `mvn test`：用于执行后端单元测试，建议作为 hard gate。
- lint/typecheck：当前没有发现稳定命令，建议先作为待补齐能力。

哪些规则你认可？哪些需要修改或保持候选？
```

Workflow 展示应解释未来使用方式：

```text
基于当前仓库复杂度，我建议生成两个工作流：
- lightweight：适合低风险文案、配置或小功能调整。
- bugfix：适合缺陷修复，要求先定位原因，再执行相关 Sensor。

未来 AI coding runtime 可以根据任务风险选择对应 Workflow。
```

最终确认应展示 summary：

```text
即将写入 Harness 资产：
- 技术栈：Java / Spring Boot。
- 模块：后端应用模块 `.`
- 团队规则：已记录 2 条。
- Guides：3 条确认，2 条保持候选。
- Sensors：1 个 hard gate，2 个待补齐。
- Workflows：lightweight、bugfix。
- 待人工后续处理：确认 lint/typecheck 是否需要新增。

输入 `confirm` 写入，输入 `back` 返回修改，输入 `cancel` 取消。
```

## 交互能力要求

未来实现该 todo 时，至少应支持：

- 中文为主的解释性输出，不直接暴露内部字段名作为主要 UI 文案。
- 对扫描结论提供证据说明，让用户知道判断从哪里来。
- 开放式补充输入：用户可以直接输入修正意见，而不是只能 yes/no。
- 用户可以修改关键扫描结论，包括技术栈、模块、验证命令和风险区域。
- 团队规则收集使用用户熟悉的业务语言，不以 `context` 作为主要概念。
- Guide 候选逐项展示标题、目的、适用范围、来源证据和确认状态。
- Sensor 候选逐项展示验证对象、命令来源、hard/soft gate 建议、是否现有能力或建议新增能力。
- Workflow 候选展示适用任务类型、步骤和未来使用方式。
- 最终写入前展示完整 summary。
- 支持返回前面阶段修改，至少支持从 summary 返回关键阶段。
- 交互决策结构化落盘，且能被 asset writer 真正消费。
- 非交互模式仍保持自动化兼容，不阻塞 CI、脚本和 acceptance。

## 终端界面体验要求

CLI 输出应当被当作一个用户界面来设计，而不是简单打印日志。

应考虑：

- 用清晰的分段标题组织信息，例如“扫描发现”“需要你确认的地方”“建议生成的规则”“最终摘要”。
- 使用中文解释和少量必要的英文路径、命令、文件名。
- 对命令、路径和 gate 类型保持可复制的原文。
- 对长列表做分组和编号。
- 对风险、待确认、已确认、建议新增能力做明确标记。
- 避免一次性输出过长内容；必要时分阶段展示。
- 所有选项都应说明后果，例如“保持候选表示不会升级为正式规则”。

## 初步验收标准

实现该 todo 时，至少应满足：

- CLI guided init 的扫描摘要不再以 `primary_stack` 等内部字段为主文案。
- 用户能在扫描摘要阶段输入补充或修正，并影响最终 `project-inventory.json` 或相关 override 产物。
- 用户能逐项查看 Guide/Sensor 候选，而不是只看到候选数量。
- 用户能确认、拒绝、修改或保持候选 Guide/Sensor。
- 用户能看到 Workflow 建议和步骤说明。
- 最终确认前会展示 summary，并支持返回修改。
- `interaction-decisions.yaml` 或新增 schema 能记录用户的修正、候选决策和最终确认。
- 生成的 Guide/Sensor/Workflow 资产能体现用户修正，而不是只记录在 human-input 文件里。
- 测试覆盖 guided happy path、用户修正扫描结论、候选逐项决策、summary 返回修改、非交互兼容。
- README 或工程文档说明 guided init 的用户体验边界。

## 待澄清点

- 第一版回退修改是否只支持从最终 summary 返回关键阶段，还是每个阶段都提供 `back`。
- 用户对扫描结论的自由文本修正，是先结构化解析为 override，还是先记录为人工确认并局部影响产物。
- CLI 是否引入更强的终端 UI 库，还是先基于 Typer prompt / rich-style 输出做第一版。
- Guide/Sensor 候选逐项编辑是否允许直接改 Markdown 文案，还是先只修改标题、状态、原因和 gate 类型。

## 非目标

第一版不要求：

- 图形界面。
- Web 管理后台。
- 多人审批流。
- 完整自然语言对话代理。
- 在 CI 或非 TTY 环境中交互。
- 一次性支持所有可能的终端 UI 组件。

重点是让 `init` 的本地向导从“工程字段确认”升级为“用户能理解、能补充、能修改、能最终确认”的 Harness 生成体验。

## 实现结果

- guided `init` 使用“扫描发现”“团队规则”“建议生成的规则”“建议生成的传感器”“推荐工作流”“最终确认”等中文分段展示。
- 扫描摘要以“主要技术栈”、判断依据、模块和验证命令说明为主，不再用 `primary_stack` 等内部字段作为主要交互文案。
- 用户可以在扫描摘要后直接输入补充说明，或用 `stack=java-spring` / `stack=dotnet-aspnet` / `stack=node` / `stack=unknown` 修正主要技术栈。
- 用户可以用结构化片段补充模块、验证命令和风险区域，例如 `module=frontend|frontend|frontend`、`command=frontend_test|npm test|test|hard|frontend/package.json|high`、`risk=frontend/package.json|前端依赖需要确认`。
- 用户补充的扫描说明、团队规则和 workflow 备注会进入 `interaction-decisions.yaml`、human input 和 generated guides 的人工补充章节。
- Guide/Sensor 候选逐项展示，支持接受、拒绝、保持候选和补充备注。
- Workflow 建议会展示 lightweight / bugfix 的适用场景和步骤，并记录到 `workflow_confirmation`。
- 最终写入前展示 summary，支持 `confirm`、`back`、`cancel`；`back` 第一版支持返回扫描修正、团队规则或候选项阶段。
- 非交互模式保持兼容，仍然不阻塞 CI、脚本和 acceptance。
