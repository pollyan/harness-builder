# Init North Star：深度引导式 Harness 生成体验

本文定义 `harness-builder-agent init` 的目标态、用户体验原则、质量指标和后续迭代边界。它用于约束后续目标模式：短期内所有主要开发循环都应优先服务 `init` 主线，避免在候选治理、Runtime、benchmark、prompt 等周边能力之间继续发散。

## 核心定位

`init` 不是模板初始化命令，而是 Harness Builder 面向用户的第一性体验。

用户拿一个陌生或遗留代码库运行 `init` 后，Harness Builder 应该像一个资深工程顾问一样：

1. 深入理解仓库结构、技术栈、模块边界、验证能力和风险区域。
2. 清楚解释它看到了什么、为什么这样判断、哪些地方不确定。
3. 让用户以低成本确认、修正或补充关键上下文。
4. 生成针对当前仓库的 Guides、Sensors、Workflow Skills、配置和成熟度入口。
5. 给出可审计的证据链、下一步建议和质量门禁解释。
6. 让用户感觉这是“为这个仓库定制的 Harness”，而不是固定模板拼装。

## 目标用户场景

### 首次初始化

作为 Harness Maintainer，我希望对一个已有代码库运行 `init` 后，系统能理解仓库、解释判断、引导我补充关键上下文，并生成一套可审查、可编辑、可持续演进的 `.ai/` Harness。

成功体验应该是：

- 我知道系统为什么判断这是某个技术栈。
- 我知道系统发现了哪些模块、验证命令、风险和缺口。
- 我知道哪些内容是事实、哪些是推断、哪些需要人工确认。
- 我能快速看到生成了哪些资产、它们之间如何关联。
- 我知道下一步应该先看哪些文件、先跑什么命令、如何判断质量。

### 再次进入已有 Harness

作为 Harness Maintainer，我希望再次运行 `init` 时，系统不是重新覆盖资产，而是先展示已有 Harness 的健康状态、维护建议和下一步动作。

成功体验应该是：

- 我能看到成熟度、benchmark、Experience、review-only 候选、Runtime 过程数据等关键信号。
- 我能理解最应该先处理的问题是什么。
- 我可以选择 assess、improve、benchmark、recommend-workflow、review-candidate、self-improve 或 reinit。
- 系统不会在我没有明确选择前覆盖正式 Guides、Sensors、Workflow Skills 或配置。

## 体验原则

### 深度优先

`init` 必须优先提升仓库理解深度，而不是只追求产物数量。

后续迭代应优先强化：

- evidence collection：构建配置、CI、源码入口、测试入口、文档、配置、关键模块。
- LLM-guided evidence expansion：LLM 可以提出还需要看的文件，Python 负责 allowlist、读取和校验。
- stack / module / command / risk 的证据链与置信度。
- 企业不规范仓库中的非标准目录、缺失测试、混合技术栈和隐性风险。

### 可解释

用户不能只看到结论，必须看到判断依据。

`init` 输出和 `init-summary.md` 应稳定表达：

- 发现了什么。
- 证据来自哪里。
- 为什么做出这个判断。
- 哪些地方置信度低。
- 哪些事项需要人工确认。
- 这些判断如何影响生成的 Guides、Sensors 和 Workflow Skills。

### 交互低负担

guided `init` 应降低用户输入成本。

目标态不是要求用户记住 `module=路径|类型|名称` 这类格式，而是逐步走向：

- 先展示系统判断，再询问是否修正。
- 支持自然语言补充团队规则、架构约束、测试策略和业务风险。
- 对结构化修正提供清晰示例和容错提示。
- 每一步都说明为什么需要这类信息。
- 用户可以跳过非关键问题，但跳过后的不确定性必须记录到产物。

### 视觉焦点清晰

CLI 是当前主要 UI，因此终端体验必须被当作产品界面设计。

目标态：

- 使用清晰的阶段标题，让用户知道当前处于扫描、证据扩展、LLM 分析、调和、资产生成、总结中的哪一步。
- 使用颜色或强调区分成功、警告、失败、需要人工确认和下一步动作。
- 使用一致的缩进、列表、分组和摘要格式，避免大段无层次文本。
- 长时间任务必须有进度反馈或阶段状态，不能让终端长时间无输出。
- 颜色必须可关闭或在无颜色环境下仍可读，不能只靠颜色表达关键信息。
- 错误信息应包含原因、影响和下一步处理建议。

### 可审计

`init` 的每个关键判断都应能回溯。

必须保留：

- LLM 原始结构化 proposal。
- reconciled inventory。
- command catalog。
- interaction decisions。
- generation trace。
- artifacts list。
- human-input-needed。
- maturity evidence。

