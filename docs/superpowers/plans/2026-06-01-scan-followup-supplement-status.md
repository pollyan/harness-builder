# Scan Follow-up 补充状态标注实施计划

## 目标

让 scan follow-up 在同轮 guided `init` 中收到结构化 scan supplement 后，进入 `questionnaire.yaml` / `human-input-needed.md` 的待复核标注，而不是继续表现为完全未处理。

## 文件

- 修改：`src/harness_builder_agent/tools/human_confirmation.py`
- 修改：`src/harness_builder_agent/tools/write_assets.py`
- 修改：`tests/unit/test_human_confirmation.py`
- 修改：`tests/integration/test_init_on_fixture_projects.py`
- 修改：`docs/engineering/init-workflow.md`
- 修改：`docs/evolution-log.md`

## TDD 步骤

1. Unit：在 `tests/unit/test_human_confirmation.py` 新增：
   - 有 follow-up + matching structured scan supplement 时，reason 包含部分回应标注、补充摘要和 pending review。
   - 无 matching supplement 时，不出现部分回应标注。

   预期先失败，因为 `build_questionnaire()` 当前没有 `interaction_decisions` 参数。

2. Integration：在 `tests/integration/test_init_on_fixture_projects.py` 新增 guided init 场景：
   - mock scan metadata 提供 `test_evidence_missing` / `module_boundary_unclear` follow-up。
   - 用户输入 `module=...; command=...; risk=...`。
   - 断言 questionnaire / human-input / interaction-decisions 的补充状态和 review 边界。

   预期先失败，因为 writer 没有把 decisions 传给 questionnaire。

3. 实现：
   - `build_questionnaire(..., interaction_decisions=None)` 接收 `InteractionDecisions` 或 dict。
   - 增加 helper：从 `scan_confirmation` 提取 stack / module / command / risk / notes 摘要。
   - 根据 follow-up trigger / affects 做保守相关性匹配。
   - 在相关时追加 reason 标注。
   - `write_initial_assets()` 传入 `decisions`。

4. 文档：
   - `docs/engineering/init-workflow.md` 增加稳定规则：用户 scan supplement 只能标注 follow-up 已被部分回应，仍需维护者复核，不能自动关闭追问。
   - `docs/evolution-log.md` 记录本轮 Gap Analysis、决策、验证和 Gate。

5. 验证：
   - Targeted unit。
   - Targeted guided integration。
   - 相关 human confirmation / interaction decisions tests。
   - `git diff --check`。
   - commit 前运行 `scripts/test-fast.sh`。

## 非目标

- 不新增 questionnaire resolved schema。
- 不修改 LLM self-check。
- 不自动关闭 follow-up。
- 不改变正式扫描事实、workflow routing policy 或 Runtime 边界。
