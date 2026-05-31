# Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器

> 核心目标：帮助企业把隐性工程约束转化为可执行、可验证、可持续演进的 AI Coding Harness。  
> 文档版本：产品整体规划 v1.0  
> 文档性质：产品定位、目标态架构与能力规划说明。

---

## 1. 一句话定义

**Harness Builder 本身就是一个 AI Agent——一个运行在 AI IDE / Coding Agent 环境中的向导式 Self-Improve Harness Agent。它通过扫描遗留代码库、识别已有工程资产、从 Workflow Toolkit 中组装最适合的执行流程、补齐关键规则与验证机制，生成并持续演进项目级 AI Coding Harness。**

Harness Builder 的核心价值在于提升企业对 AI 代码变更的验证、审计、信任和持续改进能力。

Harness Builder 将已有代码库改造成：

```text
AI Agent 可以理解上下文
→ 遵守项目规则
→ 从 Workflow Toolkit 中选择并组装适合的工作流
→ 执行必要验证（含 Prototype Preview、Sensors、Repair Loop）
→ 失败后进入修复闭环
→ 任务后沉淀经验
→ 持续提升 Harness 成熟度
→ 让 Harness Builder 自身也不断 Self-Improve
```

最终形态是让 AI Coding 从“个人经验驱动”转向“工程体系驱动”，并形成可持续积累经验的 Self-Improve Harness Agent——Harness Builder 在帮助客户项目演进的同时，自身的工作流选择策略、扫描能力和推荐逻辑也在持续改进。

---

## 2. 背景问题

很多企业已经开始使用 AI IDE、Coding Agent 或代码生成工具。随着 AI 生成代码的速度快速提升，企业级 AI Coding 的瓶颈正在从“写代码”转向“验证、审计与信任”。

在复杂遗留代码库中，AI Coding 的效果往往不稳定。典型问题包括：

- 项目真实上下文缺少结构化供给。
- 团队长期形成的隐性约束缺少显性表达。
- 高风险模块缺少明确标记。
- 可修改目录、只读目录和建议型目录缺少清晰边界。
- 测试、lint、typecheck、CI 等验证能力缺少统一入口。
- 代码修改后的必要验证缺少稳定触发机制。
- 验证失败后的修复闭环缺少标准流程。
- AI Coding 基础设施成熟度缺少评估依据。
- 历史任务中的修复经验、Review 反馈和规则教训缺少沉淀机制。

在上述条件下，很多团队虽然开始使用 AI Coding，实际过程仍然高度依赖个人经验和临时 prompt：

- 输出风格不稳定。
- 架构规则容易被破坏。
- 业务规则容易被遗漏。
- 自动化测试没有被稳定触发。
- 高风险模块缺少保护。
- 失败结果没有进入修复闭环。
- AI 生成代码难以审计和追溯。
- Agent 缺少随项目使用时间增长而持续理解代码库的机制。

Harness Builder 提升企业验证、审计、信任和持续改进 AI 代码变更的能力。

---

## 3. 产品定位与能力边界

### 3.1 产品定位

Harness Builder 是面向遗留代码库的 AI Coding 治理与控制系统生成器。

它通过扫描代码库、识别工程资产、生成项目级 Harness，并在后续任务执行中持续沉淀经验，帮助企业建立可执行、可验证、可审计、可演进的 AI Coding 工程控制体系。

Harness Builder 持续观察任务执行、Sensor 结果、Repair Loop、人工 Review 和成熟度变化，并将这些信息转化为可审查的 Harness 改进候选，推动项目级 Harness 随代码库和团队实践一起演进。

它聚焦解决的问题是：

> 一个复杂、长期演进、规则隐性化的企业代码库，如何被改造成 AI Agent 可以安全协作、可验证、可追溯、可持续改进的工程环境。

### 3.2 核心产品主张

Harness Builder 是面向企业遗留代码库的治理工具：

1. **扫描现状**  
   识别代码库已有文档、测试、构建命令、CI 配置、风险区域和工程规则。

2. **生成控制系统**  
   把团队隐性经验转成 AI 可读取的 Guides，把已有检查转成可执行 Sensors。

3. **固化工作流**  
   生成项目级 AI Coding Workflow / Skills，让 AI 修改代码时必须经过计划、验证、修复和交付闭环。

4. **沉淀任务经验**  
   从真实任务中提取失败模式、修复路径、Sensor 有效性、团队偏好和 Review 反馈，形成可审查的经验资产。

5. **持续演进**  
   输出成熟度报告、缺口分析和下一步补齐建议，让企业逐步提升 AI Coding 的可控性。

### 3.3 目标用户与使用角色

Harness Builder 的直接用户定位为客户开发团队中负责维护团队 AI Coding Harness 的技术角色。

这个角色可以称为 **Harness Maintainer**。

Harness Maintainer 可能是：

- Tech Lead。
- 架构师。
- 资深开发。
- 工程效能负责人。
- AI Coding 推广负责人。
- 负责团队 AI Coding 规范、验证和治理的项目成员。

Harness Maintainer 的核心职责包括：

- 维护项目级 AI Coding 规则和 Guides。
- 配置和确认 Sensors、risk zones、restricted paths。
- 审查 Harness Builder 生成的候选规则、经验和改进建议。
- 决定哪些任务需要 Standard Workflow，哪些可以使用 Lightweight Workflow。
- 确认哪些经验可以进入正式 Harness，哪些需要废弃或降级。
- 确保团队成员使用 AI Coding 时遵循统一的验证、审计和风险控制体系。

普通一线开发者是 Harness 的间接受益者和使用者。他们日常使用 AI Coding 工具完成开发任务，并通过 Harness 获得更稳定的项目上下文、规则约束、验证机制和交付摘要，但不一定直接维护 Harness Builder。

FDE、方案团队和客户成功团队是落地赋能角色。他们可以帮助客户完成首次扫描、初始化配置、试点任务、结果解释和交接，但长期维护主体应回到客户开发团队内部的 Harness Maintainer。

决策与采购相关方包括研发负责人、CTO、工程效能负责人和安全 / 合规负责人。他们关注 Harness Builder 是否能提升 AI Coding 的可控性、验证能力、审计能力、团队一致性和企业级落地信心。

使用角色分层如下：

| 角色 | 与 Harness Builder 的关系 | 主要关注点 |
|---|---|---|
| Harness Maintainer | 直接用户和长期维护者 | 规则维护、Sensors 配置、风险区域、经验审核、成熟度演进 |
| 一线开发者 | 间接受益者和 Harness Consumer | AI 更懂项目、验证不漏跑、风险被提醒、交付更可审计 |
| FDE / 方案团队 / 客户成功 | 落地赋能角色 | 初始扫描、试点落地、客户培训、交接给 Harness Maintainer |
| 研发负责人 / CTO / 工程效能负责人 | 决策和采购相关方 | 团队级治理、质量提升、审计追溯、AI Coding 规模化采用 |
| AI Coding 工具公司 | 产品线价值受益方 | 企业适配能力、平台差异化、客户成功效率和长期护城河 |

### 3.4 面向 AI Coding 工具公司的产品线价值

对于正在建设 AI Coding IDE、插件或 Agent 产品的团队，Harness Builder 是一项独立且高度互补的产品线能力。

它对 AI Coding 工具公司的价值在于：

- 增强产品对企业遗留代码库的适配能力。
- 将客户隐性工程经验转化为可持续维护的项目级 Harness 资产。
- 帮助客户从个人 prompt 使用升级到团队级 AI Coding 治理。
- 降低 FDE、方案团队和客户成功团队在客户现场重复配置和手工总结的成本。
- 提高企业客户对 AI Coding 的验证、审计、风控和规模化采用信心。
- 形成项目级差异化能力和长期数据 / 经验闭环。
- 推动产品从“编码助手”升级为“企业 AI Coding 平台”。

第一阶段，Harness Builder 可以采用 **独立 Skill** 形态完成快速验证：

- 有效扫描遗留代码库。
- 生成项目级 Guides / Sensors / Workflow Runtime Specification。
- 帮助客户开发团队跑通 AI Coding 控制闭环。
- 让 Harness Maintainer 能够审查和接管项目级 Harness。
- 通过任务后复盘形成下一轮 Harness 改进建议。

完成独立验证后，Harness Builder 可以逐步整合进自有 AI Coding IDE、插件或 CLI 体系中，成为产品护城河的一部分。

### 3.5 与底层 AI Coding 工具的能力边界

Harness Builder 构建在已有 AI Coding 工具之上，聚焦项目级控制资产、风险策略和改进建议的生成。

底层 AI Coding 工具默认提供：

- 基础 rules / instructions 管理能力。
- 知识库或上下文检索能力。
- 工具调用与权限控制。
- 高危命令拦截能力，例如删除文件、破坏性 shell 命令等黑名单。
- 基础审计、会话记录或执行日志能力。
- 具体命令执行、沙箱、CI 或 IDE 运行能力。

Harness Builder 的职责是生成项目级 Harness，并把项目特有的工程约束映射到底层工具可以消费的规则、知识、工作流和权限策略中。

| 能力 | 底层 AI Coding 工具负责 | Harness Builder 负责 |
|---|---|---|
| Rules / Instructions 容器 | 提供规则存储、加载和注入机制 | 生成项目级 Guides，定义适用范围、来源、证据和加载策略 |
| 知识库 / 上下文 | 提供检索、索引和上下文注入能力 | 识别哪些工程知识需要沉淀，生成结构化知识内容与任务级加载策略 |
| 高危命令拦截 | 提供通用黑名单、权限控制和执行保护 | 标记项目级风险场景，声明哪些任务应触发底层保护或人工确认 |
| 工具权限 / 沙箱 | 提供具体执行隔离和权限机制 | 根据 Harness Mapping 选择风险等级、隔离需求和升级策略 |
| 审计日志 | 提供底层会话和工具调用记录 | 生成任务级 Decision Log、Sensor Report、Handoff Summary 与 Harness 改进建议 |
| 经验存储基础设施 | 提供文件、数据库、知识库或权限能力 | 生成项目级 Experience 资产、候选改进和加载策略 |

边界原则：

```text
Harness Builder 负责生成项目级控制资产、策略和改进建议；
AI Coding 工具负责提供通用运行能力与执行基础设施。
```

通用 rules 引擎、知识库系统、命令黑名单系统、底层沙箱系统、IDE 和 CI 属于底层 AI Coding 工具或企业工程平台能力。Harness Builder 以这些能力为运行前提，并在项目级维度上定义使用时机、使用方式和使用强度。

### 3.6 Harness Builder 与 Harness Runtime 的关系

