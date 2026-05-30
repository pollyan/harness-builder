# Sensor 与 Gate 规则

本文约束 Harness Builder 生成和验证 Sensor、hard gate、benchmark 检查的规则。修改 sensor、benchmark、验证报告或质量门禁前，先阅读本文。

## 基本概念

Sensor 是 Harness 中用于验证质量、风险和执行结果的机制。它不应该只是说明文档，而应该能对应到明确的验证活动或待补齐的验证能力。

Gate 是 Sensor 的执行强度。

当前建议分类：

- `hard`：必须通过。失败应导致 benchmark 失败或任务不能被视为通过。
- `advisory`：建议检查。失败或缺失会产生风险提示，但不一定阻断。
- `manual`：需要人工确认，不能自动判断。

Sensor 状态应明确：

- `passed`：验证已执行并通过。
- `failed`：验证已执行但失败。
- `skipped`：验证未执行，必须说明原因。
- `unresolved`：当前缺少足够信息判断。

`skipped` 和 `unresolved` 不能当作成功。

## 生成 Sensor 的规则

生成的 Sensor Markdown 至少应包含：

- 已发现的验证命令。
- 缺失验证能力。
- 推荐验证活动。
- 失败处理策略。
- hard/advisory/manual 的区分。

Sensor 内容应来自：

- `command-catalog.yaml` 中的命令候选。
- 内置武器库中的 stack-specific sensor。
- LLM scan proposal 中的风险和验证建议。
- 人工确认输入或组织级上下文。

Sensor 内容不应：

- 凭空假设项目有某个测试命令。
- 把无法执行的命令标记为 hard。
- 只写“请运行测试”这类泛泛建议。
- 对失败没有处理策略。

## Hard gate 规则

Hard gate 是质量底线。

规则：

- hard gate 必须有可执行命令或明确验证机制。
- hard gate 执行失败必须显式报告。
- hard gate skipped 必须显式报告原因。
- benchmark 不能把 hard gate failed/skipped 当作 passed。
- 如果命令过重、缺少依赖或无法确认，应先标记为 advisory 或 manual，而不是 hard。

适合 hard gate 的例子：

- 明确存在且可运行的单元测试命令。
- 明确存在且可运行的编译命令。
- 明确存在且可运行的 lint/typecheck 命令。

不适合直接 hard gate 的例子：

- 需要外部数据库但没有本地配置的集成测试。
- 需要云服务账号的测试。
- LLM 猜测出来但 evidence 不支持的命令。

## Benchmark 规则

Benchmark 是 Harness Builder 的 POC 验收器，应检查生成 Harness 的最低质量。

Benchmark 应检查：

- 必需文件存在。
- JSON/YAML schema 正确。
- Markdown 必需章节存在。
- workflow skill 文件存在并被引用。
- generation trace 存在且包含阶段和 artifact。
- runtime trace 存在且包含 workflow、guide、sensor 信息。
- weapon library selection 与生成 guide/sensor 内容一致。
- hard gate sensor 结果真实反映 passed/failed/skipped。

Benchmark 不应：

- 只做文件存在检查。
- 自动修复缺失文件。
- 把失败吞掉后返回成功。
- 因为真实命令失败就隐藏错误。

## Sensor Report 规则

Sensor report 应能被程序读取。

规则：

- 必须符合 schema。
- 每个 sensor result 必须有 id、status、summary。
- failed/skipped/unresolved 必须有解释。
- hard gate 失败必须能被 benchmark 汇总。
- report 应保留执行命令和输出摘要，但不要无限制写入完整日志。

## 与生成资产的关系

Sensor 不是孤立文件。它应该和以下产物一致：

- `command-catalog.yaml`
- `harness-config.yaml`
- `weapon-library-selection.yaml`
- `runtime-summary.yaml`
- `sensor-report.yaml`
- `benchmark-report.yaml`

跨文件引用必须可测试。例如：

- `weapon-library-selection.yaml` 中的 sensor weapon id 应出现在生成的 sensor Markdown 中。
- `harness-map.yaml` 中选择的 workflow skill 路径必须存在。
- `sensor-report.yaml` 中的 hard gate 状态应影响 benchmark。

## 测试要求

修改 Sensor 或 benchmark 时，至少覆盖：

- Sensor Markdown 包含必需章节。
- Stack-specific sensor weapon id 出现在输出中。
- hard gate passed 时 benchmark 可以通过。
- hard gate failed 时 benchmark 失败并列出失败摘要。
- skipped 不被当作 passed。
- sensor report schema 校验。
- command catalog 与 sensor 内容有关联。

## 后续演进

未来可以增强：

- 更细的 gate policy。
- 针对不同技术栈的 sensor weapon library。
- 对命令执行环境的可用性检测。
- 对 flaky gate 的单独标记。
- 人工确认后把 candidate sensor 晋升为正式 sensor。

但这些增强不能改变一个底线：Sensor 必须帮助暴露真实质量问题，而不是制造看起来通过的幻觉。

