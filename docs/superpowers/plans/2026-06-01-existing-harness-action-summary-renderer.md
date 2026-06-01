# Existing Harness Action Summary Renderer 抽取计划

目标：把已有 Harness 维护动作的完成摘要、候选详情和应用预览从 `interactive_init.py` 抽到独立 renderer 模块，保持行为等价。

## 实施步骤

1. 写 RED 测试
   - 新增 `tests/unit/test_existing_harness_action_summaries.py`。
   - 从新模块导入 summary / preview renderer。
   - 覆盖 benchmark failed summary、workflow recommendation summary、candidate detail / apply preview、candidate governance summary、human-input governance summary、self-improve summary、top improvement candidate。
   - 先运行 targeted unit，确认因为模块缺失失败。

2. 新增 `existing_harness_action_summaries.py`
   - 搬迁 `_benchmark_summary()`、`_workflow_recommendation_summary()`、`_candidate_governance_summary()`、`_human_input_governance_summary()`、`_asset_candidate_detail()`、`_asset_candidate_apply_preview()`、`_candidate_append_diff_lines()`、`_self_improve_summary()`、`_top_improvement_candidate()`。
   - 使用现有 Pydantic schema：`BenchmarkReport`、`WorkflowRecommendationReport`、`SelfImprovePackageManifest`、`ImprovementCandidateReport`。

3. 连接 `interactive_init.py`
   - 从新模块导入 public renderer。
   - Action 分支改为调用 public renderer。
   - 保留 underscore facade 调用新模块，兼容旧测试和隐藏调用。
   - 清理不再需要的 imports。

4. 文档与演进记录
   - 更新 `docs/evolution-log.md`，记录本轮工程信任故事、验证结果和 Gate。
   - 本轮行为等价，不更新 README / init workflow 长期产品规则。

5. 验证
   - 运行新 unit。
   - 运行 existing Harness targeted integration。
   - 运行 `git diff --check`。
   - 创建 commit 前运行 `scripts/test-fast.sh`。

## 非目标

- 不抽取 action execution 分支。
- 不改变 existing Harness 菜单、action prompt、trace、artifact、summary 文案或错误语义。
- 不修改 schema、LLM、benchmark 检查规则或 Runtime 边界。
- 不 push；本轮只是本地工程信任切片。