Harness Builder 定位为项目级 Harness 资产生成与演进系统。

在目标态中，Harness Builder 负责生成项目级 Harness 资产，包括 Guides、Sensors 定义、Workflow 编排规范、Harness Mapping 规则、风险策略、经验候选和成熟度报告。

这些资产需要由底层 AI Coding 工具、IDE 插件、CLI Agent、CI 系统或项目级 Skill 来执行。

因此需要区分三层：

| 层级 | 责任 |
|---|---|
| Harness Builder | 扫描代码库，生成和更新项目级 Harness 资产与运行规范 |
| Harness Runtime / Execution Carrier | 读取 Harness 资产，按 Workflow 规范加载 Guides、运行 Sensors、触发 Repair Loop 和 Human Escalation |
| 底层 AI Coding Tool / IDE / CLI / CI | 提供模型调用、代码编辑、命令执行、权限控制、日志、沙箱、CI 集成等基础能力 |

Harness Builder 可以生成 Runtime 所需的配置、协议、Skill 模板和执行建议，也可以在某些产品形态中内置轻量执行器。其核心职责是把项目级工程约束转化为可被 Runtime 消费的控制资产，并复用底层 AI Coding Runtime 的通用执行能力。

边界钉子：

```text
Harness Builder 负责生成项目级 Harness 资产与运行规范，
使代码执行过程具备更强的可控性、可验证性、可审计性和持续改进能力。
```

### 3.7 关键价值假设与验证逻辑

Harness Builder 的价值基础包括代码库自动扫描、人工确认、企业规范导入、最佳实践推荐和成熟度路线图。其核心作用是帮助客户开发团队建立体系化 AI Coding 控制机制，并形成可持续演进的项目级 Harness。

尤其对很多企业端研发团队而言，当前基础往往较弱：

- 可能只有零散的代码规范或文档规范。
- 对“规范驱动开发”有初步认知，但缺少完整 Harness 视角。
- 不清楚如何把团队级、企业级规范转化为 AI 可执行的项目规则。
- 对 Sensors、自动化测试、lint、typecheck、架构约束、安全扫描、质量门禁等机制缺少系统认知。
- 缺少 AI Coding 成熟度评估框架，不知道当前处在哪个阶段，也不知道下一阶段应该补齐什么能力。

因此，Harness Builder 的价值假设应分成两个层次：

#### 从 0 到 1：帮助客户建立第一版 AI Coding Harness

从 0 到 1 阶段，Harness Builder 的核心价值是把最佳实践、代码库现状和人工输入结合起来，帮助客户低成本建立第一版项目级 Harness。

这一阶段的价值相对确定：

```text
客户原本缺少体系化 Harness
→ Harness Builder 扫描现状
→ 引导客户补充团队规范、架构规范、风险边界和验证要求
→ 生成第一版 Guides / Sensors / Workflow Runtime Specification / Maturity Report
→ 客户获得一套可维护、可演进的 AI Coding 控制基线
```

在这个过程中，Harness Builder 综合使用四类信息源：

| 信息源 | 示例 | 作用 |
|---|---|---|
| 代码库扫描 | 目录结构、依赖、测试命令、CI 配置、现有文档、历史约定 | 识别已有工程资产和可自动化控制点 |
| 客户人工输入 | 架构规范、代码规范、业务风险模块、restricted paths、测试环境限制 | 弥补代码库无法表达的组织知识和业务语义 |
| 企业 / 团队已有规范 | 安全规范、研发流程、代码 Review 标准、发布要求、合规要求 | 将组织级规则映射为项目级 Harness |
| Harness Builder 最佳实践 | 推荐的 Guides 分类、Sensor 类型、Workflow 模板、成熟度模型 | 帮助基础较弱的团队建立正确起点 |

从 0 到 1 阶段的关键目标，是通过扫描、提问、确认和最佳实践推荐，帮助客户快速形成一套清晰、可执行、可验证的 Harness 基线。

#### 从 1 到 N：验证 Harness 持续带来的效率和质量提升

从 1 到 N 阶段，关键问题变成：Harness Builder 生成并持续演进的 Harness，是否真的能提升团队 AI Coding 的效率、质量、审计能力和风险控制能力。

这一阶段需要持续验证：

| 价值假设 | 验证方式 |
|---|---|
| Guides 能减少 AI 对项目规则的误解 | 对比有无 Guides 时任务返工率、Review 问题数量、规则遗漏数量 |
| Sensors 能减少漏测和低质量提交 | 统计 Sensors 捕获的问题、Hard Gate 阻断次数、上线前缺陷变化 |
| Harness Mapping 能让任务选择更合适的流程 | 观察高风险任务是否被正确升级、低风险任务是否避免过重流程 |
| Repair Loop 能提升自动修复成功率 | 统计 Sensor 失败后的修复轮次、最终通过率、人工介入比例 |
| Experience 能形成经验复利 | 观察重复问题是否减少、pending improvements 被确认后的效果变化 |
| Maturity Report 能指导团队演进 | 跟踪客户从 L0/L1 向 L2/L3 晋升所需时间、补齐能力和实际收益 |

因此，Harness Builder 的关键验证逻辑应分阶段展开：

```text
0→1：是否能帮助基础较弱的团队快速建立第一版 Harness 基线？
1→N：这套 Harness 是否能在真实任务中持续提升 AI Coding 的可控性、效率和质量？
```

成熟度模型承担评分和路线图双重作用：

- 当前处于哪个 Harness 成熟度等级。
- 哪些 Guides、Sensors、Workflow、Experience 能力缺失。
- 如果要晋升到下一等级，需要补齐哪些工程资产和流程机制。
- 哪些改进可以低成本先做，哪些需要团队工程能力投入。
- 一段时间后是否真的从 L0 / L1 晋升到 L2 / L3。

这使 Harness Builder 成为客户 AI Coding 工程能力建设的低成本最佳实践入口，并具备持续演进价值。

---

### 3.8 行业参照与产品定位依据

Harness Builder 的产品定位建立在 AI Coding 行业正在形成的多个成熟方向之上，包括规范驱动开发、项目级规则、工具调用边界、质量门禁、经验沉淀和工程成熟度评估。

这些行业参照共同说明：AI Coding 的工程化需要在任务执行之前建立项目级上下文、规则边界、验证协议和经验资产。Harness Builder 将这些分散机制组织为一套面向既有代码库的项目级 Harness 生成体系。

#### AI Coding 的问题重心变化

AI Coding 正在从代码补全、代码生成和问答辅助，进入 Agent 执行工程任务的新阶段。

在简单任务中，Agent 主要依赖 prompt、局部文件上下文和人工即时反馈完成代码修改。在复杂企业项目中，Agent 面临的问题会显著扩大：

- 是否理解项目结构、技术栈和历史约定。
- 是否遵守团队代码规范、架构规则和安全要求。
- 是否知道哪些路径、模块、数据操作和发布动作属于高风险范围。
- 是否能选择正确的测试、构建、静态分析和安全检查。
- 是否能在验证失败后进入稳定的 Repair Loop。
- 是否能把重复出现的问题、修复经验和 Review 反馈沉淀下来。
- 是否能让团队长期观察 AI Coding 能力建设的成熟度变化。

因此，复杂项目中的 AI Coding 问题重心，已经从“让 Agent 生成代码”扩展到“为 Agent 构建可控、可验证、可审查、可演进的工程协作环境”。Harness Builder 对应的正是这一层工程治理需求。

#### 已被行业验证的关键机制

当前行业中已经出现多类与 Harness Builder 相关的成熟机制：

| 机制方向 | 代表性参照 | 已验证价值 |
|---|---|---|
| 规范驱动开发 | GitHub Spec Kit、Kiro Specs | 先形成需求、设计、任务和验收标准，再进入实现，减少临场 prompt 带来的目标漂移 |
| 项目级上下文与规则 | Claude Code Memory、Cursor Rules、Kiro Steering | 将产品背景、技术栈、代码规范、安全要求和团队偏好沉淀为 Agent 可读取的项目规则 |
| 工具调用与执行边界 | Claude Code Hooks、OpenHarness、OpenHands | 对 Agent 的命令执行、工具调用、权限边界和运行环境进行控制 |
| 质量门禁与验证 | SonarQube、CI Guard、测试与静态分析工具 | 将 lint、typecheck、test、build、security scan 等检查接入开发与交付流程 |
| 方法论与流程资产 | BMAD Method、Agent Workflow、Skills | 用角色、模板、流程和任务分解降低复杂协作中的上下文损耗 |
| Agent 执行与评估框架 | SWE-agent、mini-SWE-agent、OpenHands SDK | 支持 Agent 在沙箱或受控环境中执行任务，并保留轨迹、日志和评估结果 |

这些机制共同说明，AI Coding 的工程化方向已经比较清晰：Agent 需要结构化输入、项目级规则、受控执行、自动验证、反馈修复和长期经验资产。

#### 现有机制在既有代码库场景下的缺口

现有机制通常分散存在于不同工具和流程中，各自解决 AI Coding 生命周期中的一部分问题：

- 规范驱动开发框架主要解决单个需求从 Spec 到任务拆解的问题。
- 项目规则机制主要解决 Agent 如何读取团队规则的问题。
- Hooks 和执行框架主要解决工具调用、权限控制和运行安全的问题。
- 质量平台和 CI 工具主要解决代码结果如何被验证的问题。
- AI IDE 和 Coding Agent 主要解决任务执行体验和代码修改能力的问题。
- 方法论框架主要解决复杂协作中的角色、流程和模板问题。

这些能力在既有代码库和遗留系统场景下仍然缺少一个统一入口：如何从一个真实项目出发，识别其代码结构、工程资产、团队规则、风险边界、验证方式和历史经验，并生成一套可以被 Agent 持续加载和执行的项目级 Harness。

这个缺口尤其影响企业端落地。很多客户团队已经有部分测试、CI、代码规范、架构约束和安全流程，但这些资产分散在仓库、文档、流水线、人员经验和 Review 习惯中。AI Coding Agent 很难自动理解这些隐性规则，也很难稳定选择正确的验证链路。

Harness Builder 的机会点在于，将这些分散机制重新组织为一套面向既有代码库的 Harness 生成、确认、执行和演进体系。

#### Harness Builder 的产品定位

Harness Builder 定位为 AI Coding Agent 进入复杂项目之前的工程治理层。

它面向既有代码库和遗留系统，通过 Scanner & Analyzer 识别项目现状，通过 Guides 固化项目知识和团队规则，通过 Sensors 建立验证反馈，通过 Workflow Runtime Specification 定义任务执行协议，通过 Experience & Self-Improve 沉淀可审查经验，通过 Maturity & Evolution 形成持续改进路线图。

