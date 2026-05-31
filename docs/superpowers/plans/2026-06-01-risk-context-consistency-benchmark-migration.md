# Risk Context Consistency Benchmark 迁移计划

## 用户故事

作为 Harness Maintainer，当我运行 `benchmark` 验收包含扫描风险区域的 Harness 时，我可以确认每个 scan risk path 同时出现在 Guide、Sensor 和 standard routing 中；如果任一环缺失，benchmark 会给出精确缺失路径，从而保护高风险任务进入正确 Workflow 的信任链。

## 实施步骤

1. RED tests：
   - 在 `tests/integration/test_benchmark_command.py` 增加生成式风险 fixture，先证明 `benchmark` 应包含并通过 `content:risk-context-consistency`。
   - 增加 helper 构造一致风险上下文。
   - 增加三类负向测试：Guide 缺路径、Sensor 缺路径、routing 缺路径。
2. 实现 benchmark：
   - 在 `src/harness_builder_agent/tools/benchmark.py` 新增 `_benchmark_risk_areas()` 和 `_risk_context_consistency_check()`。
   - 将该 check 接入 `_content_checks()`。
3. 实现生成侧 routing：
   - 在 `src/harness_builder_agent/tools/write_assets.py` 用 inventory / commands 构建 HarnessConfig。
   - 对前几个 risk area 追加 `risk_area:<path>` trigger，并在 standard escalation rationale 中写入 path 和 reason。
4. 文档同步：
   - 更新 `README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/sensor-and-gate-rules.md`、`docs/engineering/testing-strategy.md`。
   - 更新 `docs/todos/local-unique-capability-migration.md` 已迁移切片。
   - 更新 `docs/evolution-log.md`。
5. 验证：
   - targeted benchmark integration。
   - `git diff --check`。
   - `scripts/test-fast.sh`。
6. 提交：
   - 本地中文 commit，不 push；迁移工作包尚未完成。
