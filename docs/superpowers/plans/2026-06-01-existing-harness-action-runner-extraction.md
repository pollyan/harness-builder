# Existing Harness Action Runner 抽取计划

目标：把已有 Harness 维护动作执行分支从 `interactive_init.py` 抽到独立 runner 模块，保持 guided `init` 维护入口行为等价。

## 实施步骤

1. 写 RED 测试
   - 新增 `tests/unit/test_existing_harness_action_runner.py`。
   - 从新模块导入 `run_existing_harness_action()` 和 `review_human_input_default_interaction_id()`。
   - 用 fake trace 覆盖 `exit`、`reinit`、unknown action 和 human-input 默认 id helper。
   - 先运行 targeted unit，确认因为模块缺失失败。

2. 新增 `existing_harness_action_runner.py`
   - 搬迁 existing Harness action execution 分支：`exit`、`assess`、`improve`、`benchmark`、`recommend-workflow`、`review-candidate`、`review-human-input`、`self-improve`、`reinit`、unknown action。
   - 搬迁 `_show_asset_candidate_summary()`、`_find_asset_candidate()` 和 `review_human_input_default_interaction_id()`。
   - 复用 `existing_harness_action_summaries.py` 的 summary / preview renderer。
   - 保持 trace event、trace artifact、trace finish summary、异常类型和 CLI 输出等价。

3. 连接 `interactive_init.py`
   - 保留现有状态读取、overview / signals / triage / menu 渲染和 action normalize。
   - 用 `run_existing_harness_action(repo, ai, inventory, action, trace, maintenance_actions)` 替换内联执行分支。
   - 清理不再需要的 imports。
   - 保留 underscore facade：`_review_human_input_default_interaction_id()`、`_show_asset_candidate_summary()`、`_find_asset_candidate()` 等按需转发到 runner / summary 模块。

4. 文档与演进记录
   - 更新 `docs/evolution-log.md`，记录本轮 Gap Analysis、工程信任故事、验证结果和 Self-Harness Gate。
   - 本轮行为等价，不更新 README / init workflow 长期产品契约。

5. 验证
   - 运行新增 runner unit。
   - 运行 existing Harness targeted integration，覆盖所有 action 关键路径。
   - 运行 `compileall` 和 `git diff --check`。
   - 提交前运行 `scripts/test-fast.sh`。

## 非目标

- 不新增或删除 existing Harness action。
- 不改变 action 菜单、默认 `exit`、action prompt、summary 文案、trace / artifact 语义或错误语义。
- 不修改 schema、LLM prompt、scan、benchmark 规则或 Runtime 边界。
- 不运行或创建 `.ai/task-runs`。
- 不 push；本轮只是本地工程信任切片。
