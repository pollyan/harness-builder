# Harness Builder Scanner Skill 需求文档

> 状态：需求设计稿  
> 日期：2026-05-25  
> 阶段：POC 第一阶段  
> 方法：Spec-first / Superpowers Brainstorm 产物  

---

## 1. 背景

Harness Builder 的长期目标，是为既有企业代码库生成一套项目级 AI Coding Harness，使 AI Coding Agent 能够在更明确的项目上下文、规则边界和验证约束下工作。

POC 第一阶段不直接建设完整 Harness Builder，也不做 Task Mapping、Workflow Runtime、Sensors 执行或 AI Coding 改码演示。本阶段只建设第一个可迁移 Skill：**Scanner Skill**。

Scanner Skill 的目标，是在当前工程根目录运行，扫描工程资产，并生成后续 Harness 生成、Task Mapping 和 Workflow 设计可使用的基础事实源。

---

## 2. 产品定位

Scanner Skill 是 Harness Builder Skill 体系中的第一块能力。

它负责回答：

```text
当前工程是什么？
它使用什么技术栈？
它有哪些模块、配置、构建方式、测试资产和文档资产？
后续 Skill 应该基于哪些事实继续工作？
```

它不负责回答：

```text
某个具体任务应该改哪些文件？
哪些路径属于高风险区域？
应该如何自动修改代码？
代码修改是否最终成功？
```

这些问题属于后续 Task Mapping Skill、Workflow Skill、Sensor Skill 或 Harness Generator 的范围。

---

## 3. 真实使用场景

未来使用场景是：

1. 用户在 AI 编程 IDE 或 AI Coding Agent 环境中打开一个代码工程。
2. 用户安装或加载 Harness Builder Scanner Skill。
3. 用户调用类似 `harness builder init` 或 `run scanner` 的能力。
4. Scanner Skill 默认以当前工作目录作为工程根目录。
5. Scanner Skill 在当前工程中生成 `.harness/`。
6. 用户或后续 Skill 基于 `.harness/` 继续生成 Guides、Sensors、Task Mapping 或 Workflow。

因此，Scanner Skill 的主要输入不是外部 repo URL，而是：

```text
当前工作目录 = 当前工程根目录
```

为了测试和自动化验证，可以支持显式 repo path，但这不是主要产品入口。

---

## 4. POC 目标

POC 第一阶段需要验证四件事：

1. **能否在真实工程根目录运行**  
   Scanner Skill 可以在 RuoYi-Vue 与 eShopOnWeb 的工程根目录运行，并生成统一结构的 `.harness/` 输出。

2. **能否生成机器可消费的事实源**  
   `project-inventory.json` 和 `command-catalog.yaml` 是主要事实源，后续 Skill 应优先读取它们。

3. **能否生成人类可审查的解释层**  
   `scanner-report.md` 用于解释扫描结果、人工校准点和后续 Skill 输入建议。

4. **能否跨技术栈复用**  
   同一套 Scanner Skill 能处理 Java/Spring Boot/Maven/Vue 项目和 .NET/ASP.NET Core 项目，证明它不是单项目定制脚本。

---

## 5. 首轮目标代码库

| 类型 | 代码库 | 技术栈 | 用途 |
|---|---|---|---|
| Java B 端项目 | RuoYi-Vue | Java / Spring Boot / Maven / Vue | 验证 Java 多模块、Spring 配置、SQL、前端 package 识别 |
| 非 Java B 端项目 | eShopOnWeb | .NET / ASP.NET Core / EF Core | 验证 sln/csproj、Clean Architecture、测试项目、CI 识别 |
| 第二轮复杂候选 | Apache Fineract | Java / Spring Boot / Gradle / PostgreSQL | 后续验证大型金融业务系统和复杂多模块场景 |

首轮只要求 RuoYi-Vue 与 eShopOnWeb 通过。Apache Fineract 不进入第一阶段完成标准。

---

## 6. 输出产物

Scanner Skill 在工程根目录生成：

```text
.harness/
  project-inventory.json
  command-catalog.yaml
  scanner-report.md
```

### 6.1 project-inventory.json

机器事实源，用于记录工程资产清单。

应包含：

- 仓库基本信息
- 技术栈识别结果
- 顶层目录结构
- 模块列表
- 构建文件
- 配置文件
- 测试资产
- CI / Docker 资产
- 文档资产
- 浅层代码结构
- 技术栈扩展字段
- 人工校准点

### 6.2 command-catalog.yaml

机器事实源，用于记录命令候选。

应包含：

- build 命令候选
- test 命令候选
- run 命令候选
- frontend 命令候选
- docker / compose 命令候选
- 命令来源
- 工作目录
- 置信度
- 是否已验证

### 6.3 scanner-report.md

人类解释层，用于说明：

- Scanner 识别到了什么
- 哪些事实来自哪些文件
- 哪些地方需要人工校准
- 当前输出能如何服务后续 Skill
- 当前 Scanner 存在哪些限制

---

## 7. 输出优先级原则

Scanner Skill 的输出以机器可消费为主，人类可审查为辅。

```text
project-inventory.json / command-catalog.yaml = 事实源
scanner-report.md = 解释层
```

规则：

1. 后续 Skill 优先读取 JSON/YAML。
2. Markdown 报告必须基于事实源生成。
3. Markdown 报告不能引入事实源之外的关键事实判断。
4. LLM 可以参与报告解释，但不能生成事实源。

---

## 8. 必须能力