在产品生态中，Harness Builder 与现有工具形成协作关系：

- 为 AI IDE 和 Coding Agent 提供项目级上下文、规则、任务协议和验证要求。
- 为 Spec 框架补充既有代码库扫描、风险识别、验证映射和经验反哺能力。
- 为质量平台和 CI 工具提供任务级调用策略、失败反馈和成熟度观察入口。
- 为客户开发团队提供可维护、可审查、可版本化的 AI Coding 治理资产。

因此，Harness Builder 的差异化来自能力组织方式：它把行业中已经被验证的分散机制，组织成面向复杂既有代码库的项目级 AI Coding Harness 生成器。

#### 行业机制到产品模块的映射

Harness Builder 的六大模块对应行业中已经出现的关键工程机制，同时针对既有代码库场景进行重新组织：

| 行业机制 | Harness Builder 对应模块 | 产品化含义 |
|---|---|---|
| 规范驱动开发 | Workflow Runtime Specification、Implementation Plan、Review Handoff | 将需求、设计、任务、验证和交付摘要纳入统一工作流 |
| 项目级规则 | Guides、Harness Mapping | 将产品背景、技术栈、代码规范、架构约束和团队偏好转化为 Agent 可加载资产 |
| 代码库理解 | Scanner & Analyzer | 从真实仓库中识别结构、命令、文档、测试、CI、风险区域和已有工程资产 |
| 执行边界控制 | Workflow Runtime Specification、Restricted Paths、Human Escalation | 定义任务风险等级、工具调用边界、人工升级和受控执行协议 |
| 质量验证 | Sensors、Maturity & Evolution | 将测试、构建、静态分析、安全检查和质量门禁组织成可执行反馈层 |
| 经验沉淀 | Experience & Self-Improve | 将任务历史、失败模式、修复路径、Review 反馈和规则缺口转化为可审查改进候选 |
| 能力建设路线图 | Maturity & Evolution | 评估当前 Harness 成熟度，给出下一阶段能力补齐建议 |

通过这种映射，六大模块形成一套有行业依据的工程治理结构。每个模块都对应 AI Coding 工程化中的一个关键控制点，并共同服务于同一个目标：让企业既有代码库具备可控、可验证、可持续改进的 AI Coding 协作能力。

---

## 4. 总体架构：六大能力模块 + Workflow Toolkit

Harness Builder 包含六个一等能力模块，以及一个贯穿执行层的 **Workflow Toolkit（工作流武器库）**。

```text
Harness Builder
├── 1. Scanner & Analyzer
├── 2. Guides
├── 3. Sensors
├── 4. Workflow Runtime Specification
│   └── Workflow Toolkit（武器库）
│       ├── Standard Workflow
│       ├── Lightweight Workflow
│       ├── Bugfix Workflow
│       ├── Prototype-first Workflow
│       └── [可扩展的定制 Workflow 模块]
├── 5. Experience & Self-Improve
└── 6. Maturity & Evolution
```

六个模块的职责如下：

| 模块 | 一句话说明 |
|---|---|
| Scanner & Analyzer | 识别遗留代码库现状，生成 Harness 初始素材，并为 Workflow 组装提供依据 |
| Guides | 把项目知识和团队规则转成 AI 可执行的前置约束 |
| Sensors | 把验证能力和风险检查转成 AI 修改后的反馈机制 |
| Workflow Runtime Specification | 定义任务编排规范，并从 Workflow Toolkit 中组装适合当前项目的执行流程 |
| Workflow Toolkit | 行业最佳实践与内部积累 Workflow 的武器库，支持灵活组装与定制化编排 |
| Experience & Self-Improve | 从真实任务中沉淀经验，并生成可审查的 Harness 改进候选 |
| Maturity & Evolution | 评估 Harness 成熟度，规划下一阶段能力补齐路径 |

六个模块之间的关系：

```text
Scanner 负责初始化，分析项目特征，并驱动 Workflow Toolkit 选择合适的执行流程
→ Guides 提供前置约束
→ Sensors 提供后验验证
→ Workflow Runtime Specification 定义执行闭环
→ Experience 负责学习和自我演进
→ Maturity 负责评估和路线规划
→ 改进建议反哺 Guides / Sensors / Workflow / Scanner
```

### 4.0 Workflow Toolkit：武器库思想

Workflow Toolkit 是 Harness Builder 区别于"单一固定流程"的核心设计理念。

**设计思路：** Scanner & Analyzer 在分析了客户代码库的现状（技术栈、项目类型、成熟度、风险分布）并收集到足够信息之后，即可从 Toolkit 武器库中找到适合这个项目的 Workflow 模块，进行定制化组装——就像从武器库中挑选并配备合适的工具组合，而不是给所有人一套固定的标准装备。

**行业最佳实践汇聚：** Toolkit 提炼并整合了行业中已被验证的多个规范驱动开发框架的优势：

| 参照框架 | 贡献的 Workflow 理念 |
|---|---|
| GitHub Spec Kit / Kiro Specs | 先 Spec 再实现：Requirement Alignment → Solution Design → Implementation Plan |
| BMAD Method | 角色分工、任务分解和交付摘要模板 |
| Claude Code / Cursor Workflow | Prototype-first 快速验证交互和方向 |
| OpenHands / SWE-agent | Test-first Build & Verify Loop 与 Repair Loop |
| Spec-Driven Development | 验收标准前置，让每个任务都有可验证的完成定义 |

**分阶段建设：**

- **MVP 阶段（相对固定）：** Toolkit 提供预设的标准 Workflow 集合（Standard / Lightweight / Bugfix），Analyzer 自动映射到合适的预设流程，输出结果相对确定，便于快速验证。
- **长期目标（灵活组装）：** Toolkit 支持模块化 Workflow 片段（如 Prototype Preview、Solution Design、Test-first Build 等），由 Analyzer 根据项目特征灵活拼装，形成高度定制化的执行方案。
- **Toolkit 自身持续演进：** Experience & Self-Improve 模块会观察各 Workflow 片段的实际效果，推动武器库不断更新和扩充。

### 4.1 Core Harness 与 Improvement System

在目标态中，AI Coding Harness 是一套围绕 AI Coding 的工程控制系统。

核心运行层定义为：

```text
Core Harness = Guides + Sensors + Workflow Runtime Specification
```

其中：

| 层级 | 作用 | 是否参与日常开发流程 |
|---|---|---|
| Guides / Knowledge Layer | 在 AI 动手前和执行中提供上下文、规则、约束和任务模板 | 是 |
| Sensors / Verification Layer | 在 AI 修改后执行验证、捕捉问题，并把反馈送回工作流 | 是 |
| Workflow Runtime Specification / Execution Protocol Layer | 定义 AI Coding 任务应如何被执行，并确保 Guides 与 Sensors 可被底层 Runtime 稳定触发 | 是，由底层 AI Coding 工具或项目级 Skill 承载执行 |

改进层定义为：

```text
Harness Improvement System = Scanner + Experience + Maturity + Recommendation
```

职责划分如下：

- Core Harness 负责定义日常 AI Coding 任务的控制规则、验证协议和执行闭环。
- Harness Improvement System 负责初始化评估、经验沉淀、缺口分析和持续升级。
- Harness Builder 负责生成和更新上述两类产物。

### 4.2 控制机制的二维分类

Guides 和 Sensors 按控制方式分为两类。

| 类型 | 含义 | 示例 |
|---|---|---|
| Computational | 确定性的、工具化的、可重复执行的控制 | lint、typecheck、测试、依赖图检查、脚手架模板、codemod、项目生成器 |
| Inferential | 语义性的、需要模型判断的控制 | AI code review、架构评审、需求一致性检查、风险评审、过度设计检查 |

二维结构如下：

| 方向 | Computational | Inferential |
|---|---|---|
| Guides | 代码生成脚手架、codemod、模板、LSP、项目生成器 | 项目规则、AI instructions、领域知识、how-to guide、架构原则 |
| Sensors | lint、typecheck、unit test、API test、E2E test、依赖检查、架构约束检查 | AI review、语义重复检查、过度设计检查、需求一致性检查、风险评审 |

该分类用于帮助 Harness Builder 识别代码库已具备的控制机制、缺失的控制机制，以及优先补齐顺序。

### 4.3 Harness 能力维度

目标态 Harness 按治理目标分成六类能力维度。

| 维度 | 目标 | Guides 示例 | Sensors 示例 |
|---|---|---|---|
| Maintainability Harness | 保持可读、可维护、符合团队风格 | 编码规范、命名规则、文件组织、错误处理、日志规范、团队常用设计模式和反模式 | lint、formatter、typecheck、复杂度检查、重复代码检查、覆盖率检查、AI 代码评审 |
| Architecture Fitness Harness | 不破坏架构、模块边界和依赖方向 | 架构说明、分层规则、模块边界、依赖方向、禁止跨层调用约定 | 架构约束检查、依赖图检查、循环依赖检查、模块边界测试、API contract check |
| Behaviour Harness | 功能行为符合业务预期 | 业务需求、用户故事、验收标准、领域词汇表、核心业务流程图、状态机定义、approved fixtures | unit / integration / E2E test、回归测试、golden master / snapshot test、mutation testing、业务规则断言 |
| Security Harness | 不引入安全漏洞或破坏权限边界 | 鉴权授权规则、敏感数据处理、输入校验、加密脱敏、日志打码、安全禁止事项 | SAST / Semgrep、依赖漏洞扫描、secret scan、权限测试、输入校验测试、AI 安全评审 |
| Performance & Reliability Harness | 不明显降低性能、稳定性和可观测性 | 性能预算、缓存规则、超时重试、熔断降级、日志指标 trace 规范、SLO / SLA | benchmark、load test、慢查询检查、日志质量检查、可观测性检查、错误率 / 延迟 / 资源监控 |
| Data & Migration Harness | 控制数据结构、迁移脚本和数据语义风险 | 数据模型说明、schema 变更规范、migration 编写规范、回滚策略、数据兼容性要求 | migration dry-run、schema diff check、backward compatibility check、数据约束检查、数据质量测试、回滚验证 |

这些能力维度主要服务于扫描、成熟度评估和缺口分析；日常 Workflow 仍由任务类型、风险等级和 Harness Mapping 决定。

---

## 5. 端到端工作流

Harness Builder 的完整生命周期可以分为初始化、任务执行、任务后复盘和持续演进四段。

