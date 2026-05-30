---
title: Harness Builder — Agent POC计划
date: 2026-05-30
status: draft
tags:
  - 词元无限
  - Harness-Builder
  - POC
  - AI-Coding
  - Agent
related:
  - "[[Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器]]"
---

# Harness Builder — Agent POC计划

> **计划定位**：本计划基于完整方案 `Harness Builder — 面向遗留代码库治理的 AI Coding Harness 生成器.md`，用于定义 Harness Builder Agent 的首轮 POC 范围。  
> **核心目标**：验证一个独立 Harness Builder Agent 能否面向真实代码库生成第一版项目级 AI Coding Harness，并用这套 Harness 跑通一次受控 AI Coding 任务闭环。  
> **推荐技术栈**：Python + LangChain Deep Agents 做快速 POC；核心扫描、生成、校验与命令执行逻辑保持确定性、schema 化、可迁移。

---

## 1. POC 的核心判断

完整方案中的 Harness Builder 是一个面向企业遗留代码库的 **AI Coding Harness 生成与演进 Agent**。POC 需要证明它能从真实代码库出发，建立项目级 AI Coding 控制基线，并支撑任务级执行闭环：

```text
真实代码库
→ 自动识别已有工程控制资产
→ 生成项目级 Harness（Guides / Sensors / Workflow Skills / Maturity）
→ 根据任务生成 Harness Map
→ 选择合适 Workflow Skill
→ 加载 Guides
→ 运行 Sensors
→ 输出验证、交接和经验候选
```

因此，本 POC 应该验证完整方案中的最小产品闭环：

> **Harness 初始化 + 一次受控任务闭环。**

---

## 2. POC 要回答的问题

本 POC 需要回答四个问题。

### 2.1 Harness Builder Agent 能否建立项目级 Harness 基线？

输入一个真实代码库后，Agent 能否识别：

- 技术栈和框架。
- 目录结构和模块边界。
- 构建、测试、lint、typecheck 等验证命令。
- 已有文档、规则、CI、Docker、配置资产。
- 可作为 Guides / Sensors / Workflow 输入的工程控制素材。

### 2.2 Agent 能否生成可审查、可执行的 `.ai/` Harness 资产？

输出不应只是一篇自然语言报告，而应包括：

- 面向人类审查的 Markdown 资产。
- 面向 Runtime 消费的 YAML / JSON 契约。
- 带证据来源、置信度和人工校准点的候选项。

### 2.3 Agent 能否基于 Harness 跑通一次任务级控制闭环？

给定一个小型 bugfix 或低风险 feature 任务，Agent 能否：

- 生成 Harness Map。
- 判断任务类型和风险等级。
- 选择 Lightweight Workflow 或 Bugfix Workflow。
- 加载相关 Guides。
- 运行必要 Sensors。
- 输出 Handoff Summary 和 Decision Log。

### 2.4 这套闭环是否能支撑后续产品化？

POC 结束后，应能判断：

- 哪些能力适合继续沉淀为核心产品能力。
- 哪些能力只是演示脚手架。
- Deep Agents 是否适合作为短期 POC 外壳。
- 后续是否需要下沉到 LangGraph 显式工作流或自定义确定性管线。

---

## 3. 推荐 POC 范围

### 3.1 一句话范围

```text
做一个独立 Harness Builder Agent，能够同时面向 Java / Spring Boot 与 .NET / ASP.NET Core 两类真实开源代码库生成第一版 .ai Harness 资产，并用一个小任务跑通 Lightweight / Bugfix 控制闭环。
```

### 3.2 端到端演示流程

POC 演示建议按以下路径展开：

```text
1. 在真实代码库根目录运行 harness-builder-agent init
2. Agent 扫描项目并生成 .ai/ 初始 Harness 资产，包括 Guides、Sensors、Workflow Skills 和成熟度资产
3. 人类查看 scan-report、harness-config、.ai/skills、maturity-report
4. 输入一个小型 bugfix / feature 任务
5. Agent 生成 task-runs/<task-id>/harness-map.yaml
6. Agent 选择 Bugfix 或 Lightweight Workflow Skill
7. Agent 加载相关 Guides
8. Agent 运行必要 Sensors
9. Agent 输出 sensor-report、decision-log、handoff-summary
10. Agent 生成 experience-candidates / pending-improvements
11. 运行 assess / improve，更新成熟度评分和改进候选
```

### 3.3 基准测试代码库

首轮固定选择两个开源代码库作为基准测试集和硬性验证对象：

| 类型 | 基准仓库 | 价值 |
|---|---|---|
| Java / Spring Boot 企业项目 | RuoYi-Vue | 验证传统 B 端系统、多模块、后端 + 前端、SQL、配置和 Maven 识别 |
| .NET / ASP.NET Core 项目 | eShopOnWeb | 验证非 Java 技术栈、Clean Architecture、sln/csproj、测试项目和 CI 识别 |

这两个项目不是可选演示样本，而是 POC 的基础验收集。Harness Builder Agent 必须能分别为它们建立项目级 Harness，并保持统一的输出资产契约。

这两个仓库同时承担三类作用：

1. **功能验证样本**：验证 Agent 能否为不同技术栈生成 Harness。
2. **回归测试样本**：每次修改扫描、schema、命令识别或资产生成逻辑后，都应在两个仓库上重新跑关键流程。
3. **演示样本**：对外说明 Harness Builder 不是面向单一项目定制，而是具备跨企业技术栈迁移能力。

首轮不要上来就选特别大的金融系统或复杂内部项目。POC 的目标是证明双技术栈闭环，而不是证明能吞下任意规模代码库。

### 3.4 双技术栈支持要求

POC 必须同时支持 Java 和 .NET 两类技术栈，且不能通过为两个项目各写一套互不相干的脚本来完成。

要求如下：

- `project-inventory.json`、`command-catalog.yaml`、`harness-config.yaml` 的核心 schema 保持一致。
- Java 与 .NET 的差异进入 `stackExtensions`、模块化 Guide 或技术栈特定 Sensor 定义。
- Agent 可以识别 Maven / Spring Boot / Vue 相关资产。
- Agent 可以识别 `.sln` / `.csproj` / ASP.NET Core / EF Core / 测试项目相关资产。
- 两个代码库都必须生成 `.ai/` 资产、Harness Map、Sensor Report、Handoff Summary。
- 成功标准以两个项目都跑通为准，单项目跑通不算 POC 完成。

### 3.5 Codex 目标模式执行边界

本 POC 后续可以作为 Codex 目标模式的实施目标，但目标输入不应直接使用整份方案文档，而应使用一段明确的执行契约。

推荐目标输入如下：

