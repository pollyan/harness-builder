# Harness Builder POC 武器库设计

## 背景

当前 POC 已能根据代码扫描结果生成 Guides、Sensors 和 Workflow Skills，但 Guides / Sensors 的技术栈建议仍散落在生成逻辑里。这样会带来两个问题：

- 同一代码库多次生成时，用户很难判断建议来自扫描事实、内置经验还是模型自由发挥。
- 不同技术栈的最佳实践缺少可审计、可复用、可 benchmark 的稳定来源。

## 决策

采用“内置武器库 + 扫描匹配 + 确定性摘取”的方案。

候选方案对比：

- 让大模型完全动态生成：表达力强，但稳定性和可复现性不足，不适合 POC 验收。
- 每个技术栈复制一整套固定模板：稳定，但无法体现项目扫描事实，也不利于未来细粒度演进。
- 内置结构化武器库，按扫描出的主技术栈和证据选择条目：稳定、可审计，也能保留项目事实注入能力。POC 采用该方案。

## 设计

武器库以代码内置数据结构交付，POC 覆盖：

- `common`：所有技术栈通用的 Guides / Sensors。
- `java-spring`：Spring / Maven / 登录权限 / SQL / 配置变更相关规则和验证建议。
- `dotnet-aspnet`：solution / Clean Architecture / PublicApi / Infrastructure / appsettings / dotnet test 相关规则和验证建议。

生成流程：

1. Scanner 输出 `ProjectInventory` 和 `CommandCatalog`。
2. Weapon Library 根据 `inventory.primary_stack` 选择 `common + stack-specific` 条目。
3. Harness Builder 写出 `.ai/weapon-library-selection.yaml`，作为本次摘取结果的审计文件。
4. Guides / Sensors 只引用已选择的武器库条目，再叠加扫描出的模块、证据和命令。
5. Benchmark 校验选择文件、schema、Guide / Sensor 中的武器库引用和技术栈特定内容。

## 产物

新增或增强以下产物：

- `.ai/weapon-library-selection.yaml`：本次选择的技术栈、guide weapon ids、sensor weapon ids、来源和摘要。
- `.ai/guides/*.md`：增加“武器库匹配结果”章节，并把候选规则、推荐补齐项映射到 weapon id。
- `.ai/sensors/*.md`：增加“武器库匹配结果”章节，并将缺失能力、推荐验证活动和失败策略映射到 sensor weapon id。
- `.ai/benchmark-report.yaml`：新增存在性、schema 和内容校验。

## 非目标

POC 不做大模型动态生成武器库、不做运行时联网下载最佳实践、不做 IDE 内 skill runtime 集成。Workflow Skills 仍按内置模板复制；Guides / Sensors 通过武器库稳定组装。

## 验收标准

- Java Spring 和 .NET ASP.NET fixture 都生成 `weapon-library-selection.yaml`。
- 两类 fixture 的 Guide / Sensor 都包含通用武器和对应技术栈武器 id。
- Benchmark 不再只依赖关键词，而是校验武器库选择文件和引用关系。
- 全量测试通过，真实 benchmark 流程仍能生成 Guides、Sensors、Skills、成熟度和改进候选。