LLM 输出不能直接成为不可审计事实；需要 schema、evidence source、allowlist、reconciler 和 benchmark 共同约束。

## Init 质量指标

后续 `init` 相关 milestone 应尽量把“体验变好”转成可验证标准。

### 仓库理解指标

一次成功的首次 `init` 至少应该：

- 识别 primary stack，并给出 evidence path 与置信度。
- 识别主要模块或明确说明模块边界不清。
- 识别构建、测试、lint、运行或 CI 相关命令候选。
- 区分 hard gate、soft gate 和低置信度命令。
- 识别至少一类风险区域或说明风险证据不足。
- 记录缺失测试、缺失 CI、命令不可验证等不确定性。

### 资产质量指标

生成的 `.ai/` 资产应该：

- Guides 包含真实仓库路径、模块名、技术栈和验证命令。
- Sensors 包含当前可运行的验证命令、缺失验证能力和失败处理策略。
- Workflow Skills 引用真实存在的 Guides / Sensors。
- `harness-config.yaml` 的 routing policy 能解释何时选择 bugfix、lightweight 或 standard。
- `init-summary.md` 像交付报告，而不是文件清单。
- `human-input-needed.md` 明确列出后续需要人工确认的问题。

### 体验质量指标

guided `init` 应该：

- 在长时间 LLM / scan 阶段持续输出阶段状态。
- 在每个阶段结束时给出简短摘要。
- 对用户输入给出清晰提示、默认选项和错误恢复。
- 在写入前展示将生成或更新的资产摘要。
- 对已有 Harness 默认进入维护入口，而不是覆盖。

### Benchmark 指标

benchmark 不应只检查文件存在。

与 `init` 相关的 benchmark 应逐步覆盖：

- schema 有效性。
- 关键章节存在。
- 关键字段与跨文件引用一致。
- Guide / Sensor 是否包含仓库特定内容。
- hard gate command 是否有 evidence 和足够置信度。
- trace 是否记录阶段、事件和产物。

## 后续迭代切片规则

短期目标模式应优先围绕 `init` 主线选题。

每轮 milestone 必须回答：

1. 这轮改善了 `init` 用户旅程中的哪一步？
2. 用户能看到什么新的价值？
3. 它是否是一个可独立验收的体验切片？
4. 它是否提升了仓库理解深度、交互体验、资产质量、结果解释或验证可信度？

不应优先选择：

- 与 `init` 体验无直接关系的周边功能。
- 只为了内部结构漂亮、但用户看不到价值的重构。
- 只新增 schema 或测试、但没有改善 `init` 体验的技术切片。
- 大而散的多模块改造。

可以选择的优先方向：

- `init` CLI 阶段化输出、颜色和进度反馈。
- `init-summary.md` 结果解释增强。
- scan evidence 深度与 LLM-guided evidence expansion。
- guided init 的自然语言上下文补充。
- 资产生成内容的仓库特异性。
- init quality benchmark。
- 中等真实仓库的人工体验验收样本。

## 推荐演进路线

### 第一阶段：让用户看得懂

目标：用户运行 `init` 后清楚知道系统正在做什么、做完后得到了什么、下一步该做什么。

候选 milestone：

- CLI 阶段标题、状态、颜色和进度反馈。
- `init-summary.md` 改成面向维护者的交付报告。
- benchmark 结果解释和下一步建议。

### 第二阶段：让判断更可信

目标：用户能看到证据链、置信度和不确定性。

候选 milestone：

- stack / module / command / risk evidence 展示。
- LLM-guided evidence expansion 更深入。
- `human-input-needed.md` 与 guided questions 对齐。

### 第三阶段：让资产更定制

目标：生成资产明显反映目标仓库，而不是通用模板。

候选 milestone：

- Guides 注入真实模块、路径、命令和风险。
- Sensors 对应真实验证能力与缺口。
- Workflow routing policy 根据仓库风险和 sensor 覆盖解释升级规则。

### 第四阶段：让体验可持续

目标：已有 Harness 能持续维护，而不是每次重建。

候选 milestone：

- existing Harness maintenance triage 体验优化。
- candidate / recommendation / self-improve 与 init 入口更清晰联动。
- Runtime 过程数据只读证据进入 init 维护摘要。

## 与现有文档关系

- 全景规划仍以 `docs/strategy/Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md` 为产品 North Star。
- 本文是 `init` 体验的局部 North Star，用于约束短中期开发循环。
- `docs/engineering/init-workflow.md` 继续定义当前工程契约、文件产物、失败行为和测试要求。
- 当本文目标态与当前工程文档不一致时，先通过 spec 记录 gap，再按小步 milestone 修改工程文档和实现。