```text
目标：在 /Users/anhui/Documents/myProgram/harness-builder 中从 0 到 1 实现 Harness Builder Agent POC。

完成标准：
1. 提供 Python CLI：harness-builder-agent init、harness-builder-agent run、harness-builder-agent assess、harness-builder-agent improve、harness-builder-agent benchmark。
2. init 能扫描 Java / Spring Boot / Vue 和 .NET / ASP.NET Core 项目，生成 .ai/project-inventory.json、.ai/command-catalog.yaml、.ai/harness-config.yaml、Guides、Sensors、Workflow Skills、maturity-report.md、maturity-score.yaml、evolution-plan.md。
3. 所有关键 JSON / YAML 输出必须经过 Pydantic schema 校验。
4. Workflow 正文必须以内置 Skill 模板形式生成到 .ai/skills/，不由 LLM 每次动态重写；harness-config.yaml 只作为机器可读索引和策略配置。
5. Guides 与 Sensors 必须基于扫描结果动态生成，并同时包含“当前项目事实”和“Harness Builder 推荐补齐项”；所有生成的 Markdown 默认使用中文。
6. run 能基于一个小任务生成 harness-map.yaml，选择 Bugfix 或 Lightweight Workflow Skill，执行至少一个低风险 Sensor，并输出 sensor-report.yaml、decision-log.md、handoff-summary.md、experience-candidates.md。
7. assess 能重新评估 .ai/ Harness 成熟度，输出 maturity-report.md 与 maturity-score.yaml；improve 能基于扫描结果、任务记录和 Sensor 结果输出 evolution-plan.md、pending-improvements.md 与 improvement-candidates.yaml。
8. benchmark 能对 Java 和 .NET 两类项目执行初始化、任务闭环、成熟度评估、改进建议和内容质量检查。无网络或基准仓库不可用时，必须至少在 mini Java fixture 和 mini .NET fixture 上完成等价验证。
9. pytest 通过，fixture init / run / assess / improve 流程通过，端到端测试通过，关键 golden output 检查通过。
10. 不做完整 IDE 集成、不做完整 Self-Improve 自动生效、不做复杂 Workflow Toolkit 动态组装、不强制完成真实业务代码修复。
11. 实施过程中必须小步提交，每完成一个可验证阶段或关键能力就提交一次，不允许把全部实现憋到最后一次性提交。
12. 测试默认不依赖真实 API key；真实 LLM / Agent 调用使用 DeepSeek，并通过环境变量显式启用。
```

目标模式中的“完成 POC”以自动化验收通过为准，而不是以自然语言报告完成为准。

### 3.6 工程落地位置

首轮 POC 工程落地到现有 GitHub 仓库对应的本地目录：

```text
/Users/anhui/Documents/myProgram/harness-builder
```

该仓库作为 Harness Builder Agent 的代码主仓库使用。旧版 Skill 尝试和历史草稿不再作为实现基础；可以保留 Git 仓库和远端配置，但工作区内容以本 POC 的新工程结构为准。

### 3.7 真实任务边界

首轮 POC 的任务闭环目标是验证 Harness Builder 能否生成并执行“控制闭环”，不强制要求完成真实业务代码修复。

任务闭环必须做到：

- 根据任务描述生成 Harness Map。
- 选择 Bugfix 或 Lightweight Workflow Skill。
- 加载相关 Guides。
- 尝试执行至少一个低风险 Sensor。
- 即使 Sensor 失败，也输出结构化失败摘要。
- 输出 Decision Log、Handoff Summary 和经验候选。

任务闭环可以暂不做到：

- 自动定位并修复真实业务 bug。
- 自动生成完整补丁并保证业务测试通过。
- 对高风险任务进行无人值守执行。

这一区分可以避免 POC 被“真实修 bug”拖大。真实代码修改能力可以作为下一阶段 MVP 增强目标。

### 3.8 离线最低验收与真实仓库 E2E 验收

为了降低目标模式执行过程中的外部依赖风险，验收分成两档：

| 验收档位 | 目标 | 说明 |
|---|---|---|
| 离线最低验收 | mini Java fixture + mini .NET fixture 跑通 | 不依赖下载大型开源仓库，作为硬门禁 |
| 真实仓库 E2E 验收 | RuoYi-Vue + eShopOnWeb 跑通 | 当前本地 POC 必须执行，用于证明真实开源仓库链路 |

离线最低验收必须包含：

- Java fixture 可以生成 `.ai/` 资产。
- .NET fixture 可以生成 `.ai/` 资产。
- 两者输出 schema 保持一致。
- 两者都能生成 Harness Map 和任务级交付资产。
- 所有关键输出通过 schema 校验。

真实仓库 E2E 验收必须包含：

- 自动或半自动获取 RuoYi-Vue 和 eShopOnWeb。
- 在两个真实开源仓库上运行 `init`、`run`、`assess`、`improve` 和 `benchmark`。
- 校验两个仓库的 `.ai/project-inventory.json`、`.ai/command-catalog.yaml`、`.ai/harness-config.yaml` 和 `.ai/benchmark-report.yaml`。
- 校验两个仓库都生成 `.ai/skills/<workflow>/SKILL.md`，并且 `harness-map.yaml` 能指向实际使用的 Workflow Skill。
- 校验两个仓库的 Guides / Sensors 不是空壳模板，必须包含扫描事实、证据来源、候选规则、推荐补齐项和人工确认点。
- 校验两个仓库都生成 `.ai/task-runs/demo-task-001/harness-map.yaml`、`sensor-report.yaml`、`decision-log.md`、`handoff-summary.md` 和 `experience-candidates.md`。
- 校验两个仓库都能执行 `assess` 和 `improve`，并输出成熟度结构化评分与改进候选。
- 记录无法执行的 Sensor 与原因，而不是让流程整体失败。

### 3.9 固定演示任务

首轮 POC 固定两类演示任务，用于避免每次演示时重新临场设计任务。

| 技术栈 | 仓库 / fixture | 演示任务 | 验证重点 |
|---|---|---|---|
| Java / Spring Boot / Vue | RuoYi-Vue，mini Java fixture 作为离线兜底 | 修复登录接口错误提示不一致的问题 | Bugfix Workflow、后端模块识别、测试 / build Sensor 候选 |
| .NET / ASP.NET Core | eShopOnWeb，mini .NET fixture 作为离线兜底 | 调整商品详情页或 Catalog 相关低风险文案 / 配置行为 | Lightweight Workflow、sln / csproj 识别、dotnet test Sensor 候选 |

如果真实仓库任务因环境缺失无法执行完整 Sensor，POC 仍应输出 Sensor 失败摘要和人工处理建议。

### 3.10 小步提交策略

目标模式执行过程中应保留清晰的 Git 历史，便于回溯、复盘和中途调整。

提交策略如下：

- 每完成一个可验证阶段就提交一次，例如工程骨架、schema、scanner、asset generation、run workflow、benchmark、fixtures、tests。
- 每次提交前尽量运行与该阶段相关的最小验证命令。
- 提交信息应说明完成的能力，而不是使用笼统描述。
- 不应把多个无关能力混在同一个提交里。
- 不应等到 POC 全部完成后才做第一次提交。

建议提交粒度：

```text
chore: scaffold python cli project
feat: add project inventory and command catalog schemas
feat: implement repository scanner for java and dotnet fixtures
feat: generate initial ai harness assets
feat: copy builtin workflow skills into generated harness
feat: generate richer guides and sensors
feat: add task run harness map and sensor report output
feat: add maturity assess command
feat: add improvement candidate generation
test: add fixture and golden output coverage
test: add end-to-end fixture workflow coverage
feat: add benchmark command for fixture and real repositories
test: enforce real repository content quality checks
```