```text
初始化阶段：
扫描代码库
→ 识别技术栈、目录结构、验证命令和现有文档
→ 生成候选 Guides / Sensors / risk zones
→ 分析项目特征，从 Workflow Toolkit 中选择并组装适合的 Workflow 集合
→ 请求人类确认低置信度高影响判断
→ 生成初始 Harness
→ 生成 Maturity Report

任务执行阶段：
输入需求 / bug / refactor intent
→ Harness Mapping
→ 选择 Workflow
→ 加载 Guides
→ [按需] Prototype Preview（对 UI、外部系统或流程型功能先确认交互和业务方向）
→ 执行实现
→ 运行 Sensors
→ Repair Loop / Human Escalation
→ Review / Decision Log / Handoff

任务后复盘阶段：
读取任务记录、Sensor Report、Review 反馈
→ 提取经验
→ 生成 pending improvements
→ 人类确认
→ 更新 Guides / Sensors / Workflow / Maturity

持续演进阶段：
汇总多次任务趋势
→ 识别重复失败、缺失验证、过期规则和高风险区域
→ 生成下一阶段 Harness 升级建议
```

自我演进遵循人工确认原则。Experience 模块负责生成经验和改进候选；经验候选正式进入 Guides、Sensors、Workflow 或风险策略之前，必须经过人工确认或项目规则审批。

---

## 6. 六大能力模块详解

### 6.1 Scanner & Analyzer：扫描与识别

#### 模块价值

Scanner & Analyzer 负责建立遗留代码库的工程现状基线。它识别项目规则、验证命令、风险区域和可供 AI 使用的工程文档。

它的价值是把代码库现状转化为 Harness 的初始素材，降低客户从零设计 AI Coding 控制系统的成本。

#### 目标状态

成熟形态下，Scanner & Analyzer 应能够：

- 自动识别技术栈、框架、目录结构和模块分层。
- 自动识别构建、测试、lint、typecheck、pre-commit、CI 配置。
- 自动发现已有 Guides，例如 README、architecture.md、AGENTS.md、CLAUDE.md、团队规范和脚手架模板。
- 自动发现已有 Sensors，例如 lint、test、typecheck、build、架构测试、安全扫描。
- 反向推导候选规则、候选风险区域和候选验证机制。
- 为所有推断结果标注证据来源、置信度和适用范围。
- 把低置信度、高影响的判断交给人类确认。

#### 实现机制

Scanner & Analyzer 采用“代码库扫描 + 模型推断 + 人工确认 + 最佳实践引导”的方式建立初始 Harness。

它应区分四类信息：

| 类型 | 示例 | 处理方式 |
|---|---|---|
| 确定性可扫描 | package.json、pom.xml、go.mod、pyproject.toml、CI 配置、测试目录、构建命令 | 直接进入候选 Harness |
| 半确定性可推断 | 模块边界、高风险业务模块、核心业务流程、领域模型、缺失测试区域、高频变更区域 | 生成带置信度的候选项 |
| 必须人工确认 | 哪些模块业务后果最高、哪些目录限制 AI 修改、哪些测试 flaky、哪些风险可以接受 | 进入向导式问题 |
| 最佳实践引导补齐 | 是否需要架构规范、代码规范、测试策略、安全规则、迁移规则、Review 标准 | 当客户基础薄弱或缺少现成规范时，由 Harness Builder 给出推荐模板和补齐路线 |

候选项分为四类：

| 类型 | 含义 | 处理方式 |
|---|---|---|
| confirmed | 证据充分、风险低，可直接进入初始 Harness | 生成 active Guide / Sensor |
| candidate | 有证据但置信度不足 | 进入待确认清单 |
| rejected | 客户确认不适用 | 记录原因，不进入 Harness |
| unknown gap | 系统无法判断但影响重要 | 提醒客户补充信息 |

候选 Guide 示例：

```yaml
rule: 所有外部 API 调用必须经过 apiClient 封装
confidence: high
evidence:
  - src/services/user.ts
  - src/services/order.ts
  - src/services/payment.ts
scope:
  paths:
    - src/services/**
needs_human_confirmation: false
```

候选项必须包含证据来源。低置信度规则进入待确认清单，确认前不得升级为 Hard Gate 或强制 Guide。

#### 主要产物

```text
.ai/scan-report.md
.ai/harness-candidates.md
.ai/risk-zones.md
.ai/maturity-report.md
.ai/harness-config.yaml
```

#### 与其他模块关系

- 为 Guides 生成初始项目上下文、架构说明、编码规则和风险区域说明。
- 为 Sensors 生成已有验证命令和缺失验证能力清单。
- 为 Workflow Runtime Specification 提供任务类型、风险区域和 restricted paths。
- 为 Experience 提供初始化基线，后续经验可以与扫描结果对照。
- 为 Maturity 提供初始评分依据。

### 6.2 Guides：知识与前置约束

#### 模块价值

Guides 定义 AI 在项目中应遵循的前置知识与行为约束。它们把项目上下文、团队规则、架构原则、领域知识、风险边界和任务模板转化为 AI 可读取、可审查、可按任务加载的 Instructions as Code。

Guides 为 AI Coding 提供稳定的项目级规则来源，减少对临时 prompt、上下文窗口和模型默认经验的依赖。

#### 目标状态

成熟形态下，Guides 应成为项目级 Instructions as Code：

- **模块化**：按架构、领域、测试、安全、迁移、任务模板等主题拆分。
- **可版本控制**：随代码库一起演进，重要变更可以被 review、追溯和回滚。
- **可按需加载**：根据 Harness Mapping 的任务类型、影响范围和风险等级动态选择。
- **可证据化**：自动发现的规则应记录来源文件、代码证据、置信度和适用范围。
- **可演进**：AI 可以根据任务执行和 Review 反馈提出 Guide 更新建议，但正式生效前应经过人类确认或项目规则审批。

#### 实现机制

Guides 初始化时由 Scanner 生成初版；任务执行时由底层 AI Coding 工具或项目级 Skill 根据 Workflow Runtime Specification 和 Harness Map 加载；任务结束后由 Experience 生成更新候选；人工确认后进入正式 Guide。

Guide metadata 示例：

```yaml
id: api-error-handling-guide
scope:
  paths:
    - src/api/**
source:
  type: inferred_from_codebase
  evidence:
    - src/api/user.ts
    - src/api/order.ts
confidence: medium
owner: backend-team
last_verified_at: 2026-05-23
status: candidate
```

#### 主要产物

```text
.ai/guides/
  project-context.md
  coding-rules.md
  architecture.md
  domain-glossary.md
  ai-instructions.md
  risk-zones.md
  task-templates/
    feature.md
    bugfix.md
    refactor.md
    test-generation.md
    migration.md
```

#### 与其他模块关系

- 由 Scanner 生成初稿。
- 被底层 AI Coding 工具或项目级 Skill 按 Workflow Runtime Specification 和 Harness Map 加载。
- 与 Sensors 联动，在 Sensor 失败时加载对应 Guide。
- 被 Experience 反哺，形成 Guide 更新候选。
- 被 Maturity 评估覆盖度、结构化程度和任务加载能力。

### 6.3 Sensors：验证与反馈

#### 模块价值

Sensors 解决“AI 做完后如何验证”的问题。它们把已有测试、lint、typecheck、安全检查、架构约束、AI Review 和业务验证转化为 AI 修改后的反馈机制。

Guides 提高 AI 一次做对的概率，Sensors 承认 AI 仍会出错，并通过后验验证驱动修复闭环。

#### 目标状态

成熟形态下，Sensors 应能够：

- 覆盖 lint、formatter check、typecheck、unit test、integration test、API / contract test、E2E / UI test、build、architecture check、migration dry-run、security scan、performance benchmark、AI review / evaluator。
- 按任务类型、风险等级和影响范围动态选择。
- 区分 Hard Gate、Soft Signal 和 Human Escalation。
- 输出结构化失败上下文，让 AI 可以直接用于修复。
- 与 Guides 联动，在失败时自动加载相关规则。
- 记录执行结果，进入 Sensor Report、Experience 和 Maturity。

#### 实现机制

Sensor 可以按执行结果的处理方式分为三类：

| 类型 | 含义 | 示例 | 处理方式 |
|---|---|---|---|
| Hard Gate Sensor | 必须执行，失败时任务保持未完成状态 | typecheck、unit test、build、migration dry-run | 失败后进入 repair loop，多次失败后升级给人类 |
| Soft Signal Sensor | 非阻断型风险信号 | coverage 下降、复杂度上升、bundle size 增加、AI 架构 review | 汇总风险，进入 review summary |
| Human Escalation Sensor | 机器无法决定是否接受，需要人类判断 | 兼容性破坏、安全例外、跳过 flaky test、高风险目录修改 | 暂停或升级，记录 decision log |

每个 Sensor 应定义以下内容：

```yaml
sensors:
  typecheck:
    gate: hard
    type: computational
    run: pnpm typecheck
    parse: typescript
    applicable_tasks: [feature, bugfix, refactor, migration]
    risk_threshold: low

  architecture_review:
    gate: soft
    type: inferential
    guide: .ai/guides/architecture.md
    applicable_tasks: [feature, refactor]
    risk_threshold: medium

  migration_dry_run:
    gate: hard
    type: computational
    run: pnpm migration:dry-run
    parse: generic
    applicable_tasks: [migration]
    risk_threshold: low
    on_failure_load_guide: .ai/guides/migration-rules.md
```

Sensors 的执行目标：

```text
执行验证
→ 捕获失败
→ 结构化失败信息
→ 反馈给 AI 修复
→ 重跑相关验证
→ 通过 / 升级 / 记录遗留风险
```

#### 主要产物

```text
.ai/sensors/
  verification.md
  test-strategy.md
  architecture-checks.md
  security-checks.md
  quality-checks.md
  migration-checks.md
  review-agents.md
```

#### 与其他模块关系

- 由 Scanner 发现已有命令和验证能力。
- 被底层 AI Coding 工具、CLI、IDE 插件、CI 或项目级 Skill 按 Workflow Runtime Specification 执行、解析、反馈和升级。
- 与 Guides 通过 `on_failure_load_guide` 联动。
- 被 Experience 记录有效性、误报、漏报和修复效果。
- 被 Maturity 评估覆盖度、自动化程度和绑定 Workflow 的程度。

### 6.4 Workflow Runtime Specification：任务编排规范、执行协议与 Harness Mapping

#### 模块价值

Workflow Runtime Specification 定义 Guides、Sensors、风险策略和人工确认点应如何被执行。Harness Builder 负责生成该规范及相关配置，具体执行由 IDE 插件、CLI Agent、CI、项目级 Skill 或其他 AI Coding Runtime 承载。

