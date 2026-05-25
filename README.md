# Harness Builder

Harness Builder 是一个概念验证（POC）项目，目标是从现有企业级代码库中自动生成项目级 AI Coding Harness 资产。

当前 POC 聚焦于 Scanner v2：通过 **LLM 分析 + 确定性脚本证据** 建立代码库现状基线，并生成初始 Harness 资产。

```text
目标仓库
→ Scanner v2
→ project-inventory.json / command-catalog.yaml / scanner-report.md
→ 后续 Guides / Sensors / Workflow Runtime / Task Mapping
```

## 当前状态

Scanner v2 已完成 POC 主路径：

- 文件树收集
- DeepSeek LLM 两轮扫描与自检
- 按 LLM 结论选择性提取确定性证据
- LLM 推断 vs 脚本事实校验
- 命令候选生成
- CLI 默认 LLM 模式 + `--no-llm` 离线模式
- v2 scanner report
- RuoYi-Vue / eShopOnWeb 真实 smoke 验证

当前仍是 POC，不是生产级产品。后续模块包括 Guides、Sensors、Workflow Runtime、Experience 和 Maturity。

## POC 范围

首轮 POC 验证两种常见企业技术栈：

- Java / Spring Boot / Maven / Vue：RuoYi-Vue
- .NET / ASP.NET Core / EF Core：eShopOnWeb

Apache Fineract 作为第二阶段复杂业务系统候选，已纳入跟踪。

## Scanner v2 使用方式

### 默认模式：启用 DeepSeek LLM

在仓库根目录准备 `.env`：

```bash
DEEPSEEK_API_KEY=your-key
# 可选
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
```

运行：

```bash
python3 -m harness_builder.scanner.cli \
  --repo /path/to/target-repo \
  --out /path/to/output/.harness
```

### 离线模式：不调用 LLM

```bash
python3 -m harness_builder.scanner.cli \
  --repo /path/to/target-repo \
  --out /path/to/output/.harness \
  --no-llm
```

## 输出文件

Scanner 会生成三个核心文件：

```text
.harness/
  project-inventory.json   # v2 inventory: fileTree / analysis / evidence / validation
  command-catalog.yaml     # build / test / run / frontend / docker 命令候选
  scanner-report.md        # 人类可读扫描报告
```

### `project-inventory.json`

包含：

- `repo`：仓库元数据
- `fileTree`：确定性文件树
- `analysis`：LLM 推断结果（技术栈、模块、命令、架构、异常等）
- `evidence`：脚本检测事实（Java/Node/.NET/CI/目录结构等）
- `validation`：LLM 推断与脚本事实的交叉校验结果

### `command-catalog.yaml`

命令分组：

- `build`
- `test`
- `run`
- `frontend`
- `docker`

每条命令包含：`name`、`command`、`workingDirectory`、`source`、`confidence`、`verified`。

## 开发与验证

本仓库遵循规范优先（Spec-first）和 TDD 开发流程：

1. 先设计，后实现
2. 先制定实施计划，后编写代码
3. 小粒度任务拆分
4. 测试先行
5. 真实目标仓库 smoke 验证
6. 扩大范围前必须经过评审

运行测试：

```bash
python3 -m pytest -q
```

Scanner v2 smoke 记录见：

```text
docs/research/scanner-v2-smoke-test.md
```