### 3.11 DeepSeek API Key 与 LLM 执行配置

Harness Builder Agent 的 POC 应区分“确定性能力验证”和“真实 LLM 执行验证”。

默认规则：

- Scanner、schema 校验、资产写入、fixture 端到端测试和 benchmark 最低验收不应依赖真实 API key。
- 真实 Deep Agents / LLM 调用使用 DeepSeek，需要显式配置 API key。
- 默认支持通过环境变量读取 API key，例如 `DEEPSEEK_API_KEY`。
- 默认 DeepSeek base URL 为 `https://api.deepseek.com`，但应允许通过环境变量覆盖。
- 默认模型建议使用 `deepseek-v4-pro`；需要降低成本或加快 smoke test 时可切换到 `deepseek-v4-flash`。
- API key 不写入仓库、不写入 `.ai/` 产物、不写入日志和测试快照。
- 如果用户选择真实 LLM 模式但没有提供 API key，CLI 应给出明确错误信息和设置方式，而不是静默失败。
- 自动化测试应使用 fake / mock / deterministic LLM adapter，保证本地和 CI 环境可重复运行。
- 若本地需要保存 key，只能放在未纳入版本控制的本地环境文件或 shell 环境中，例如 `.env.local`，并确保 `.gitignore` 覆盖。

建议配置方式：

```bash
export DEEPSEEK_API_KEY="..."
export HARNESS_BUILDER_LLM_PROVIDER="deepseek"
export HARNESS_BUILDER_LLM_BASE_URL="https://api.deepseek.com"
export HARNESS_BUILDER_LLM_MODEL="deepseek-v4-pro"
```

测试中的真实 LLM 端到端验证应作为本地真实 Agent 能力 smoke test。只要本地环境或仓库 `.env` 中存在 `DEEPSEEK_API_KEY`，该测试就应执行；只有在完全没有 API key 的环境中才允许自动跳过。

```bash
pytest tests/e2e/test_real_llm_smoke.py
```

如果没有设置 `DEEPSEEK_API_KEY`，且仓库本地 `.env` 也没有该配置，真实 LLM smoke test 应自动跳过，不影响没有密钥的 CI 环境；但在当前本地 POC 环境中已经提供 DeepSeek API key，因此目标模式验收时不应跳过该测试。

### 3.12 当前第一版产物复盘与增强基线

基于当前已在 RuoYi-Vue 和 eShopOnWeb 上生成的 `.ai/` 产物，可以确认第一版实现已经证明了最小链路：

- `init` 能生成 `.ai/` 目录和基础资产。
- `run` 能生成任务级 `harness-map.yaml`、`sensor-report.yaml`、`decision-log.md`、`handoff-summary.md`。
- `benchmark` 能检查关键文件存在、schema 校验和技术栈匹配。
- 两个真实开源仓库都能完成基础流程。

但这些结果只能证明“链路跑通”，不能证明 Harness 内容质量已经达到 POC 最终标准。下一轮目标模式必须补齐以下差距：

| 模块 | 当前差距 | 增强要求 |
|---|---|---|
| Guides | 内容偏通用模板，项目规则、模块差异和推荐项不足 | 生成中文、项目特定、证据驱动的 Guides，并区分扫描事实与推荐补齐项 |
| Sensors | 主要是命令列表，缺少 gate 策略、失败处理和缺失项推荐 | 生成中文 Sensor 说明，包含 hard gate / soft signal / human escalation、失败处理和推荐补齐 |
| Workflow | 只有 YAML stages，没有项目级 Skill 载体 | 从 Agent 内置模板复制 `.ai/skills/<workflow>/SKILL.md`，并由 harness-map 指向实际 Skill |
| Maturity | 静态报告，缺少结构化评分和证据 | 新增 `assess` 命令，输出 `maturity-score.yaml` 和中文报告 |
| Evolution | 静态建议，缺少基于任务历史的候选项 | 新增 `improve` 命令，输出 `improvement-candidates.yaml` 和 pending improvements |
| Benchmark | 主要检查文件存在 | 升级为内容质量检查，覆盖 Skills、Guides、Sensors、Maturity、Evolution |

因此，后续目标模式不能把“文件存在 + schema 通过”视为完成。完成标准必须包含内容结构、中文可审查性、Workflow Skill 载体和真实仓库差异化输出。

---

## 4. POC 功能范围

POC 应覆盖完整方案的六大模块，但每个模块只做最小可验证版本。

### 4.1 Scanner & Analyzer：扫描与识别

#### 必须做

- 识别项目技术栈。
- 识别顶层目录结构。
- 识别模块、子项目、前后端边界。
- 识别构建文件，例如 `pom.xml`、`build.gradle`、`package.json`、`.sln`、`.csproj`。
- 识别测试资产，例如 `test` 目录、测试项目、测试命令候选。
- 识别配置文件，例如 `application.yml`、`appsettings.json`、`.env.example`、Docker / Compose 配置。
- 识别 CI 文件，例如 GitHub Actions、GitLab CI、Jenkinsfile。
- 识别已有文档，例如 README、docs、CONTRIBUTING、架构说明。
- 识别浅层代码结构，例如 Controller、Service、Repository、Entity、Test、前端页面和组件目录。

#### 低成本增强

- 提取 API 路由候选。
- 提取数据库表名或 migration 候选。
- 提取测试项目与生产项目的粗略对应关系。
- 标记低置信度、高影响的人工校准点。

#### 输出资产

```text
.ai/
  scan-report.md
  project-inventory.json
  command-catalog.yaml
```

---

### 4.2 Guides：项目知识与前置约束

#### 必须做

基于扫描结果生成最小 Guides 集合：

```text
.ai/guides/
  project-context.md
  coding-rules.md
  architecture.md
  task-templates/
    bugfix.md
    lightweight-feature.md
```

#### 内容要求

所有生成的 Markdown Guide 默认使用中文。每个 Guide 不能只是静态模板，必须至少包含两类内容：

1. **当前项目事实**：基于扫描结果、文件路径、配置、命令、目录结构和已有文档提炼出的项目现状。
2. **Harness Builder 推荐补齐项**：基于技术栈、项目类型和成熟度模型给出的候选规则、风险提示和后续补齐建议。

每个 Guide 应尽量包含：

- 适用范围。
- 来源证据。
- 置信度。
- 人工确认状态。
- 不确定点。
- 已确认事实、候选判断和推荐项的区分。
- 与任务类型、Workflow Skill 或 Sensor 的关联。

首轮 POC 中，至少需要让不同技术栈生成明显不同的 Guide 内容：

| 技术栈 | Guide 内容最低要求 |
|---|---|
| Java / Spring Boot / Vue | 识别 Maven 多模块、后端分层、前端目录、配置文件、登录 / 权限 / SQL 等风险候选 |
| .NET / ASP.NET Core | 识别 solution / project 结构、Clean Architecture 线索、测试项目、appsettings、PublicApi / Web / Infrastructure 等模块角色 |

示例元数据：

```yaml
---
asset_type: guide
status: candidate
source: inferred_from_codebase
confidence: medium
needs_human_confirmation: true
---
```