它是 Harness 的任务执行协议中枢，并与底层 AI Coding Runtime 形成分层协作关系。

```text
Guides 告诉 AI 怎么做
Sensors 判断做得对不对
Workflow Runtime Specification 决定什么时候加载 Guides、什么时候运行 Sensors、失败后应如何处理；具体执行由承载 Runtime 完成
```

#### 目标状态

成熟形态下，Workflow Runtime Specification 应能够定义：

- 任务开始前应如何检查 Harness 初始化状态。
- 如何根据需求、bug 或 refactor intent 生成 Harness Map。
- 如何选择 Standard Workflow 或 Lightweight Workflow。
- 如何按任务类型、风险等级和影响范围加载 Guides。
- 如何按 immediate / staged / deferred 执行 Sensors。
- 如何将 Sensor 失败结果解析成修复上下文。
- 如何驱动 Repair Loop，并在失败多次后升级人类。
- 如何记录 Decision Log、Sensor Report、Review Summary 和 Handoff Summary。
- 如何在任务结束后把运行数据交给 Experience 和 Maturity。

#### 实现机制

Workflow Runtime Specification 内部包含三层规范：

```text
Workflow Definition：任务类型、阶段、人工确认点
Harness Mapping：每类任务要加载哪些 Guides、运行哪些 Sensors、触发哪些风险策略
Runtime & Repair Loop Protocol：定义如何按计划执行、收集 Sensor 结果、驱动修复、失败升级人工
```

##### Workflow Runtime Specification Precondition

任何项目级 AI Coding Workflow 启动前，底层 AI Coding 工具或项目级 Skill 执行 Harness 初始化状态检查。

运行前置检查包括：

- 读取 `.ai/harness-config.yaml`。
- 识别可用 Guides。
- 识别可用 Sensors。
- 读取任务类型策略。
- 读取 risk zones 和 restricted paths。
- 读取当前执行策略和修复重试策略。

当 `.ai/harness-config.yaml` 不存在时，项目处于 Harness 未初始化状态。系统应提示或触发 `harness-builder` 完成初始化，再执行开发 Workflow。

##### Standard Workflow

标准流程适用于复杂功能开发、高风险变更、跨模块改造、涉及权限 / 金额 / 数据迁移 / 安全边界的任务。

```text
1. Requirement Alignment
2. Harness Mapping
3. Solution Design
4. Prototype Preview（按需）
5. Implementation Plan
6. Test-first / Sensor-aware Build & Verify Loop
7. Review / Decision Log / PR / Handoff
```

各步骤目标：

| 步骤 | 目标 |
|---|---|
| Requirement Alignment | 把原始需求澄清成可执行、边界清晰、可验证的需求基线 |
| Harness Mapping | 将需求映射到代码库、Guides、Sensors、风险区域，并从 Workflow Toolkit 中确定执行策略 |
| Solution Design | 在编码前形成高层方案，明确实现路径和关键取舍 |
| Prototype Preview | **Workflow Toolkit 中的关键可选片段**。对 UI 交互、外部系统集成或流程型功能，在进入完整实现前先快速验证方向和用户体验。触发条件：涉及新 UI 布局、用户交互流程、不确定的业务流程、需要与外部系统对齐的接口设计。通过 Prototype 提前暴露方向性问题，避免完整实现后大幅返工。 |
| Implementation Plan | 把方案拆成可执行小任务，降低一次性大改风险 |
| Build & Verify Loop | 将实现过程绑定验证机制，失败后进入 Repair Loop |
| Review / Handoff | 输出验证结果、方案取舍、风险和交付信息 |

##### Lightweight Workflow

轻量流程适用于影响范围明确、风险较低、变更较小、不需要复杂方案设计的任务。

```text
1. Requirement Brief
2. Harness Mapping
3. Direct Implementation / Build & Verify Loop
4. Review / Handoff
```

轻量流程用于降低低风险任务的流程负担，同时保留关键控制点：

- 风险识别。
- restricted paths 判断。
- required Guides 加载。
- 必要 Sensors 执行。
- hard gate 失败后的 repair / escalation。
- 未解决风险记录。

Harness Mapping 命中以下条件时，自动升级为 Standard Workflow：

- 影响范围不清楚。
- 命中高风险模块。
- 涉及权限、金额、安全、迁移、核心业务状态。
- 需要跨模块设计。
- Sensors 覆盖不足但风险较高。
- AI 对代码影响范围判断置信度低。
- 存在必须人类确认的业务决策。

##### Bugfix Workflow

Bugfix Workflow 是 Lightweight Workflow 下的任务类型流程，用于缺陷复现、根因定位、最小修复和回归验证。

第一阶段可由一个 `bugfix` 项目级 Skill 承载。以下内容描述的是该 Skill 的内部执行阶段，不代表需要拆分成多个独立 Skill。

```text
1. Reproduce / Observe
2. Root Cause Investigation
3. Harness Mapping
4. Hypothesis & Fix Plan
5. Minimal Fix + Targeted Sensors
6. Regression Check
7. Debug / Handoff Summary
```

Bugfix Workflow 聚焦回答：

- 这个 bug 涉及哪些模块和调用链？
- 是否命中 risk zones？
- 应加载哪些 debugging guides？
- 应运行哪些 targeted sensors？
- 是否需要扩展回归测试？
- 是否存在高风险修复，需要人类确认？

##### Harness Mapping

Harness Mapping 是每次 AI Coding 任务的控制计划。

```text
Requirement / Bug / Refactor Intent
→ Harness Mapping
→ Workflow Selection
→ Guides Selection
→ Sensors Selection
→ Risk Policy
→ Execution Strategy
```

它需要决定：

- 使用 Standard Workflow 还是 Lightweight Workflow。
- 本次任务属于 feature、bugfix、refactor、migration、test-generation 还是其他类型。
- 影响哪些模块、接口、页面、数据表、任务队列。
- 是否命中 risk zones。
- 是否涉及 restricted paths。
- 风险等级是多少。
- AI 对影响范围判断的置信度是多少。
- 哪些 Guides 必须加载。
- 哪些 Sensors 必须执行。
- 哪些 Sensors 是 Hard Gate。
- 哪些风险需要人类确认。
- 是否允许自动修改代码。
- 是否需要 Prototype Preview。
- 是否需要 Solution Design。
- 是否需要记录 Decision Log。

Harness Map 示例：

```yaml
harness_map:
  task_id: feat-refund-review-001
  task_type: feature
  complexity: high
  risk_level: high

  workflow_selection:
    selected_workflow: standard
    reason:
      - 涉及退款和金额相关状态
      - 涉及订单履约状态判断
      - 涉及客服权限和主管 override
      - 涉及后台审核页面
    upgrade_from_lightweight: true

  confidence:
    requirement_clarity: medium
    code_mapping: medium
    sensor_coverage: high
    risk_assessment: medium

  affected_domains:
    - refund
    - order
    - shipment
    - customer_service
    - admin_ui

  relevant_modules:
    - src/refund/**
    - src/order/**
    - src/shipment/**
    - src/admin/refund-review/**

  guide_policy:
    required:
      - .ai/guides/domain-glossary.md
      - .ai/guides/architecture.md
      - .ai/guides/task-templates/feature.md
      - .ai/guides/risk-zones.md

  sensor_policy:
    hard_gates:
      - typecheck
      - unit_test
      - integration_test
      - api_contract_test
    soft_signals:
      - coverage_change
      - architecture_review
    deferred:
      - e2e_test
    human_escalation:
      - permission_boundary_change
      - refund_state_semantics

  risk_controls:
    restricted_paths_hit: false
    risk_zones:
      - src/refund/**
      - src/payment/**
    requires_human_approval_before_edit: true
    allow_auto_edit: false

  needs_prototype: true
  needs_solution_design: true

  decision_points:
    - “已揽收”以哪个物流状态为准？
    - 主管 override 是否必须记录审计日志？
```

##### Sensor Runtime 与 Repair Loop

Sensor Runtime 在本文中指 Sensors 生效所需的项目级运行协议。它定义哪些检查要跑、何时跑、如何解析、如何反馈和升级；具体命令执行、日志采集和权限控制由底层 AI Coding 工具、CLI、IDE 插件或 CI 承载。

```text
Sensor Definition
→ Sensor Runner
→ Result Parser
→ Repair Loop
→ Gate / Escalation
→ Sensor Report
```

Result Parser 负责把原始日志翻译成 AI 可以直接使用的修复上下文：

```yaml
repair_context:
  sensor: typecheck
  severity: hard
  failed_files:
    - path: src/refund/refund-service.ts
      errors:
        - line: 47
          message: "Argument of type 'string' is not assignable to parameter of type 'RefundStatus'"
          context: "createRefund(orderId, 'pending')"
  repair_hint: "RefundStatus is a union type defined in src/types/refund.ts. Check the allowed values."
```

Repair Loop 流程：

```text
Result Parser 输出修复摘要
→ 附加对应 Guide
→ 发给 AI Coding Agent 修复
→ Agent 修改代码
→ 只重跑之前失败的 Sensors
→ 失败次数未超上限 → 继续 Repair Loop
→ 失败次数超上限 → Gate / Escalation
```

Gate / Escalation 规则：

| 情况 | 处理方式 |
|---|---|
| 所有 Hard Gate Sensor 通过 | 任务完成，进入 Review & Handoff |
| Hard Gate Sensor 超出修复次数上限 | 升级给人类，附上失败摘要和修复历史 |
| Soft Signal Sensor 触发 | 汇总风险摘要，附入 Review，由 AI 解释影响 |
| Human Escalation Sensor 触发 | 暂停任务，请求人类决策，记录 Decision Log |

#### 主要产物

```text
.ai/harness-config.yaml
.ai/task-runs/<task-id>/harness-map.yaml
.ai/task-runs/<task-id>/sensor-report.yaml
.ai/task-runs/<task-id>/decision-log.md
.ai/task-runs/<task-id>/handoff-summary.md
.skills/<task-skill>/SKILL.md
```

#### 与其他模块关系

- 消费 Guides 和 Sensors。
- 依赖 Scanner 识别出的配置、命令、risk zones 和 restricted paths。
- 把执行结果、失败上下文、人工决策和 handoff 交给 Experience。
- 把 Sensor 覆盖度、Repair Loop 成功率和升级事件交给 Maturity。

### 6.5 Experience & Self-Improve：经验沉淀与自我演进

#### 模块价值

Experience & Self-Improve 负责让 Harness Builder 在项目使用过程中持续积累工程经验。

