# Observable Harness Generation Design

## 背景

`docs/ideas/observable-harness-generation.md` 提出：`init`、`assess`、`improve` 的生成过程需要可追溯。当前 POC 已能生成 `.ai` 资产，也能在 benchmark 中校验一部分 schema 和内容，但用户仍难以回答这些问题：

- 为什么扫描出了当前技术栈？
- 为什么选择了这些武器库条目？
- 哪些文件是由哪一步生成的？
- benchmark 或 sensor 失败时，前置生成链路是否正常？

## 目标

为 Harness Builder 增加一个轻量级、本地文件化的 generation trace。每次 `init`、`assess`、`improve`、`benchmark` 运行时，都能在 `.ai/runs/<run_id>/` 下留下结构化事件、摘要和产物索引，支持人工审计和自动测试。

## 非目标

- 不做 Web UI、后台服务或远程遥测。
- 不采集密钥、完整源码内容或用户未显式生成的私有数据。
- 不替代现有 `.ai/scan-report.md`、`benchmark-report.yaml`、`sensor-report.yaml`，而是补充“生成过程本身”的追溯。
- 不在本轮实现跨运行趋势分析。

## 方案比较

### 方案 A：只扩展现有报告

把 trace 信息塞进 `scan-report.md`、`maturity-report.md`、`benchmark-report.yaml`。

优点是改动少。缺点是报告职责会混乱，且无法表达多步骤事件时间线。

### 方案 B：新增 `.ai/runs/<run_id>/` 本地 trace

每次 CLI 命令创建一个 run 目录，写入 `events.jsonl`、`trace.yaml`、`decision-log.md` 和 `artifacts.yaml`。

优点是结构清晰、容易测试、便于未来 UI/IDE 读取。缺点是需要引入 run context 和少量写入封装。

### 方案 C：引入 OpenTelemetry 或外部日志系统

优点是标准化程度高。缺点是对当前 CLI POC 过重，也会引入部署和隐私问题。

本轮选择方案 B。

## 产物结构

每次命令运行创建：

```text
.ai/runs/<run_id>/
  events.jsonl
  trace.yaml
  decision-log.md
  artifacts.yaml
```

`run_id` 使用稳定可读格式：`YYYYMMDD-HHMMSS-<command>`。测试中允许注入固定 run id。

## 事件模型

`events.jsonl` 每行一个 JSON 对象：

```json
{
  "schema_version": "1.0",
  "run_id": "20260530-120000-init",
  "command": "init",
  "stage": "scan",
  "event_type": "completed",
  "message": "LLM scan reconciled into inventory and command catalog.",
  "details": {
    "primary_stack": "java-spring",
    "command_count": 1
  }
}
```

字段要求：

- `schema_version`：固定为 `1.0`。
- `run_id`：当前 run id。
- `command`：`init`、`assess`、`improve`、`benchmark`。
- `stage`：`scan`、`weapon-selection`、`asset-write`、`maturity`、`improvement`、`benchmark`、`sensor` 等。
- `event_type`：`started`、`completed`、`warning`、`failed`。
- `message`：面向人的短说明。
- `details`：结构化上下文，只记录摘要和路径，不记录密钥。

## Trace 摘要

`trace.yaml` 是机器可读摘要：

```yaml
schema_version: '1.0'
run_id: 20260530-120000-init
command: init
status: completed
repo_name: mini-spring-boot
stages:
  - scan
  - weapon-selection
  - asset-write
summary:
  primary_stack: java-spring
  command_count: 1
  generated_artifact_count: 18
```

`decision-log.md` 是中文可读摘要，描述关键决策：

- 识别到的主技术栈和证据来源。
- 命中的武器库条目数量。
- 生成了哪些核心资产。
- 是否有 warning 或 failed 事件。

`artifacts.yaml` 记录本次命令写出的核心文件：

```yaml
schema_version: '1.0'
run_id: 20260530-120000-init
artifacts:
  - path: .ai/project-inventory.json
    kind: inventory
  - path: .ai/guides/project-context.md
    kind: guide
```

## CLI 集成

`init`：

1. 开始 run，记录 `scan.started`。
2. 扫描完成后记录 `scan.completed`，包含 `primary_stack`、`stacks`、`command_count`。
3. 写资产前记录 `asset-write.started`。
4. 写资产后记录 `asset-write.completed`，包含生成文件清单。
5. 完成 run。

`assess`：

1. 开始 run。
2. 写入成熟度报告后记录 `maturity.completed`。
3. 完成 run。

`improve`：

1. 开始 run。
2. 写入改进候选后记录 `improvement.completed`。
3. 完成 run。

`benchmark`：

1. 开始 run。
2. 执行 benchmark 后记录 `benchmark.completed` 或 `benchmark.failed`。
3. 将 benchmark 报告路径放入 artifacts。

## 错误处理

- 如果命令失败，trace run 仍应尽量写入 `trace.yaml`，`status=failed`。
- 失败事件要记录错误类型和短消息。
- trace 写入失败不应掩盖原始业务错误，但在 POC 中可以让命令失败并暴露问题。

## 测试策略

单元测试：

- `GenerationTrace` 能写 `events.jsonl`、`trace.yaml`、`artifacts.yaml`、`decision-log.md`。
- 事件字段完整，JSONL 每行可解析。
- artifact 路径必须使用 `.ai/...` 相对路径。

集成测试：

- `init` 在 fixture 仓库生成 `.ai/runs/<run_id>/`。
- trace 中包含 `scan`、`weapon-selection`、`asset-write`。
- artifacts 包含 `project-inventory.json`、`llm-scan-proposal.json`、核心 guide/sensor/skill。

Benchmark 测试：

- benchmark report 新增 `exists:runs-trace`、`schema:generation-trace`、`content:generation-trace`。
- 真实仓库 e2e 至少断言 run trace 存在且包含 benchmark hard gate 结果摘要。

## 验收标准

- 默认测试通过。
- 真实 DeepSeek fixture acceptance 通过。
- 真实开源仓库 e2e acceptance 通过。
- 任意一次 `init --repo <repo>` 后，用户能打开 `.ai/runs/<latest>/decision-log.md` 看懂本次生成的关键决策。