#### POC 边界

POC 中 Guides 可以是候选态，不要求全部自动变成正式规则。但候选态不等于空壳模板；必须能让人类维护者看出 Agent 的判断来源、项目差异和推荐理由。

---

### 4.3 Sensors：验证与反馈

#### 必须做

生成最小 Sensor 定义，覆盖：

- build。
- test。
- lint。
- typecheck。

若项目没有对应命令，则标记为缺口，而不是编造命令。

Sensor 文档默认使用中文。Sensor 资产也必须同时包含两类内容：

1. **当前已有验证能力**：从 `pom.xml`、`package.json`、`.sln`、`.csproj`、CI 文件等证据中识别出的可执行命令。
2. **推荐补齐验证能力**：基于技术栈和项目风险推荐但当前未发现的验证活动，例如 lint、typecheck、API contract test、安全扫描、架构约束检查。

每个 Sensor 候选至少需要包含：

- sensor id。
- 命令或人工执行说明。
- gate 类型：hard gate / soft signal / human escalation。
- 适用任务类型。
- 来源证据。
- 置信度。
- verified 状态。
- timeout 或跳过条件。
- 失败时应加载的 Guide 或人工处理建议。

#### 输出资产

```text
.ai/sensors/
  verification.md
  test-strategy.md
```

以及结构化配置：

```yaml
sensors:
  build:
    gate: hard
    type: computational
    run: mvn clean package
    confidence: medium
    source: pom.xml
    verified: false

  unit_test:
    gate: hard
    type: computational
    run: mvn test
    confidence: medium
    source: pom.xml
    verified: false
```

#### POC 中的 Sensor 执行要求

POC 至少应尝试运行一个低风险 Sensor，例如：

- `mvn test`
- `npm test`
- `dotnet test`
- `pnpm test`

如果命令失败，不要求 Agent 自动修复所有问题，但必须输出结构化失败摘要。若本地缺少 `mvn`、`dotnet`、Node 包管理器或外部依赖，应标记为 `skipped` 或 `failed`，并说明原因、影响和人工下一步。

---

### 4.4 Workflow Runtime Specification：工作流执行规范

#### 必须做

POC 不做完整 Workflow Toolkit 动态组装，但必须生成可读、可编辑、可被 Agent Runtime 消费的项目级 Workflow Skills。

首轮保留两个核心流程：

| Workflow | 适用场景 |
|---|---|
| Lightweight Workflow | 低风险、小范围 feature 或文档/配置调整 |
| Bugfix Workflow | 有明确错误现象、可复现或可定位的小型修复任务 |

Workflow 正文不应由 LLM 每次动态生成。Harness Builder Agent 应在自身工程中内置稳定的 Skill 模板，`init` 时复制到目标项目：

```text
src/harness_builder_agent/templates/skills/
  lightweight/SKILL.md
  bugfix/SKILL.md
```

目标项目输出：

```text
.ai/skills/
  lightweight/SKILL.md
  bugfix/SKILL.md
```

Skill 模板默认使用中文，且允许用户在目标项目中直接修改。这样可以保证 Workflow 稳定、可审查、可定制，也避免大模型每次重新生成导致内容漂移。

#### Lightweight Workflow 的 POC 要求

Lightweight Workflow 不是一个单独环节，也不是简单任务模板。它应作为完整的低风险开发 Workflow Skill，至少覆盖：

- 需求复述与范围收敛。
- 影响面识别。
- Harness Mapping。
- 必读 Guides 加载。
- 小步实现或建议输出。
- Sensor 选择与执行。
- 失败摘要与一次有限修复尝试策略。
- Decision Log、Handoff Summary 和 Experience Candidate 输出。

#### Bugfix Workflow 的 POC 要求

Bugfix Workflow 可以是更聚焦的 Workflow Skill，至少覆盖：

- 错误现象复述。
- 复现线索与影响范围判断。
- 根因定位假设。
- 最小修复策略。
- 回归测试或 targeted Sensor 选择。
- Sensor 失败后的摘要和人工升级条件。
- 交接与经验候选。

#### 不做

- 不做完整 Standard Workflow。
- 不做 Prototype-first Workflow。
- 不做复杂可组合 Workflow Toolkit。
- 不做 LLM 动态生成或动态拼装 Workflow Skill 正文。
- 不做 UI 流程预览。

#### 输出资产

```text
.ai/harness-config.yaml
.ai/skills/lightweight/SKILL.md
.ai/skills/bugfix/SKILL.md
.ai/task-runs/<task-id>/harness-map.yaml
```

`harness-config.yaml` 的定位是机器可读索引和策略配置，不是 Workflow 正文本身。真正可读、可编辑、可执行的 Workflow 载体是 `.ai/skills/<workflow>/SKILL.md`。

#### `harness-config.yaml` 最小字段

```yaml
version: 1

runtime:
  default_workflow: lightweight
  allow_workflow_upgrade: true
  require_user_confirmation_for_high_risk: true

workflows:
  lightweight:
    skill_path: .ai/skills/lightweight/SKILL.md
    stages:
      - requirement_brief
      - harness_mapping
      - implementation_or_advice
      - sensor_check
      - handoff

  bugfix:
    skill_path: .ai/skills/bugfix/SKILL.md
    stages:
      - observe
      - root_cause_investigation
      - harness_mapping
      - minimal_fix_or_advice
      - targeted_sensors
      - handoff

sensors:
  max_repair_attempts: 1
  rerun_failed_only: true
```

---

### 4.5 Harness Mapping：任务级控制计划

#### 必须做

给定一个任务描述，Agent 生成：

```text
.ai/task-runs/<task-id>/harness-map.yaml
```

最小字段包括：

```yaml
harness_map:
  task_id: demo-bugfix-001
  task_type: bugfix
  selected_workflow: bugfix
  risk_level: low
  confidence:
    requirement_clarity: medium
    code_mapping: medium
    sensor_coverage: medium

  relevant_modules:
    - src/example/**

  guide_policy:
    required:
      - .ai/guides/project-context.md
      - .ai/guides/architecture.md
      - .ai/guides/task-templates/bugfix.md

  workflow_skill:
    path: .ai/skills/bugfix/SKILL.md
    source: builtin_template
    editable_by_user: true

  sensor_policy:
    hard_gates:
      - unit_test
    soft_signals:
      - build

  human_confirmation:
    required: false
    reasons: []
```

#### POC 边界

Harness Mapping 可以由 LLM 参与生成，但必须引用扫描事实、Guide、Sensor 配置和 Workflow Skill；不能凭空判断风险区域。若 selected_workflow 为 `bugfix` 或 `lightweight`，`harness-map.yaml` 必须指向实际存在的 `.ai/skills/<workflow>/SKILL.md`。

---

### 4.6 Experience & Self-Improve：经验候选

#### 必须做

任务结束后生成：

```text
.ai/experience/
  pending-improvements.md
```

内容包括：

- 本次任务中哪些 Guide 有用。
- 哪些 Sensor 失败或缺失。
- 是否暴露出新的规则候选。
- 是否需要人工确认。

#### POC 边界

经验只进入候选区，不自动修改正式 Guides / Sensors / Workflow。