它从真实任务中提取失败模式、成功修复、团队偏好、Sensor 误报、Review 反馈和规则缺口，并将这些信息沉淀为可审查、可版本化、可反哺 Harness 的经验资产。

它的价值是让每个客户项目形成自己的 AI Coding 经验资产，并把这些经验持续反哺 Guides、Sensors、Workflow 和 Maturity。

#### 目标状态

成熟形态下，Experience & Self-Improve 应能够：

- 从每次任务中提取可复用经验。
- 识别重复失败模式和有效修复策略。
- 记录哪些 Guides 有用、哪些 Guides 不清楚或过期。
- 记录哪些 Sensors 有效、哪些误报、哪些漏报。
- 记录团队偏好、代码审查意见和高频决策。
- 生成 Harness 改进候选，并将正式规则修改纳入人工确认流程。
- 通过人工确认将候选经验转化为 Guide / Sensor / Workflow / Maturity 更新。
- 在框架升级时保护客户经验文件不被覆盖。

#### 实现机制

第一阶段采用轻量、可审查、可版本化的 Markdown 经验文件，不引入复杂数据库或跨客户自动学习。

经验资产结构：

```text
.ai/experience/
  project-experience.md
  repair-patterns.md
  sensor-feedback.md
  team-preferences.md
  pending-improvements.md
  deprecated-experience.md

.ai/skills/
  feature/
    experience.md
  debug/
    experience.md
  review/
    experience.md
```

每次 Workflow 结束后，Harness Builder 做一次轻量复盘，抽取：

- 这次任务触发了哪些 Guides？
- 哪些 Guides 不够清楚？
- 哪些 Sensors 有效？
- 哪些 Sensors 误报或漏报？
- Repair Loop 是怎么成功的？
- 人类 Review 提了哪些重复性意见？
- 是否暴露出新的风险目录、业务规则、架构边界？
- 需要补充的 Sensor、Guide 或 Workflow 升级条件。

复盘结果进入 `pending-improvements.md`：

```yaml
pending_improvement:
  id: refund-status-guide
  source_task: feat-refund-review-001
  evidence:
    - Review 中多次确认“已揽收”状态语义
    - 当前 domain-glossary.md 未定义物流状态与退款状态映射
  suggested_update:
    target: .ai/guides/domain-glossary.md
    add: “已揽收”与退款审核状态的权威映射
  target_modules:
    - src/refund/**
    - src/shipment/**
  confidence: medium
  risk: high
  status: pending_human_review
```

经验确认后，反哺五类 Harness 资产：

| 反哺对象 | 示例 |
|---|---|
| Guide Update | 补充团队规则、架构约束、领域知识 |
| Sensor Update | 新增 Sensor、调整 Sensor 严格度、记录误报模式 |
| Workflow Update | 某类任务必须先跑某个检查，或必须升级标准流程 |
| Harness Mapping Update | 让类似任务以后自动加载相关经验和验证 |
| Maturity Report Update | 把反复出现的问题变成成熟度缺口 |

关键边界：

```text
经验可由 AI 生成，正式规则变更必须经过确认。
经验默认项目内隔离，不跨客户复用。
框架升级不得覆盖客户经验文件。
过期经验必须能被标记、废弃或回滚。
高风险经验，比如安全、权限、数据迁移规则，必须人工确认。
```

#### 经验反哺的风险控制

Experience & Self-Improve 的核心风险在于经验资产进入正式 Harness 后，会被后续任务持续加载和复用。错误、过期、局部化或低质量经验一旦被固化，可能放大为团队级规则偏差，影响后续 AI Coding 的稳定性和质量。

经验反哺需要建立从候选、审核、生效、观察到废弃的完整控制链路。

```text
任务经验
→ 候选经验
→ 证据标注
→ 范围限定
→ 风险分级
→ 人工确认
→ 小范围生效
→ 持续观察
→ 扩大 / 调整 / 废弃 / 回滚
```

主要风险与控制方式如下：

| 风险类型 | 风险说明 | 控制方式 |
|---|---|---|
| 错误经验固化 | AI 或人工复盘可能从单次任务中提取出错误结论，并写入正式规则 | 经验默认进入候选区；必须记录来源任务、证据、置信度、风险等级和审核状态 |
| 局部经验泛化 | 某个模块、页面或业务场景的局部规则被扩大为全局规则 | 每条经验必须标注路径范围、模块范围、任务类型和适用条件；局部规则升级为全局规则需要额外确认 |
| 过期经验延续 | 代码结构、架构规范或业务流程变化后，旧经验继续影响后续任务 | 记录 `last_verified_at`；关联文件或目录发生重大变化时触发复核；支持废弃、替换和回滚 |
| Review 反馈污染 | 单次 Review 意见可能只是个人偏好，未必代表团队规范 | 区分个人偏好、团队约定、架构规则和强制规范；重复出现或负责人确认后再升级为正式 Guide |
| Sensor 误报吸收 | flaky test、安全扫描误报或 AI Review 误判被当成真实规则缺口 | Sensor 反馈记录真实问题、误报、漏报、flaky、人工豁免等状态；高误报 Sensor 进入降级或调整建议 |
| Harness 复杂度膨胀 | 经验持续增加导致 Guides 过长、Sensors 过多、低风险任务流程过重 | 新增规则和 Sensor 需要评估收益、成本和适用范围；保留 minimal / standard / strict 配置档位；定期清理低价值和重复经验 |

经验候选正式进入 Harness 前，应至少包含以下结构化信息：

```yaml
experience_candidate:
  id: refund-status-guide
  source_task: feat-refund-review-001
  source_type: review_feedback
  evidence:
    - Review 中多次确认“已揽收”状态语义
  suggested_target: .ai/guides/domain-glossary.md
  scope:
    paths:
      - src/refund/**
      - src/shipment/**
    task_types:
      - feature
      - bugfix
  confidence: medium
  risk_level: high
  review_status: pending_harness_maintainer_review
  last_verified_at: null
  expiry_policy: review_when_related_paths_change
```

经验反哺遵循以下原则：

- 经验默认进入候选区，正式生效前需要审核。
- 每条经验必须记录来源、证据、适用范围、置信度、风险等级和审核状态。
- 高风险经验必须由 Harness Maintainer 确认。
- 局部经验默认局部生效，扩大适用范围需要额外确认。
- 过期、冲突、误报和低价值经验必须支持废弃或回滚。
- Harness 演进需要控制复杂度，避免规则、Sensors 和流程持续膨胀。

#### 主要产物

```text
.ai/experience/project-experience.md
.ai/experience/repair-patterns.md
.ai/experience/sensor-feedback.md
.ai/experience/team-preferences.md
.ai/experience/pending-improvements.md
.ai/experience/deprecated-experience.md
```

#### 与其他模块关系

- 消费承载 Runtime 按 Workflow Runtime Specification 产生的任务记录、Sensor Report、Decision Log 和 Handoff Summary。
- 向 Guides 提出规则、领域知识、架构说明和任务模板更新候选。
- 向 Sensors 提出新增、降级、升级、误报标记和 parser 改进候选。
- 向 Workflow Runtime Specification 提出流程升级条件、任务路由和人类确认点更新候选。
- 向 Maturity 提供真实任务数据，使成熟度评估结合初始化扫描与持续运行结果。

### 6.6 Maturity & Evolution：成熟度评估与演进路径

#### 模块价值

Maturity & Evolution 负责评估当前 Harness 能力水平，并规划下一阶段能力补齐路径。

企业客户需要持续了解 Harness 当前成熟度、未覆盖风险和下一阶段能力建设优先级。

#### 目标状态

成熟形态下，Maturity & Evolution 应能够：

- 评估项目当前 AI Coding 控制能力。
- 识别 Guides、Sensors、Workflow、Risk Control、Repair Loop、Observability、Experience 等维度的缺口。
- 给出下一步补齐优先级。
- 基于真实任务数据持续更新成熟度判断。
- 形成项目级、团队级甚至组织级 Harness 演进路线。

#### 实现机制

成熟度分级：

##### L0：Ad-hoc Prompting

- 没有稳定规则。
- 靠开发者临时 prompt。
- 没有固定验证闭环。
- AI Coding 结果高度依赖个人经验。

##### L1：Documented Guides

- 有项目说明、编码规范、AI instructions。
- AI 可以读取并尝试遵循。
- Sensors 稳定性不足，工作流尚未固化。

##### L2：Executable Sensors

- 有可运行的 lint / typecheck / test / build。
- Harness 能自动发现并执行部分 checks。
- Repair Loop 和任务 Workflow 完整度不足。

##### L3：Workflow-bound Harness

- 有项目级 AI Coding Skills。
- Guides / Sensors 被嵌入任务流程。
- Sensor 失败会反馈给 AI 修复。
- Hard Gate 不可跳过。

##### L4：Adaptive & Self-Improve Harness

- 按任务类型和风险等级动态选择 Guides 和 Sensors。
- 自动发现缺失测试和风险区域。
- 能持续更新 Harness。
- 能生成成熟度报告和改进建议。
- 能从任务历史中沉淀经验并形成可审查的改进候选。

成熟度评分维度：

| 维度 | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|
| Guides | 无 | 有零散文档 | 有结构化 Guides | 按任务类型加载 | 按风险和上下文动态加载 |
| Sensors | 无 | 手动执行 | 可自动发现和执行 | 绑定 Workflow | 动态选择并持续演进 |
| Workflow | 临时 prompt | 有人工流程 | 有半自动流程 | Skill 固化 | 自适应路由 |
| Risk Control | 无 | 人工提醒 | 有 risk zones 文档 | Workflow 强制策略 | 自动识别与升级 |
| Repair Loop | 无 | 人工修复 | AI 可读日志 | 自动重试 | 基于历史优化 |
| Observability | 无 | 简单总结 | Sensor Report | Decision Log + Handoff | 趋势和健康度面板 |
| Experience | 无 | 零散人工经验 | 有任务后记录 | 有 pending improvements | 可持续反哺 Harness |
| Verification Sophistication | 无自动验证 | lint / typecheck / test | task-to-sensor mapping | invariant / property-based sensors | deterministic replay + fault injection |
| Governance & Auditability | 无记录 | 简单 Handoff Summary | Sensor Report + Decision Log | Workflow Event Store | 可审计、可回放、可追责的 Agentic SDLC 记录 |

成熟度阻断规则：

