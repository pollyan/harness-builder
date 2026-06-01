# Existing Harness Signal Renderer 抽取计划

目标：把已有 Harness 维护入口的 benchmark / workflow routing / experience signals 从 `interactive_init.py` 抽到独立模块，保持 CLI 行为等价。

## 实施步骤

1. 写 RED 测试
   - 新增 `tests/unit/test_existing_harness_signals.py`，从新模块导入 signal renderer。
   - 覆盖缺 benchmark report、failed benchmark detail、workflow routing standard / risk trigger、experience index + human-input + workflow recommendation signals。
   - 先运行 targeted unit，确认因为模块缺失而失败。

2. 新增 `existing_harness_signals.py`
   - 搬迁 `_read_benchmark_status()`、`_benchmark_signal_lines()`、`_workflow_routing_status_lines()`、`_experience_status_lines()` 及其私有 helper。
   - 使用现有 Pydantic schema 读取 `BenchmarkReport`、`ExperienceIndex`、`Questionnaire`、`WorkflowRecommendationHistory`、`WorkflowRecommendationReport` 和 `SelfImprovePackageManifest`。
   - 从 `human_confirmation` 复用 `SCAN_CONFIRMATION_TYPES`。

3. 连接 `interactive_init.py`
   - 从新模块导入 `read_benchmark_status`、`benchmark_signal_lines`、`workflow_routing_status_lines`、`experience_status_lines`。
   - 删除或改写原内联 helper 为薄 facade。
   - 清理不再需要的 imports 和重复 `SCAN_CONFIRMATION_TYPES`。

4. 文档与演进记录
   - 更新 `docs/evolution-log.md`，记录本轮工程信任故事、验证结果和 Gate。
   - 本轮行为等价，不更新 README / init workflow 长期产品规则。

5. 验证
   - 运行新 unit。
   - 运行 existing Harness 只读 exit integration。
   - 运行 `git diff --check`。
   - 创建 commit 前运行 `scripts/test-fast.sh`。

## 非目标

- 不拆动作执行分支。
- 不改变 existing Harness 菜单、标题、signals 内容、triage 排序或动作语义。
- 不修改 schema、LLM、benchmark 检查规则或 Runtime 边界。
- 不 push；本轮只是本地工程信任切片。