Scanner Skill 首轮必须具备以下能力：

| 能力 | 说明 |
|---|---|
| 文件系统扫描 | 识别目录、文件类型、关键文件、文件数量 |
| 技术栈识别 | 识别 Maven、Gradle、dotnet、npm、Vue、Spring Boot、ASP.NET Core 等信号 |
| 模块识别 | 识别 Maven modules、Gradle modules、sln/csproj、前端项目 |
| 配置识别 | 识别 application.yml、appsettings.json、docker-compose、CI workflow 等 |
| 命令提取 | 提取 build/test/run/frontend/docker 命令候选 |
| 测试资产识别 | 识别 test 目录、测试项目、测试命令 |
| 文档资产识别 | 识别 README、CONTRIBUTING、docs 等 |
| 浅层代码结构识别 | 识别 Controller/API、Service、Entity/Model、Test、前端页面/组件目录 |

---

## 9. 低成本增强能力

以下能力可以在不显著增加复杂度时实现：

| 能力 | 说明 |
|---|---|
| API 路由提取 | 从注解、Controller、Endpoint 中提取路由候选 |
| 数据库表名提取 | 从 SQL、migration 或实体映射中提取表名候选 |
| 测试与生产代码关系 | 粗略识别测试项目与生产项目的对应关系 |

这些能力不是首轮完成的硬性条件，但可以提高 Scanner 输出对后续 Task Mapping Skill 的价值。

---

## 10. 明确不做

第一阶段不做以下内容：

| 不做项 | 原因 |
|---|---|
| Task Mapping | 后续独立 Skill，依赖 Scanner 输出 |
| Risk Zones | 需要业务风险判断，容易误判 |
| Restricted Paths | 需要权限和流程设计 |
| Human Escalation | 企业落地阶段再设计 |
| Experience & Self-Improve | 需要多轮任务数据 |
| Maturity Model | 更偏售前评估，不适合首轮 Scanner |
| 完整调用链 | 成本高，偏静态分析平台 |
| 深度业务流程推理 | LLM 猜测风险高，首轮不做 |
| AI Coding 执行 | 后续 Workflow / Task Mapping 阶段再做 |
| Web UI | 当前验证 Skill 能力，不验证产品界面 |

---

## 11. LLM 使用边界

Scanner 本体确定性优先，LLM 只做解释层和人工校准建议。

### 11.1 确定性脚本负责

- 文件扫描
- 技术栈识别
- 模块识别
- 命令提取
- 配置文件识别
- 测试资产识别
- 浅层代码结构识别
- JSON/YAML 事实源生成

### 11.2 LLM 可以负责

- `scanner-report.md` 的说明性总结
- 模块职责的初步描述
- 人工校准点提示
- 后续 Skill 输入建议

### 11.3 LLM 不负责

- 事实源生成
- 命令凭空编造
- 构建是否成功的最终判断
- 风险区域自动判断
- 业务流程推断
- Task Mapping 决策

---

## 12. 输出契约

Scanner 输出采用：

```text
统一 core schema + 技术栈扩展字段
```

### 12.1 Core Schema

所有技术栈必须输出：

```text
repo
structure
modules
buildFiles
configFiles
testAssets
documentation
commands
shallowCodeStructure
ciAssets
dockerAssets
manualCalibrationPoints
```

### 12.2 Stack Extensions

技术栈差异进入扩展字段：

```text
stackExtensions.java
stackExtensions.dotnet
stackExtensions.node
stackExtensions.gradle
```

原则：

1. 后续 Skill 优先读取 core schema。
2. 技术栈特定能力读取 stack extensions。
3. 不为了统一抹平技术栈差异。
4. 不允许不同技术栈各自发散成不可复用 schema。

---

## 13. 成功演示

第一阶段成功演示不包含 Task Mapping 和 AI Coding 执行。

演示流程：

1. 在 RuoYi-Vue 工程根目录调用 Scanner Skill。
2. 生成 `.harness/` 三个文件。
3. 打开 `project-inventory.json` 和 `command-catalog.yaml` 说明机器事实源。
4. 打开 `scanner-report.md` 说明人类解释层。
5. 在 eShopOnWeb 重复同一流程。
6. 对比两个技术栈下输出结构一致、扩展字段不同。
7. 说明这些输出如何成为后续 Task Mapping Skill / Harness Generator 的输入。

---

## 14. 验收标准

Scanner Skill 第一阶段完成标准：

1. 能在当前工程根目录运行。
2. 能对 RuoYi-Vue 生成 `.harness/`。
3. 能对 eShopOnWeb 生成 `.harness/`。
4. 两个项目都生成 `project-inventory.json`、`command-catalog.yaml`、`scanner-report.md`。
5. JSON/YAML 是主要事实源。
6. Markdown 报告不引入事实源之外的关键判断。
7. 两个技术栈共用同一 core schema。
8. 技术栈差异进入 stack extensions。
9. 输出能明确支撑下一阶段 Task Mapping Skill 的设计。
10. 不要求启动完整应用，不要求数据库或中间件可用。

---

## 15. 后续阶段

Scanner Skill 完成后，才进入下一轮 Brainstorm：

```text
Task Mapping Skill
```

Task Mapping Skill 将基于 `.harness/` 事实源和用户任务描述，回答：

```text
这个任务应该加载哪些上下文？
可能涉及哪些模块和文件？
应该运行哪些验证命令？
执行前需要哪些人工确认？
```

当前阶段只为它准备输入，不提前实现。