---

### 4.7 Maturity & Evolution：成熟度与演进建议

#### 必须做

`init` 阶段必须生成第一版成熟度与演进资产：

```text
.ai/maturity-report.md
.ai/maturity-score.yaml
.ai/evolution-plan.md
```

成熟度报告至少覆盖：

- Guides 成熟度。
- Sensors 成熟度。
- Workflow 成熟度。
- Risk Control 成熟度。
- Observability 成熟度。
- Experience 成熟度。

同时需要提供两个独立命令，用于在初始化后或任务运行后重新触发评估：

```bash
harness-builder-agent assess --repo <repo>
harness-builder-agent improve --repo <repo>
```

#### `assess` 命令要求

`assess` 负责重新评估当前 `.ai/` Harness 成熟度。它应读取：

- `.ai/project-inventory.json`
- `.ai/command-catalog.yaml`
- `.ai/harness-config.yaml`
- `.ai/skills/`
- `.ai/guides/`
- `.ai/sensors/`
- `.ai/task-runs/*/sensor-report.yaml`
- `.ai/task-runs/*/decision-log.md`

输出：

```text
.ai/maturity-report.md
.ai/maturity-score.yaml
```

`maturity-score.yaml` 至少包含：

- overall_level。
- dimension_scores。
- evidence。
- blocking_reasons。
- recommended_next_steps。
- last_assessed_at。

#### `improve` 命令要求

`improve` 负责基于扫描结果、成熟度评分、任务历史和 Sensor 结果生成可审查的改进候选。它不自动修改正式 Guides / Sensors / Workflow。

输出：

```text
.ai/evolution-plan.md
.ai/experience/pending-improvements.md
.ai/improvement-candidates.yaml
```

`improvement-candidates.yaml` 至少包含：

- candidate id。
- candidate type：guide_update / sensor_update / workflow_policy_update / maturity_action。
- suggested target。
- rationale。
- evidence。
- confidence。
- human_confirmation_required。
- priority。

#### 内容要求

成熟度和演进产物不能只是固定模板。至少需要解释：

- 当前项目为什么是这个等级。
- 哪些证据支撑该等级。
- 哪些缺口阻止它进入下一等级。
- 下一步改进项的收益、成本和优先级。
- 哪些改进可以自动生成候选，哪些必须人工确认。

#### 输出示例

```yaml
maturity:
  overall_level: L1
  dimension_scores:
    guides: L1
    sensors: L2
    workflow: L1
    risk_control: L0
    observability: L1
    experience: L0
  blocking_reasons:
    - risk zones 尚未经过人工确认
    - Sensors 尚未绑定完整 repair loop
  recommended_next_steps:
    - 确认核心风险目录
    - 将 unit test 设置为 hard gate
    - 补充 bugfix guide
```

---

## 5. POC 明确排除范围

为了避免 POC 膨胀，以下内容明确不做。

### 5.1 不做完整产品平台

- 不做 Web UI。
- 不做 Dashboard。
- 不做组织级管理后台。
- 不做团队权限系统。

### 5.2 不做完整 AI Coding IDE 集成

- 不做 IDE 插件。
- 不做 Cursor / Claude Code / InfCode 深度集成。
- 不做完整 MCP server。

POC 可以保留未来 MCP 化的接口设计，但不作为首轮交付目标。

### 5.3 不做高风险自动决策

- 不自动判断业务高风险模块。
- 不自动生成 restricted paths 并强制生效。
- 不自动修改安全、权限、金额、数据迁移相关规则。

这些内容只生成候选项，必须人工确认。

### 5.4 不做完整 Self-Improve

- 不跨项目学习。
- 不自动把经验写入正式规则。
- 不做组织级 Pattern Library。
- 不做长期趋势 Dashboard。

### 5.5 不做复杂 Workflow Toolkit

- 不做 Standard Workflow 全流程。
- 不做 Prototype Preview。
- 不做可视化 Workflow 编排。
- 不做多 Workflow 动态拼装。

---

## 6. 推荐技术方案

### 6.1 短期 POC 技术栈

```text
Language: Python
Agent Harness: LangChain Deep Agents
Workflow Runtime: LangGraph 底层能力
CLI: Typer / Click
Schema: Pydantic
Output: Markdown + YAML + JSON
Execution: Local filesystem + local shell backend
LLM Config: DeepSeek 环境变量 + fake / mock adapter for tests
```

### 6.2 为什么用 Python + Deep Agents

本 POC 的重点是验证真实 Agent 闭环：从代码库初始化，到 Harness 资产生成，再到一次任务级控制流程。

Deep Agents 提供：

- 内置 planning / todo。
- 内置文件系统读写。
- 内置 glob / grep。
- 支持 shell 执行。
- 支持 subagents。
- 基于 LangGraph，可继续演进到显式工作流。

因此它适合 1-2 周内快速证明：Harness Builder Agent 是否能完成初始化、生成资产和任务级控制闭环。

### 6.3 技术风险

| 风险 | 说明 | 缓解 |
|---|---|---|
| Deep Agents 版本仍偏新 | Python 包仍处于 Beta，API 可能变化 | 锁定版本，不使用高级实验特性 |
| ReAct 循环不可控 | Agent 可能自由探索，偏离确定流程 | 核心阶段写成明确工具函数，Agent 只做编排 |
| LangChain 依赖链较重 | 后续产品化可能有框架锁定 | 保持工具函数和 schema 独立，保留迁移到 LangGraph / 自定义管线的路径 |
| 结构化输出不稳定 | LLM 输出可能不符合 schema | 所有关键 YAML / JSON 必须经过 Pydantic 校验 |
| DeepSeek API key 配置不清 | 真实 LLM 调用无法执行或泄露密钥 | 从 `DEEPSEEK_API_KEY` 读取，测试默认 mock，日志和产物禁止输出密钥 |

### 6.4 长期演进方向

如果 POC 成功，建议演进为：

```text
Deep Agents 快速 POC
→ LangGraph 显式工作流
→ 核心扫描 / 生成 / 校验能力沉淀为确定性工具库
→ CLI / MCP / IDE Plugin 多入口复用
```

### 6.5 Harness Builder 自身的工程 Harness

开发 Harness Builder Agent 时，应把它自身也当作一个需要 Harness 约束的工程系统。也就是说，POC 不只要给目标 Java / .NET 项目生成 Harness，Harness Builder 自己的确定性脚本、schema、工具函数和 Agent 编排逻辑也要有清晰架构、规则规范和自动化验证。

#### 自身架构原则

Harness Builder Agent 工程至少分成四层：

| 层级 | 职责 | 约束 |
|---|---|---|
| Agent Orchestration | Deep Agents 编排、任务阶段控制、调用工具 | 尽量只做编排，不直接写复杂业务逻辑 |
| Deterministic Tools | 文件扫描、命令识别、schema 生成、Sensor 执行 | 必须可单元测试，不依赖 LLM 输出 |
| Schemas & Contracts | Pydantic 模型、YAML / JSON 契约、版本字段 | 所有关键输出必须经过 schema 校验 |
| Report / Evaluation | Markdown 报告、成熟度说明、经验候选、LLM 评价 | 只能解释结构化事实，不直接制造事实源 |