- 没有结构化 Guides，最高只能到 L0 / L1。
- 没有可执行 Sensors，最高只能到 L1。
- Sensors 没有绑定 Workflow，最高只能到 L2。
- Hard Gate 可以被随意跳过时，最高等级为 L2。
- 缺少 risk-based routing 时，最高等级为 L3。
- 缺少 Sensor Report 和 Decision Log 时，最高等级为 L3。
- 缺少 Experience 记录和 pending improvements 时，最高等级为 L3。
- 缺少任务级审计事件或可回放记录时，最高等级为 L3。

成熟度报告示例：

```yaml
maturity:
  overall_level: L2
  dimension_scores:
    guides: L1
    sensors: L2
    workflow: L1
    risk_control: L1
    repair_loop: L0
    observability: L1
    experience: L0
    verification_sophistication: L1
    governance_auditability: L1
  blocking_reasons:
    - Sensors 尚未绑定项目级 Workflow
    - Sensor 失败后没有自动 repair loop
    - risk zones 需要人工确认
    - 尚未建立任务后经验沉淀机制
  recommended_next_steps:
    critical:
      - 生成项目级 feature / bugfix 任务流程
      - 将 typecheck / unit_test / build 设为 hard gates
      - 建立 .ai/experience/pending-improvements.md
    recommended:
      - 增加 risk-zones.md
      - 增加 sensor report 输出
      - 增加任务后复盘模板
```

#### 主要产物

```text
.ai/maturity-report.md
.ai/evolution-plan.md
.ai/harness-health.md
```

#### 与其他模块关系

- 基于 Scanner 的初始化结果生成第一版成熟度评估。
- 基于 Workflow Runtime Specification、承载 Runtime 和 Experience 的真实任务数据持续更新。
- 向 Guides、Sensors、Workflow 和 Experience 输出下一阶段补齐建议。

---

## 7. 输出资产结构

Harness Builder 的目标态输出包括以下项目级资产。

```text
.ai/
  harness-config.yaml
  scan-report.md
  harness-candidates.md
  risk-zones.md
  maturity-report.md
  evolution-plan.md

  guides/
    project-context.md
    coding-rules.md
    architecture.md
    domain-glossary.md
    ai-instructions.md
    risk-zones.md
    task-templates/
      feature.md
      bugfix.md
      refactor.md
      test-generation.md
      migration.md

  sensors/
    verification.md
    test-strategy.md
    architecture-checks.md
    security-checks.md
    quality-checks.md
    migration-checks.md
    review-agents.md

  experience/
    project-experience.md
    repair-patterns.md
    sensor-feedback.md
    team-preferences.md
    pending-improvements.md
    deprecated-experience.md

  task-runs/
    <task-id>/
      harness-map.yaml
      sensor-report.yaml
      decision-log.md
      handoff-summary.md
      experience-candidates.md

.skills/
  <task-skill>/
    SKILL.md
```

### 7.1 输出资产契约

Harness Builder 输出的项目级资产需要同时满足人类审查和系统执行两类要求。

面向人类审查的资产用于解释规则来源、设计意图、风险判断、成熟度缺口和经验沉淀；面向系统执行的资产用于让底层 AI Coding 工具、IDE 插件、CLI、CI 或项目级 Skill 稳定读取和执行 Harness 策略。

因此，输出资产分为三类：

| 类型 | 主要用途 | 典型资产 |
|---|---|---|
| 人类可审查资产 | 帮助 Harness Maintainer、开发团队和管理者理解规则、风险、成熟度和改进建议 | `scan-report.md`、`maturity-report.md`、`evolution-plan.md`、`handoff-summary.md`、`pending-improvements.md` |
| 机器可执行契约 | 为底层执行环境提供稳定、结构化、可解析的配置和策略 | `harness-config.yaml`、`harness-map.yaml`、`sensor-report.yaml`、Sensor 定义、Workflow 策略、风险策略 |
| 混合型资产 | 同时具备人类可读说明和结构化元数据，便于审查、加载和追踪 | 带元数据的 Guides、候选规则、经验文件、风险区域、任务模板 |

#### 人类可审查资产

人类可审查资产以 Markdown 为主，重点表达上下文、原因、证据、判断和建议。

这类资产应满足：

- 说明规则或建议的来源。
- 标注适用范围、影响模块和风险等级。
- 保留 Harness Maintainer 可以审查和修改的文字说明。
- 适合进入代码评审、团队讨论、客户交付或管理汇报。

示例资产包括：

```text
.ai/scan-report.md
.ai/maturity-report.md
.ai/evolution-plan.md
.ai/task-runs/<task-id>/handoff-summary.md
.ai/experience/pending-improvements.md
```

#### 机器可执行契约

机器可执行契约以 YAML / JSON 等结构化格式为主，重点表达 承载运行环境必须稳定消费的配置、策略、映射关系和执行结果。

这类资产应满足：

- 字段含义稳定。
- 支持版本号和结构演进。
- 可被底层 AI Coding 工具、IDE 插件、CLI、CI 或项目级 Skill 直接读取。
- 关键字段避免依赖自然语言自由解释。
- 影响执行路径的配置必须结构化表达。

示例资产包括：

```text
.ai/harness-config.yaml
.ai/task-runs/<task-id>/harness-map.yaml
.ai/task-runs/<task-id>/sensor-report.yaml
```

适合结构化表达的内容包括：

- 任务类型。
- 风险等级。
- 影响模块。
- 必须加载的 Guides。
- 必须执行的 Sensors。
- 强制门禁、软信号和人工升级。
- 受限路径。
- 修复重试策略。
- 工作流选择。
- 决策点。

#### 混合型资产

混合型资产用于连接人类审查和系统执行。它们通常采用 Markdown 正文 + YAML 元数据，或 Markdown 文档中嵌入结构化元数据的方式。

这类资产适合表达：

- Guides 的适用范围、来源、置信度和状态。
- 候选规则的证据来源和人工确认状态。
- 经验条目的来源任务、风险等级、目标文件和审核状态。
- 风险区域的路径、风险原因和处理策略。

示例：

```yaml
---
id: api-error-handling-guide
asset_type: guide
status: active
scope:
  paths:
    - src/api/**
source:
  type: inferred_from_codebase
  evidence:
    - src/api/user.ts
    - src/api/order.ts
confidence: medium
owner: backend-team
last_verified_at: 2026-05-24
---
```

资产契约的核心原则是：

```text
影响执行的内容必须结构化；
影响理解和审查的内容必须可读；
同时影响执行和审查的内容必须同时保留结构化元数据和文字说明。
```

---

## 8. harness-config.yaml 示例

```yaml
version: 1

runtime:
  default_workflow: lightweight
  allow_workflow_upgrade: true
  require_user_confirmation_for_high_risk: true

platform_capabilities:
  rules_engine: provided_by_ai_coding_tool
  knowledge_base: provided_by_ai_coding_tool
  command_guardrails: provided_by_ai_coding_tool
  audit_log: provided_by_ai_coding_tool
  isolation:
    supported_modes: [worktree]
    default_mode: worktree

experience:
  enabled: true
  storage: markdown
  pending_improvements: .ai/experience/pending-improvements.md
  require_human_review_before_apply: true
  protect_on_framework_upgrade:
    - .ai/experience/**
  default_scope: project_only

sensor_runtime:
  max_repair_attempts: 3
  feed_logs_to_agent: true
  rerun_failed_only: true
  escalation:
    after_attempts: 3
    require_human_decision: true

task_types:
  feature:
    workflow_policy:
      default: standard
      allow_lightweight_when:
        - risk_level: low
        - affected_modules_count_lte: 2
        - no_restricted_paths: true
      require_standard_when:
        - risk_level: high
        - touches_risk_zone: true
        - touches_security_or_permission: true
        - touches_migration: true
    guides:
      - .ai/guides/project-context.md
      - .ai/guides/architecture.md
      - .ai/guides/domain-glossary.md
      - .ai/guides/task-templates/feature.md
    required_sensors:
      immediate:
        - typecheck
        - lint
        - unit_test
      staged:
        - integration_test
        - build
      deferred:
        - e2e_test
    ai_reviews:
      - requirement_alignment_review
      - architecture_review

sensors:
  typecheck:
    gate: hard
    type: computational
    run: pnpm typecheck
    parse: typescript

  unit_test:
    gate: hard
    type: computational
    run: pnpm test:unit
    parse: vitest

  architecture_review:
    gate: soft
    type: inferential
    guide: .ai/guides/architecture.md

risk_zones:
  - path: src/payment/**
    policy: require_plan_before_edit
    required_sensors:
      - unit_test
      - integration_test
      - security_review

restricted_paths:
  - db/migrations/**

platform_policy_mapping:
  note: Harness Builder provides project-level policy mapping for platform capabilities.
  high_risk_tasks:
    use_platform_command_guardrails: true
    require_human_gate: true
  restricted_path_tasks:
    allow_auto_edit: false
    allow_advisory_output: true
```

---

## 9. 产品路线图：MVP / 中期 / 长期

路线图以阶段价值为主线，并明确六个模块在各阶段的能力支撑。

### 9.1 MVP：跑通最小可验证闭环

MVP 的目标：

> 为真实遗留代码库生成可执行的项目级 AI Coding Harness，并通过项目级 Skill 跑通一次任务。

MVP 验证三个核心问题：

1. **自动发现已有工程控制**  
   输入一个真实遗留代码库，Harness Builder 能识别技术栈、测试命令、lint / typecheck / build、现有文档、目录结构和潜在 risk zones。

2. **生成可执行的 Harness**  
   生成最小但可运行的 `.ai/harness-config.yaml`、基础 Guides、基础 Sensors、项目级 Skill 和 Maturity Report。

3. **跑通一次任务闭环**  
   用一个真实小任务验证读取 Harness、生成 Harness Map、从 Workflow Toolkit 选择 Workflow、加载 Guides、修改代码、运行 Sensors、失败后 repair、生成 handoff summary。

**MVP 阶段的 Workflow Toolkit 形态（相对固定）：** 提供预设的三种 Workflow（Standard / Lightweight / Bugfix），Analyzer 根据任务类型和风险等级自动映射，输出结果相对确定，不要求灵活组装。Prototype Preview 作为 Standard Workflow 中的内置可选步骤，当 Harness Mapping 判断 `needs_prototype: true` 时触发。

MVP 阶段的 Self-Improve 能力聚焦任务后经验候选闭环：

```text
任务后复盘
→ 生成 experience-candidates
→ 写入 pending-improvements
→ 人类确认后手动更新 Harness
```

### 9.2 中期：稳定服务多任务类型

中期目标是让 Harness Builder 从“一次试运行”变成“日常任务可持续使用”。

能力重点：

