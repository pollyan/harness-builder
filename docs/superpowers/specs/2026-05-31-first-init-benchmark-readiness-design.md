# First Init Benchmark Readiness Design

## 用户故事

作为第一次为仓库建立 Harness 的 Harness Maintainer，当 `init` 完成第一版 `.ai` 资产生成后，我可以直接看到 benchmark 健康度目前是未运行、为什么不默认运行、应该用哪个入口完成首次质量验收，以及验收会检查哪些方面，从而知道第一版 Harness 还没有被质量门禁证明通过。

## Current State Gap Analysis

- North Star 要求首次 `init` 不只是甩文件列表，而要用成熟度主线解释当前状态、阻断项和下一步。
- 当前 `init-summary.md` 已有当前成熟度、主要阻断项、建议下一步、推荐入口文件和本次未执行事项。
- 当前 CLI 完成输出已显示成熟度、阻断项、下一步和入口文件。
- 但首次初始化完成后，用户看不到 benchmark 健康状态：`.ai/benchmark-report.yaml` 是否存在、为什么首次 `init` 没有默认运行 benchmark、下一步应该如何触发验收、benchmark 会验证哪些质量面。
- 这会让 Maintainer 误以为“资产生成成功”等同于“Harness 质量已验收通过”。

## 目标

- `init-summary.md` 增加稳定章节 `## Benchmark 健康度`。
- 首次 `init` 完成 CLI 输出增加 benchmark readiness 摘要。
- 当 `.ai/benchmark-report.yaml` 不存在时，明确展示：
  - `benchmark_status=not_run`
  - `quality_status=not_available`
  - 推荐命令：`harness-builder-agent benchmark --repo <repo>`
  - 不默认运行 benchmark 的边界：首次 init 不执行质量门禁，不等同于 benchmark passed。
- 如果未来 summary 生成时已有 benchmark report，复用 `BenchmarkReport` schema 展示 status / quality / failed checks。
- Benchmark readiness 是解释性输出，不改变首次 `init` 默认执行边界，不触发 benchmark，不增加耗时。

## 非目标

- 不让首次 `init` 默认运行 benchmark。
- 不改变 standalone 或 existing-Harness guided `benchmark` 行为。
- 不新增机器消费 schema。
- 不改变 benchmark 检查项。
- 不运行真实 DeepSeek acceptance。

## 设计

扩展 `init_summary.py`：

- 新增 `_benchmark_readiness_lines(ai)`：
  - 如果 `.ai/benchmark-report.yaml` 缺失，返回 `benchmark_status=not_run`、`quality_status=not_available`、推荐命令和边界说明。
  - 如果存在，使用 `BenchmarkReport` schema 校验并返回 status / quality / failed checks。
- `build_init_summary_markdown(score, ai=None)` 增加可选 `ai` 参数；`write_init_summary(ai, score)` 传入 `ai`，测试中的纯 score 调用仍可不传。
- `render_init_completion_message(ai)` 增加 `Benchmark 健康度` 段，读取同一 helper。

## 验收标准

- integration 覆盖非交互首次 `init` 后 `.ai/init-summary.md` 包含 `## Benchmark 健康度`、`benchmark_status=not_run`、`quality_status=not_available`、推荐 benchmark 命令和“not equivalent to benchmark passed” 边界。
- integration 覆盖非交互首次 `init` CLI 输出包含 benchmark readiness 摘要。
- unit 覆盖已有 benchmark report 时 summary / completion message 使用 `BenchmarkReport` schema 展示 failed check count。
- 测试确认首次 `init` 不创建 `.ai/benchmark-report.yaml`，不改变默认耗时边界。
- README、init workflow、todo 和 evolution log 同步说明首次 init 会展示 benchmark readiness，但不会默认运行 benchmark。

## Decisions / Responses

- 价值切分：本轮服务 0→1 首次用户“知道第一版 Harness 尚未验收”的独立价值，不是内部文档字段。
- 效率回应：不默认运行 benchmark，避免拉长首次 `init` 循环；用户可以用 standalone 或 existing-Harness guided `benchmark` 明确触发。
- 边界回应：资产生成成功不是 benchmark passed，必须在 summary 和 CLI 输出中明确。
- 兼容回应：如果已有 benchmark report，严格通过 `BenchmarkReport` schema 展示，不 ad hoc 解析。

## Assumptions / Risks

- 假设首次 init 不默认跑 benchmark 是当前更稳妥的 POC 边界；以后可以增加显式 `init` 末尾动作选择。
- 风险是输出变长；本轮只增加一小段稳定 health summary。
- 风险是用户需要复制命令；后续可以用 existing-Harness guided `benchmark` 或 IDE action 降低操作成本。
