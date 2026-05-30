# Harness Builder — POC 方案设计

> 文档状态：POC 方案修订稿  
> 目标用途：内部方案讨论、可行性验证、原型演示、资源争取  
> 当前阶段：只做 Scanner Skill，不做 Task Mapping Skill

---

## 1. POC 定位

Harness Builder POC 的第一阶段目标，是做出一个可迁移到 AI 编程 IDE 中使用的 **Scanner Skill**。

这个 Skill 安装到编程 IDE 或 AI Coding Agent 环境后，应能够在当前工程根目录运行，自动扫描工程资产，并生成后续 Harness 构建所需的基础事实源。

第一阶段不做完整 Harness Builder，不做 Task Mapping，不做 AI Coding 执行演示。当前只证明一件事：

```text
当前工程根目录 → Scanner Skill → .harness/ 基础事实源 → 人类可审查报告 → 后续 Skill 可消费输入
```

POC 成功的判断标准，是 Scanner Skill 能在两个不同企业技术栈项目中生成稳定、结构化、可审查、可被后续 Skill 使用的工程资产清单。

---

## 2. 为什么先只做 Scanner Skill

Task Mapping 应该是后续独立 Skill，而不是 Scanner 的一部分。

原因：

1. **职责不同**  
   Scanner 负责回答“当前工程是什么”。  
   Task Mapping 负责回答“某个任务应该怎么进入这个工程”。

2. **输入依赖不同**  
   Scanner 的输入是当前工程根目录。  
   Task Mapping 的输入是 `.harness/` 事实源 + 用户任务描述。

3. **验证节奏不同**  
   Scanner 可以通过双技术栈代码库稳定验证。  
   Task Mapping 需要先确认 Scanner 输出质量，否则会建立在不稳定事实源上。

4. **避免首轮范围膨胀**  
   如果同时做 Scanner、Task Mapping、Agent 执行和 Sensors 验证，POC 会快速接近 MVP，失去低成本验证意义。

因此，当前 POC 明确收敛为：

```text
第一阶段：Scanner Skill
第二阶段：Task Mapping Skill
第三阶段：Harness Generator / Workflow / Sensors
```

---

## 3. Scanner Skill 的真实使用场景

未来真实使用方式是：

```text
用户在 AI 编程 IDE 中打开一个工程
安装或加载 Harness Builder Scanner Skill
调用类似 harness builder init / run scanner 的能力
Skill 以当前工程根目录为目标进行扫描
在当前工程下生成 .harness/
```

因此，Scanner Skill 首轮默认输入不是外部 repo path，而是：

```text
当前工作目录 = 当前工程根目录
```

为了测试和自动化验证，可以保留 `--repo <path>` 参数，但这是测试入口，不是主要产品入口。

---

## 4. 第一阶段目标

Scanner Skill 第一阶段需要回答四个问题：

1. **能否识别当前工程的技术栈与工程结构**  
   例如 Java/Maven/Spring Boot、.NET/ASP.NET Core、前端项目、测试项目、配置文件、CI 文件等。

2. **能否生成机器可消费的事实源**  
   事实源包括 `project-inventory.json` 和 `command-catalog.yaml`。

3. **能否生成面向人类审查的扫描报告**  
   报告用于解释 Scanner 看到了什么、没看到什么、哪些地方需要人工校准。

4. **能否跨两个典型企业技术栈复用**  
   同一套 Scanner Skill 能处理 RuoYi-Vue 和 eShopOnWeb，证明不是单项目定制脚本。

---

## 5. 首轮目标代码库

| 类型 | 代码库 | 技术栈 | 作用 |
|---|---|---|---|
| Java B 端项目 | RuoYi-Vue | Java / Spring Boot / Maven / Vue | 验证 Java 多模块、Spring 配置、SQL、前端 package 识别 |
| 非 Java B 端项目 | eShopOnWeb | .NET / ASP.NET Core / EF Core | 验证 sln/csproj、Clean Architecture、测试项目、CI 识别 |
| 第二轮复杂候选 | Apache Fineract | Java / Spring Boot / Gradle / PostgreSQL | 后续验证大型金融业务系统和多模块压力场景 |

首轮只使用 **RuoYi-Vue + eShopOnWeb**。Apache Fineract 不进入第一阶段实现范围，只保留为后续复杂业务验证对象。

---

## 6. Scanner Skill 输出

Scanner Skill 在当前工程根目录生成：

```text
.harness/
  project-inventory.json
  command-catalog.yaml
  scanner-report.md
```

### 6.1 project-inventory.json

机器事实源，记录：

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

### 6.2 command-catalog.yaml

机器事实源，记录：

- build 命令候选
- test 命令候选
- run 命令候选
- frontend 命令候选
- docker / compose 命令候选
- 命令来源
- 置信度
- 是否已验证

### 6.3 scanner-report.md