#### 确定性脚本规范

所有 `tools/` 下的确定性脚本应遵循以下规则：

- 输入、输出必须显式定义，优先使用 Pydantic model。
- 不在工具函数内部直接调用大模型。
- 不把自然语言报告作为后续执行依据。
- 不凭空生成命令；命令必须有来源，例如 `pom.xml`、`package.json`、`.csproj`、CI 文件或明确规则。
- 所有推断性字段必须包含 `confidence`、`source` 或 `evidence`。
- 文件系统扫描必须遵守忽略规则，例如 `.git`、`node_modules`、`target`、`bin`、`obj`、`dist`、`build`。
- 写入 `.ai/` 前必须先通过 schema 校验。

#### 自动化测试要求

POC 阶段至少需要四类测试：

| 测试类型 | 目标 | 示例 |
|---|---|---|
| Unit Test | 验证单个确定性工具函数 | Maven / `.csproj` / `package.json` 命令提取 |
| Fixture Test | 用小型样例项目验证扫描结果 | mini Spring Boot fixture、mini ASP.NET fixture |
| Golden Output Test | 验证 `.ai/` 输出结构稳定 | 对比 `project-inventory.json`、`command-catalog.yaml`、`harness-config.yaml` 的关键字段 |
| End-to-End Test | 验证 CLI 从输入仓库到 `.ai/` 产物、任务闭环、成熟度评估和改进候选的完整链路 | 在临时目录复制 fixture，运行 `init`、`run`、`assess`、`improve`、`benchmark`，校验关键输出和 schema |

建议测试目录：

```text
tests/
  unit/
    test_scan_repo.py
    test_detect_commands.py
    test_schema_validation.py
  fixtures/
    mini-spring-boot/
    mini-dotnet-webapi/
  golden/
    ruoyi-vue/
    eshop-on-web/
  integration/
    test_init_on_fixture_projects.py
    test_harness_map_generation.py
  e2e/
    test_fixture_end_to_end.py
    test_real_llm_smoke.py
```

端到端测试要求：

- E2E 测试必须从 CLI 入口运行，而不是只调用内部函数。
- E2E 测试必须在临时目录中复制 fixture，避免污染源 fixture。
- E2E 测试必须覆盖 `init`、`run`、`assess`、`improve` 和 `benchmark` 的最小链路。
- E2E 测试必须校验 `.ai/` 关键文件存在、JSON / YAML schema 通过、任务级报告生成。
- 默认 E2E 测试使用 fake / mock / deterministic LLM adapter，不依赖真实 API key。
- 真实 LLM smoke test 使用 DeepSeek；当环境变量或仓库 `.env` 存在 `DEEPSEEK_API_KEY` 时必须执行，只有完全没有 key 时才跳过。
- 真实仓库 E2E 测试必须覆盖 RuoYi-Vue 和 eShopOnWeb。测试可以使用本地 ignored 目录 `.benchmarks/RuoYi-Vue` 和 `.benchmarks/eShopOnWeb`，但不得把开源仓库内容提交进 Harness Builder 仓库。
- 真实仓库 E2E 必须运行 `init`、`run`、`assess`、`improve` 和 `benchmark`，并校验两个仓库的 benchmark report 状态通过、任务级 `task-runs/demo-task-001` 产物完整、Workflow Skill 存在和内容质量检查通过。

#### 双技术栈回归测试

针对 RuoYi-Vue 和 eShopOnWeb，应建立回归测试或半自动验证脚本，至少验证：

- 两个项目都能完成初始化扫描。
- 两个项目都能生成统一结构的 `.ai/` 资产。
- Java / .NET 技术栈差异进入扩展字段或技术栈特定 Guide / Sensor。
- 输出文件通过 schema 校验。
- Agent 不因缺少某个命令或依赖环境而中断整个流程。

建议提供一个显式的基准测试入口：

```bash
harness-builder-agent benchmark --repo .benchmarks/RuoYi-Vue --profile java-spring
harness-builder-agent benchmark --repo .benchmarks/eShopOnWeb --profile dotnet-aspnet
```

该命令可以先作为半自动脚本存在，不要求首轮实现成完整产品命令。它的目标是固定验证流程和输出检查项，避免每次演示都依赖人工临场判断。

#### 大模型验证要求

大模型验证不作为首轮硬门禁，但应作为后续增强方向预留。

可选验证包括：

- 让 LLM 审查 `scan-report.md` 是否忠实于 JSON / YAML 事实源。
- 让 LLM 判断生成的 Guides 是否有明显幻觉或越权推断。
- 让 LLM 评价 Harness Map 是否引用了正确的 Guides / Sensors。
- 让 LLM 对比 Java / .NET 两个项目输出，检查是否存在 schema 漂移。

大模型验证结果应作为 Soft Signal，不应在早期直接作为 Hard Gate。Hard Gate 仍以 schema 校验、单元测试、fixture 测试和 golden output 测试为主。

---

## 7. POC 交付物清单

### 7.1 Agent 工程交付物

```text
harness-builder-agent/
  pyproject.toml
  src/harness_builder_agent/
    cli.py
    agent.py
    tools/
      scan_repo.py
      generate_guides.py
      detect_sensors.py
      copy_workflow_skills.py
      run_sensor.py
      assess_maturity.py
      generate_improvements.py
      write_assets.py
    schemas/
      project_inventory.py
      command_catalog.py
      harness_config.py
      harness_map.py
      maturity_report.py
      improvement_candidate.py
    templates/
      skills/
        lightweight/
          SKILL.md
        bugfix/
          SKILL.md
    prompts/
      harness_builder_system.md
      guide_generator.md
      maturity_evaluator.md
    benchmarks/
      ruoyi-vue.yaml
      eshop-on-web.yaml
```

### 7.2 目标项目输出资产

```text
.ai/
  harness-config.yaml
  scan-report.md
  project-inventory.json
  command-catalog.yaml
  maturity-report.md
  maturity-score.yaml
  evolution-plan.md

  guides/
    project-context.md
    coding-rules.md
    architecture.md
    task-templates/
      bugfix.md
      lightweight-feature.md

  sensors/
    verification.md
    test-strategy.md

  skills/
    lightweight/
      SKILL.md
    bugfix/
      SKILL.md

  experience/
    pending-improvements.md

  improvement-candidates.yaml

  task-runs/
    demo-task-001/
      harness-map.yaml
      sensor-report.yaml
      decision-log.md
      handoff-summary.md
      experience-candidates.md
```

---

## 8. POC 分阶段计划

### Phase 0：方案冻结

目标：确认 POC 的交付边界为“初始化 + 一次任务闭环”。

产出：

- POC 范围文档。
- Codex 目标模式执行契约。
- 工程落地仓库确认：`/Users/anhui/Documents/myProgram/harness-builder`。
- 输出资产结构。
- 基准测试代码库固定为 RuoYi-Vue 和 eShopOnWeb。
- 离线 fixture 验收策略。
- 演示任务选择。

完成标准：

- 团队确认本计划中的范围、排除项、目标输入和成功标准。

---

### Phase 1：Agent 骨架与工具层

