# Harness Builder POC 实施计划

> ⚠️ 本文档为早期草稿，已被 `docs/plans/2026-05-25-scanner-skill-requirements.md` 与 `docs/plans/2026-05-25-scanner-skill-implementation-plan.md` 取代。当前第一阶段只实现 Scanner Skill，不包含 Task Mapping 或 AI Coding 执行。



> 状态：草案  
> 日期：2026-05-25  
> 范围：以 Scanner 为先的 POC 实现  
> 方法：规范优先 + 小步 TDD

---

## 1. 目标

围绕 Scanner 优先闭环构建首个 Harness Builder POC：

```text
RuoYi-Vue + eShopOnWeb
→ 确定性仓库扫描器
→ 项目清单
→ 命令目录
→ 扫描报告
→ 下一阶段 Harness Generator 的输入
```

本 POC 需验证：同一 Scanner 框架能够从至少两种常见企业技术栈中提取有价值的 Harness 输入。

---

## 2. 目标仓库

| 仓库 | 技术栈 | POC 角色 |
|---|---|---|
| `yangzongzhuan/RuoYi-Vue` | Java / Spring Boot / Maven / Vue | Java 企业后台系统基线 |
| `dotnet-architecture/eShopOnWeb` | .NET / ASP.NET Core / EF Core | 非 Java 跨技术栈基线 |
| `apache/fineract` | Java / Spring Boot / Gradle / PostgreSQL | 第二阶段复杂业务系统候选 |

首轮实现仅针对 RuoYi-Vue 和 eShopOnWeb。

---

## 3. 首个里程碑：Scanner 原型

### 输出契约

对每个目标仓库，生成：

```text
.harness/
  project-inventory.json
  command-catalog.yaml
  scanner-report.md
```

### Scanner 必备能力

1. 文件系统清单扫描
2. 技术栈检测
3. Java / Maven 检测器
4. Node / Vue 检测器
5. .NET 解决方案 / 项目检测器
6. CI / Docker 检测器
7. 命令目录生成
8. 人工可读的扫描报告

---

## 4. 开发顺序

### 任务 1 — 仓库骨架

- 创建 Scanner 包结构
- 添加最小化 CLI 入口
- 添加测试 Harness 和示例 fixture 目录

验证标准：

```bash
python -m pytest
python scanner/scan_repo.py --help
```

### 任务 2 — 文件系统清单

- 扫描顶层目录
- 按扩展名统计文件数量
- 检测常见文档 / 配置 / 构建文件

验证标准：

- 基于 fixture 仓库的单元测试通过
- JSON 输出包含预期目录和文件计数

### 任务 3 — Java / Maven 检测器

- 检测 `pom.xml`
- 提取 Maven 模块
- 检测 Spring 配置文件
- 检测 SQL 文件

验证标准：

- 基于 Maven fixture 的单元测试通过
- 对 RuoYi-Vue 运行并确认模块被正确检测

### 任务 4 — Node / Vue 检测器

- 检测 `package.json`
- 提取 scripts
- 检测 Vue 项目目录

验证标准：

- 基于 package fixture 的单元测试通过
- 对 `ruoyi-ui` 运行并确认 scripts 被正确提取

### 任务 5 — .NET 检测器

- 检测 `.sln`、`.csproj`、`global.json`、`Directory.Packages.props`
- 提取项目列表及推测的项目角色

验证标准：

- 基于 .NET fixture 的单元测试通过
- 对 eShopOnWeb 运行并确认项目结构被正确检测

### 任务 6 — 命令目录

- 生成 build / test / run / frontend 命令候选
- 记录每条命令的来源和置信度

验证标准：

- YAML 输出符合预期 schema 验证
- 命令包含 Maven 和 dotnet 候选

### 任务 7 — 扫描报告

- 渲染人工可读的 Markdown 报告
- 包含项目概览、已检测技术栈、模块、命令候选及人工校准要点

验证标准：

- 快照式测试或黄金文件比对通过
- 两个目标仓库均生成报告

### 任务 8 — 跨技术栈验证

- 分别对 RuoYi-Vue 和 eShopOnWeb 运行 Scanner
- 对比公共输出契约和技术栈特定差异

验证标准：

- 两个仓库均生成全部三项必需产物
- 摘要中明确区分公共部分与技术栈特定部分

---

## 5. 首个里程碑排除范围

- 风险区域检测
- 受限路径
- 人工升级策略
- 多工作流路由
- 经验积累 / 自我改进
- 成熟度模型
- 安全扫描集成
- 完整项目启动流程
- Web UI
- 数据库持久化存储

---

## 6. 完成定义

Scanner 原型在以下条件全部满足时视为完成：

1. 所有测试通过
2. Scanner 能在 RuoYi-Vue 上正常运行
3. Scanner 能在 eShopOnWeb 上正常运行
4. 每次运行输出 `project-inventory.json`、`command-catalog.yaml` 和 `scanner-report.md`
5. 报告质量足以支撑下一阶段 Harness Generator 的设计工作