人类解释层，记录：

- 项目概览
- 技术栈识别
- 模块结构
- 构建与测试命令
- 配置与数据库资产
- CI / Docker / 文档资产
- Scanner 输出可用于后续哪些 Skill
- 人工校准点

---

## 7. 输出优先级原则

首轮输出以机器可消费为主，人类可审查为辅：

```text
project-inventory.json / command-catalog.yaml = 事实源
scanner-report.md = 解释层
```

规则：

1. 后续 Skill 优先读取 JSON/YAML。
2. Markdown 报告必须从事实源生成或严格基于事实源解释。
3. 不允许在 Markdown 中编造 JSON/YAML 中不存在的事实。
4. LLM 可以参与报告解释，但不能生成事实源。

---

## 8. Scanner 能力边界

### 8.1 必须包含

| 能力 | 说明 |
|---|---|
| 文件系统扫描 | 目录、文件类型、关键文件、文件数量 |
| 技术栈识别 | Maven、Gradle、dotnet、npm、Vue、Spring Boot、ASP.NET Core |
| 模块识别 | Maven modules、Gradle modules、sln/csproj、前端项目 |
| 配置识别 | application.yml、appsettings.json、docker-compose、CI workflow |
| 命令提取 | build/test/run/frontend/docker 命令候选 |
| 测试资产识别 | test 目录、测试项目、测试命令 |
| 文档资产识别 | README、CONTRIBUTING、docs |
| 浅层代码结构 | Controller/API、Service、Entity/Model、Test、前端页面/组件目录 |

### 8.2 低成本增强

| 能力 | 说明 |
|---|---|
| API 路由提取 | 从注解、Controller、Endpoint 中提取路由候选 |
| 数据库表名提取 | 从 SQL、migration 或实体映射中提取表名候选 |
| 测试与生产代码关系 | 粗略识别测试项目对应的生产项目 |

### 8.3 暂不包含

| 暂缓能力 | 暂缓理由 |
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

---

## 9. LLM 使用边界

Scanner 本体确定性优先，LLM 只做解释层和人工校准建议。

### 9.1 确定性脚本负责

- 文件扫描
- 技术栈识别
- 模块识别
- 命令提取
- 配置文件识别
- 测试资产识别
- 浅层代码结构识别
- JSON/YAML 事实源生成

### 9.2 LLM 可以负责

- `scanner-report.md` 的说明性总结
- 模块职责的初步描述
- 人工校准点提示
- 后续 Skill 输入建议

### 9.3 LLM 不负责

- 事实源生成
- 命令凭空编造
- 构建是否成功的最终判断
- 风险区域自动判断
- 业务流程推断
- Task Mapping 决策

---

## 10. 输出契约设计

Scanner 输出采用：

```text
统一 core schema + 技术栈扩展字段
```

### 10.1 Core Schema

所有技术栈都必须输出：

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

### 10.2 Stack Extensions

技术栈差异放入扩展字段：

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

## 11. 第一阶段成功演示

第一阶段成功演示不包含 Task Mapping 和 AI Coding 执行。

演示方式：

1. 在 RuoYi-Vue 工程根目录调用 Scanner Skill。
2. 生成 `.harness/` 三个文件。
3. 打开 `project-inventory.json` 和 `command-catalog.yaml` 说明机器事实源。
4. 打开 `scanner-report.md` 说明人类解释层。
5. 在 eShopOnWeb 重复同一流程。
6. 对比两个技术栈下输出结构一致、扩展字段不同。
7. 说明这些输出如何成为后续 Task Mapping Skill / Harness Generator 的输入。

---

## 12. 成功标准

Scanner Skill 第一阶段成功标准：

1. 能在当前工程根目录运行。
2. 能对 RuoYi-Vue 生成 `.harness/`。
3. 能对 eShopOnWeb 生成 `.harness/`。
4. 两个项目都生成 `project-inventory.json`、`command-catalog.yaml`、`scanner-report.md`。
5. JSON/YAML 是主要事实源。
6. Markdown 报告不引入事实源之外的关键判断。
7. 两个技术栈共用同一 core schema。
8. 技术栈差异进入 stack extensions。
9. 输出能明确支撑下一阶段 Task Mapping Skill 的设计。

---

## 13. 当前建议

当前最合理的推进方式是：

1. 暂停 Task Mapping 相关实现设计。
2. 先完成 Scanner Skill 的 Brainstorm 和设计文档。
3. 将 GitHub 仓库中的实施计划降级为草稿，等 Scanner Skill 设计确认后重写。
4. 第一阶段只开发 `harness-builder init` / `scanner init` 这类初始化扫描能力。
5. Scanner Skill 稳定后，再进入 Task Mapping Skill 的 Brainstorm。

一句话：

```text
先把当前工程扫描清楚，再讨论某个任务怎么进入这个工程。
```