目标：搭建独立 Agent CLI，并完成确定性工具函数。

功能：

- `harness-builder-agent init`。
- `harness-builder-agent assess`。
- `harness-builder-agent improve`。
- 本地文件扫描。
- 构建文件识别。
- 命令候选提取。
- 输出目录写入。
- Pydantic schema 校验。

完成标准：

- 可以在目标代码库生成 `.ai/project-inventory.json` 和 `.ai/command-catalog.yaml`。
- 所有关键输出通过 schema 校验。

---

### Phase 2：Harness 资产生成

目标：从扫描结果生成第一版项目级 Harness。

功能：

- 生成 `harness-config.yaml`。
- 从内置模板复制 Workflow Skills 到 `.ai/skills/`。
- 生成中文 Guides，区分扫描事实与推荐补齐项。
- 生成中文 Sensors，区分已有验证能力、缺失项和推荐验证活动。
- 生成 `scan-report.md`。
- 生成 `maturity-report.md`。
- 生成 `maturity-score.yaml`。
- 生成 `evolution-plan.md`。

完成标准：

- 人类可以审查 `.ai/` 资产并理解 Agent 的判断来源。
- 所有执行相关内容都有结构化表达。
- 不确定判断被标记为人工确认点。
- `.ai/skills/lightweight/SKILL.md` 与 `.ai/skills/bugfix/SKILL.md` 存在，内容来自 Agent 内置模板，且默认中文。
- Guides / Sensors 不能只是通用模板，必须体现 Java 与 .NET 真实仓库差异。

---

### Phase 3：任务级 Harness Mapping

目标：输入一个小任务，生成任务级控制计划。

功能：

- `harness-builder-agent run "<task>"`。
- 判断任务类型。
- 判断风险等级。
- 选择 Bugfix / Lightweight Workflow。
- 选择需要加载的 Guides。
- 选择需要执行的 Sensors。
- 输出 `task-runs/<task-id>/harness-map.yaml`。

完成标准：

- Harness Map 能解释为什么选择某个 Workflow。
- Harness Map 能引用已有 Guides、Sensors 和实际存在的 Workflow Skill。
- 高风险或低置信度判断进入人工确认。

---

### Phase 4：一次受控任务闭环演示

目标：用一个低风险任务跑通最小闭环。

功能：

- 加载任务相关 Guides。
- 执行一个目标 Sensor。
- 解析 Sensor 结果。
- 输出 `sensor-report.yaml`。
- 输出 `decision-log.md`。
- 输出 `handoff-summary.md`。
- 输出 `experience-candidates.md`。
- 可在任务后运行 `assess` 重新评估成熟度。
- 可在任务后运行 `improve` 生成改进候选。

完成标准：

- 即使 Sensor 失败，也能输出可行动的失败摘要。
- Handoff Summary 能说明任务做了什么、验证了什么、还有什么风险。
- Experience Candidate 不自动生效，只进入待审查状态。
- `assess` 能基于任务记录更新成熟度报告。
- `improve` 能基于任务记录和 Sensor 结果生成待确认改进候选。

---

### Phase 5：双开源仓库基准复验

目标：证明 Harness Builder Agent 能同时为 Java / Spring Boot 与 .NET / ASP.NET Core 两类开源代码库建立 Harness。

验证方式：

- 在 RuoYi-Vue 上完整跑一遍。
- 在 eShopOnWeb 上完整跑一遍。
- 对比两者输出结构是否一致、技术栈扩展是否不同。
- 用固定 benchmark 配置记录每个仓库的预期关键资产、Workflow Skill、命令候选、内容质量检查和最低验收项。

完成标准：

- 两个项目都能生成同样结构的 `.ai/` 资产。
- Java 与 .NET 的技术栈差异进入扩展字段或不同 Guide / Sensor，而不是破坏统一资产契约。
- 两个项目都能通过 POC 定义的 schema 校验和关键输出检查。
- 两个项目都能生成 `.ai/skills/`，并且 harness-map 指向实际 Workflow Skill。
- 两个项目的 Guides / Sensors / Maturity / Evolution 产物具备可审查内容，而不是只有文件存在。

---

## 9. 成功标准

POC 成功需要同时满足以下条件。

### 9.1 资产生成成功

- 能在真实代码库生成 `.ai/` 目录。
- 能生成结构化 `harness-config.yaml`。
- 能生成项目级 Workflow Skills。
- 能生成中文 Guides，且包含扫描事实、证据来源、候选规则和推荐补齐项。
- 能生成中文 Sensors，且包含已有命令、缺失项、推荐验证活动和失败处理策略。
- 能生成 Maturity Report、Maturity Score 和 Evolution Plan。

### 9.2 任务闭环成功

- 能输入一个小型任务并生成 Harness Map。
- 能选择 Bugfix 或 Lightweight Workflow Skill。
- 能加载相关 Guides。
- 能运行至少一个 Sensor。
- 能输出 Sensor Report、Decision Log、Handoff Summary。
- Harness Map 必须引用实际存在的 `.ai/skills/<workflow>/SKILL.md`。

### 9.3 可审查性成功

- Agent 的关键判断有来源证据。
- 低置信度判断有人工校准点。
- Markdown 报告不编造结构化事实源之外的关键判断。
- 生成的 Markdown 默认中文，方便 Harness Maintainer 直接审查和修改。
- Benchmark 不只检查文件存在，还要检查 Guides / Sensors / Skills / Maturity / Evolution 的最低内容结构。

### 9.4 可迁移性成功

- RuoYi-Vue 与 eShopOnWeb 两个基准仓库都可以跑通。
- 输出资产结构保持一致。
- 技术栈差异被隔离在扩展字段或模块化文件中。
- 任意一个基准仓库无法生成 Harness，都不算 POC 完成。
- RuoYi-Vue 与 eShopOnWeb 生成的 Guides / Sensors 应体现各自技术栈和项目结构差异。

### 9.5 Harness Builder 自身质量成功

- 确定性工具函数具备单元测试。
- 至少有 Java / .NET 两类 fixture 测试。
- 至少有一组端到端测试从 CLI 入口验证 `init`、`run`、`benchmark` 完整链路。
- 至少有一组端到端测试从 CLI 入口验证 `assess` 和 `improve`。
- 关键 `.ai/` 输出通过 Pydantic schema 校验。
- 至少有一组 golden output 检查，防止输出契约无意漂移。
- Agent 编排层与确定性工具层职责清晰，不把复杂扫描逻辑写进 prompt。
- 默认 fixture / benchmark 测试不依赖真实 API key；DeepSeek 真实 LLM smoke test 在本地有 key 时必须执行，无 key 的 CI 环境可自动跳过。

### 9.6 产品判断成功

POC 结束后，团队能判断：

- Harness Builder 是否值得从 POC 进入 MVP。
- Deep Agents 是否适合作为后续基座。
- 哪些能力需要下沉到 LangGraph 显式工作流。
- 哪些能力需要变成确定性工具库。

### 9.7 目标模式硬验收命令

目标模式完成时，至少需要提供并通过以下命令：