- 多任务 Workflow Routing。
- **Workflow Toolkit 初步模块化：** Prototype Preview、Solution Design、Test-first Build 等步骤开始作为可独立配置的 Toolkit 片段，支持按项目类型启用或禁用。
- 更完整的 Sensor Runtime。
- 结构化 Result Parser。
- Repair Loop 记录和失败趋势分析。
- Sensor 命中统计、误报和漏报记录。
- Experience Store 从 Markdown 走向半结构化。
- Maturity Report 基于真实任务数据持续更新。

### 9.3 长期：Self-Improve Harness Agent

长期目标是让 Harness Builder 成为企业级 Self-Improve Harness Agent。

能力重点：

- **Workflow Toolkit 完整灵活组装：** Analyzer 根据项目特征（技术栈、成熟度、风险分布、任务模式）从 Toolkit 中自动选择并拼装定制化 Workflow，不同项目可以有截然不同的执行流程。
- **Toolkit 自我演进：** Experience & Self-Improve 持续观察各 Workflow 片段的效果，自动生成武器库改进建议，经人工确认后更新。
- 组织级 Harness Pattern Library。
- 跨项目经验迁移，并默认执行隔离、脱敏和人工确认。
- Self-Improve Dashboard。
- Workflow Event Store。
- CI Integration 形成团队级治理闭环。
- IDE / 插件内可视化 Harness Mapping、Sensor 状态、Repair Loop 和经验候选。
- 高级验证能力，例如 invariant、property-based sensors、deterministic replay、fault injection。

---

## 10. 各阶段能力矩阵

| 模块 | MVP | 中期 | 长期 |
|---|---|---|---|
| Scanner & Analyzer | 识别技术栈、目录结构、测试 / lint / build 命令、现有文档、基础 risk zones | 深度架构扫描、依赖边界识别、高频变更区域、缺失测试区域 | 多项目模式识别、组织级扫描基线 |
| Guides | 生成 project-context、coding-rules、risk-zones、task templates | 按任务类型和风险动态加载，支持来源证据和冲突处理 | 组织级 Guide 模板、过期检测、跨项目可迁移 Pattern |
| Sensors | 接入已有 typecheck / lint / test / build，区分 hard gate / soft signal | Sensor Runtime、结构化 parser、failed-only rerun、on_failure_load_guide | 高级语义 Sensor、趋势分析、CI 结果回读、高级验证能力 |
| Workflow Runtime Specification | Standard / Lightweight 基础流程、Harness Mapping、一次 Build & Verify Loop 协议 | 多任务 Workflow Routing、Event Log、Repair Loop 统计、人类升级策略 | 可视化执行协议、策略调优、企业级流程治理 |
| Experience & Self-Improve | Markdown 经验文件、任务后复盘、pending improvements、人工确认 | 结构化 Experience Store、Sensor 反馈统计、Repair Pattern 推荐 | 组织级 Harness Pattern Library、跨项目经验迁移、Self-Improve Dashboard |
| Maturity & Evolution | 初始成熟度报告、缺口分析、下一步建议 | 持续成熟度追踪、基于任务历史的缺口推荐 | 组织级治理评估、趋势面板、年度 / 季度 Harness 演进计划 |

---

## 11. 失败场景与降级策略

企业级产品方案需要定义明确的失败处理策略。

| 失败场景 | 处理策略 |
|---|---|
| 找不到测试命令 | 标记 Sensor 缺失，要求客户确认或补充 |
| 测试命令长期失败 | 标记为 unstable sensor，进入人工确认流程 |
| AI 无法判断 risk zone | 降级为人工确认 |
| Guides 文档冲突 | 要求客户选择权威来源，并记录冲突 |
| Sensor 运行依赖外部环境 | 标记为 deferred 或 manual sensor |
| 代码库过大扫描超时 | 执行目录级扫描，再按任务进行局部扫描 |
| 生成的 Harness 太重 | 提供 minimal / standard / strict 配置档位 |
| Restricted path 被命中 | 阻止自动修改，生成修改建议并触发人工确认 |
| Repair Loop 多次失败 | 提前终止并升级，附失败摘要和修复历史 |
| Sensor 日志过长 | 截断原始日志，生成结构化摘要 |
| 低置信度 Harness Mapping | 要求用户确认影响范围和风险等级 |
| 任务中途发现风险升级 | 从 Lightweight Workflow 升级到 Standard Workflow |
| 经验候选相互冲突 | 保留冲突项，要求人类确认权威版本 |
| 经验候选来自失败任务 | 标记为 low confidence，进入人工确认流程 |
| 框架升级覆盖客户经验 | 禁止覆盖 `.ai/experience/**`，只更新模板和框架文件 |

关键原则：

> Harness Builder 的失败处理必须产生可行动的下一步处理策略。

---

## 12. 产品形态演进

目标态产品形态保留三类：

```text
独立 Skill 验证
→ 整合进自有 AI Coding IDE / 插件
→ 接入 CI Integration，形成团队级治理闭环
```

### 12.1 Skill 形态：第一阶段独立验证

第一阶段以独立 Skill 形态验证可行性。

适用场景：

- 客户开发团队中的 Harness Maintainer 为真实遗留代码库生成第一版项目级 AI Coding Harness。
- 一线开发团队基于生成的 Harness 跑通真实 AI Coding 任务。
- FDE / 方案团队在客户现场协助初始化、解释结果、推进试点和完成交接。
- 早期试点客户用一个真实代码库验证闭环。
- 内部团队用典型项目沉淀 Harness 模板和最佳实践。

Skill 形态重点证明：

```text
扫描代码库
→ 生成 Guides / Sensors / Workflow
→ 跑通一次真实任务
→ 输出验证报告、经验候选和改进建议
```

### 12.2 IDE / 插件形态：成为 AI Coding 产品护城河

独立 Skill 验证完成后，下一阶段将 Harness Builder 整合进自有 AI Coding IDE 或插件产品中。

可整合能力包括：

- 项目初始化时自动提示运行 Harness Builder。
- 通过 IDE 现有界面展示 Harness Mapping。
- 根据任务类型和风险等级推荐 Standard / Lightweight Workflow。
- 调用底层规则 / 知识能力加载相关 Guides。
- 自动触发对应 Sensors。
- 在编辑器内展示 Sensor 失败摘要和 Repair Loop 过程。
- 对 risk zones / restricted paths 做实时提醒。
- 在任务完成时生成 Handoff Summary、Decision Log 和 Experience Candidates。
- 在项目面板中展示 Harness Maturity、缺口建议和 pending improvements。

### 12.3 CI Integration 形态：形成团队级治理闭环

CI Integration 面向团队交付体系和长期治理。

能力包括：

- 将关键 Sensors 接入团队交付流水线。
- 持续监控 Harness 健康状态。
- 将 CI 失败结果反馈给 AI Coding 流程。
- 支持长期趋势分析。
- 识别 flaky tests、缺失测试和验证覆盖盲区。
- 为 Maturity Report 和 Experience 提供持续数据来源。
- 将 Harness 结果接入已有 PR、质量门禁和审计流程。

IDE / 插件与 CI Integration 结合后形成完整闭环：

```text
IDE 中进行任务级 Harness Mapping
→ 开发过程中加载 Guides 并运行 Sensors
→ PR / CI 阶段继续执行 Hard Gates
→ 失败结果反馈给 AI Coding 流程
→ 长期数据进入 Experience 和 Maturity Report
→ 反向优化 Harness 配置和团队规则
```

---

## 13. 下一阶段专项设计范围

本规划文档定义 Harness Builder 的产品定位、目标态架构和核心能力边界。进入 MVP 实施设计阶段后，需要进一步细化以下专项规格：

| 专项 | 需要细化的内容 |
|---|---|
| Harness Builder Skill | 向导式流程、交互步骤、输入输出、异常处理和验收标准 |
| 项目级 Skill 模板 | Standard Workflow、Lightweight Workflow、Bugfix Workflow 的模板结构和任务入口 |
| Workflow 切换策略 | 任务类型、风险等级、影响路径、验证要求和人工升级条件 |
| Sensor Runtime | 失败日志解析格式、重试策略、failed-only rerun、结果结构化和 Repair Loop 触发规则 |
| Maturity 评分细则 | 各成熟度等级的评分指标、证据要求、权重和晋级条件 |
| `harness-config.yaml` schema | 字段定义、版本演进、默认值、兼容策略和校验规则 |
| Experience 审核流程 | 经验候选模板、证据字段、风险等级、确认流程、废弃和回滚机制 |
| Guides / Sensors 识别 | 从代码库、文档、CI、测试和团队规范中识别已有控制资产的方法 |
| 风险区域识别 | risk zones、restricted paths、只读区域、建议型区域和人工确认区域的判定标准 |
| 规范导入与冲突处理 | 客户已有规范导入、冲突 Guides 处理、冲突经验处理和过期经验治理 |
| IDE / CI 集成 | IDE 插件、CLI、CI、质量平台和团队审计流程的接入方式 |
| 效果衡量 | AI Coding 质量、效率、返工率、验证覆盖、Review 问题和成熟度变化的评估口径 |
| 组织级复用 | 跨项目 Pattern Library、脱敏、隔离、人工确认和错误经验传播防护 |

---

## 14. 总结

Harness Builder 的目标是让 AI 在企业真实工程约束中更安全、更可控、更可验证地写代码，并在长期使用中逐步变得更懂这个项目。

v1.0 的核心判断是：

- Scanner：识别当前代码库的工程资产和控制基础。
- Guides：定义 AI 应遵循的项目知识与前置约束。
- Sensors：定义 AI 修改后的验证与反馈机制。
- Workflow Runtime Specification：定义 Guides、Sensors、风险策略和人工确认点的执行闭环规范。
- Experience：沉淀真实任务经验并形成 Harness 改进候选。
- Maturity：评估当前 Harness 成熟度并规划下一阶段能力补齐路径。

目标态 Harness Builder 的端到端能力包括：

```text
扫描代码库
→ 识别已有工程控制
→ 补齐关键 Guides 与 Sensors
→ 生成项目级 Workflow Runtime Specification 配置
→ 根据任务动态生成 Harness Map
→ 由承载 Runtime 执行标准或轻量 Workflow
→ 由承载 Runtime 运行 Sensors 并驱动 Repair Loop
→ 输出 Review / Decision Log / Handoff Summary
→ 任务后生成经验候选
→ 人类确认后反哺 Harness
→ 生成成熟度报告和下一步改进建议
```

最终，它帮助企业完成从“临时 prompt 驱动的 AI Coding”到“工程 Harness 驱动的 AI Coding”，再到“经验持续复利的 Self-Improve AI Coding Governance”的转变。