```bash
pytest
pytest tests/e2e
pytest tests/e2e/test_real_repositories_e2e.py
harness-builder-agent init --repo tests/fixtures/mini-spring-boot
harness-builder-agent init --repo tests/fixtures/mini-dotnet-webapi
harness-builder-agent run --repo tests/fixtures/mini-spring-boot "修复登录接口错误提示不一致的问题"
harness-builder-agent run --repo tests/fixtures/mini-dotnet-webapi "调整 Catalog 相关低风险文案"
harness-builder-agent assess --repo tests/fixtures/mini-spring-boot
harness-builder-agent assess --repo tests/fixtures/mini-dotnet-webapi
harness-builder-agent improve --repo tests/fixtures/mini-spring-boot
harness-builder-agent improve --repo tests/fixtures/mini-dotnet-webapi
harness-builder-agent benchmark --repo tests/fixtures/mini-spring-boot --profile java-spring
harness-builder-agent benchmark --repo tests/fixtures/mini-dotnet-webapi --profile dotnet-aspnet
harness-builder-agent init --repo .benchmarks/RuoYi-Vue
harness-builder-agent init --repo .benchmarks/eShopOnWeb
harness-builder-agent run --repo .benchmarks/RuoYi-Vue "修复登录接口错误提示不一致的问题"
harness-builder-agent run --repo .benchmarks/eShopOnWeb "调整 Catalog 相关低风险文案"
harness-builder-agent assess --repo .benchmarks/RuoYi-Vue
harness-builder-agent assess --repo .benchmarks/eShopOnWeb
harness-builder-agent improve --repo .benchmarks/RuoYi-Vue
harness-builder-agent improve --repo .benchmarks/eShopOnWeb
```

真实开源仓库 benchmark 验收命令为：

```bash
harness-builder-agent benchmark --repo .benchmarks/RuoYi-Vue --profile java-spring
harness-builder-agent benchmark --repo .benchmarks/eShopOnWeb --profile dotnet-aspnet
```

Benchmark 必须检查以下内容，而不仅是文件存在：

- `.ai/skills/lightweight/SKILL.md` 和 `.ai/skills/bugfix/SKILL.md` 存在且为中文。
- `.ai/harness-config.yaml` 中 Workflow 条目指向实际 Skill 文件。
- `.ai/task-runs/<task-id>/harness-map.yaml` 中的 selected workflow 指向实际 Skill 文件。
- Guides 包含项目事实、证据来源、候选规则、推荐补齐项和人工确认点。
- Sensors 包含已有验证命令、缺失验证能力、推荐验证活动、gate 类型和失败处理策略。
- `maturity-score.yaml` 与 `improvement-candidates.yaml` 通过 schema 校验。
- RuoYi-Vue 与 eShopOnWeb 的输出内容体现技术栈差异，而不是同一套空壳模板。

如果真实仓库因为依赖、网络、数据库或 SDK 环境不完整导致 Sensor 失败，仍可接受，但必须生成结构化 `sensor-report.yaml`，并在 `handoff-summary.md` 中说明失败原因、影响和人工下一步。

真实 LLM smoke test 为本地增强验收；当前本地仓库已配置 DeepSeek API key，因此目标模式验收时必须执行：

```bash
pytest tests/e2e/test_real_llm_smoke.py
```

该命令需要配置 `DEEPSEEK_API_KEY`，可来自 shell 环境或仓库本地 `.env`。如果在 CI 或其他环境未配置 API key，可自动跳过；但在已提供 key 的本地 POC 验收中不应跳过。

---

## 10. POC 风险与应对

| 风险 | 表现 | 应对 |
|---|---|---|
| Scope 膨胀 | 想把完整方案一次性做完 | 只做初始化 + 一次任务闭环 |
| Agent 自由度太高 | Agent 到处读文件、偏离流程 | 用明确工具和阶段约束控制 Agent |
| 输出不可验证 | LLM 生成漂亮报告但没有事实依据 | 关键资产必须结构化并通过 schema 校验 |
| 技术栈识别误判 | Java / .NET / 前端项目识别不准 | 输出置信度和人工校准点 |
| Sensor 命令失败 | 测试环境不完整或依赖缺失 | 失败也算有效结果，但要结构化解释 |
| Deep Agents 框架锁定 | 后续迁移困难 | 核心逻辑写成独立工具函数 |
| Harness Builder 自身不够健壮 | 确定性脚本缺少规范和测试，后续难维护 | 为工具函数、schema 和基准仓库输出建立自动化测试 |
| 缺少端到端测试 | 单元测试通过但 CLI 链路或输出资产不完整 | 将 fixture E2E 测试作为硬门禁 |
| DeepSeek API key 缺失或泄露 | 真实 LLM 执行失败，或密钥进入日志 / 产物 / 快照 | 默认 mock，真实 LLM 显式启用，密钥只从环境变量读取 |
| 演示代码库太复杂 | 第一轮无法稳定跑通 | 首轮用 RuoYi-Vue 和 eShopOnWeb，不选超大型项目 |

---

## 11. 建议的演示脚本

### 11.1 初始化演示

```bash
harness-builder-agent init --repo .benchmarks/RuoYi-Vue
```

展示：

- `.ai/project-inventory.json`
- `.ai/command-catalog.yaml`
- `.ai/harness-config.yaml`
- `.ai/skills/lightweight/SKILL.md`
- `.ai/skills/bugfix/SKILL.md`
- `.ai/guides/project-context.md`
- `.ai/maturity-report.md`

### 11.2 任务闭环演示

```bash
harness-builder-agent run --repo .benchmarks/RuoYi-Vue "修复登录接口错误提示不一致的问题"
```

展示：

- `.ai/task-runs/<task-id>/harness-map.yaml`
- `.ai/task-runs/<task-id>/sensor-report.yaml`
- `.ai/task-runs/<task-id>/decision-log.md`
- `.ai/task-runs/<task-id>/handoff-summary.md`
- `.ai/experience/pending-improvements.md`

### 11.3 成熟度与改进演示

```bash
harness-builder-agent assess --repo .benchmarks/RuoYi-Vue
harness-builder-agent improve --repo .benchmarks/RuoYi-Vue
```

展示：

- `.ai/maturity-score.yaml`
- `.ai/maturity-report.md`
- `.ai/improvement-candidates.yaml`
- `.ai/evolution-plan.md`
- `.ai/experience/pending-improvements.md`

---

## 12. 最终建议

本 POC 应以完整方案为基础，验证 **Harness Builder Agent 的最小产品闭环**。

推荐范围是：

```text
扫描真实代码库
→ 生成第一版项目级 Harness
→ 生成任务级 Harness Map
→ 跑通一次 Bugfix / Lightweight Workflow Skill
→ 输出验证报告、交接摘要和经验候选
→ 基于任务记录更新成熟度和改进候选
```

推荐技术路线是：

```text
Python + Deep Agents 快速验证 Agent 形态
核心扫描 / 生成 / 校验逻辑保持确定性工具化
关键输出全部 schema 化
POC 成功后逐步沉淀到 LangGraph 显式工作流或自定义确定性管线
```

一句话：

> **POC 要证明 Harness Builder 能把真实代码库初始化成可控 AI Coding 环境，并跑通一次受控任务闭环。**
