# Review Human Input 默认待处理项实施计划

目标：让已有 Harness 维护入口的 `review-human-input` guided action 能默认使用 triage 推荐的首个待处理 scan follow-up interaction id。

## 实施步骤

1. 写 RED 测试
   - 修改 `test_guided_init_existing_harness_can_review_human_input_without_overwriting_formal_assets`，在 interaction id prompt 直接回车。
   - 保留对 governance、questionnaire、trace 和 formal assets unchanged 的断言。
   - 先运行该 integration，确认当前代码因为空 interaction id 失败。

2. 实现默认 id
   - 在 `interactive_init.py` 中增加小 helper，从 `maintenance_actions` 找到 `human_input_scan_followups_pending` 的 `detail`。
   - `review-human-input` 分支用该值作为 `typer.prompt()` 默认值；没有默认值时保持 `default=""`。
   - 不改变 `review_human_input()` 的校验，不增加 silent fallback。

3. 验证
   - 运行目标 integration。
   - 运行 existing Harness 相关 unit / integration 切片。
   - 运行 `git diff --check`。
   - 提交前运行 `scripts/test-fast.sh`。

## 非目标

- 不修改 `Questionnaire`、`HumanInputGovernanceLog` 或其他 schema。
- 不自动治理所有待处理 follow-up。
- 不跳过 reviewer / rationale / decision prompt。
- 不修改正式 Guides、Sensors、Workflow Skills、配置或 Runtime 产物。
- 不抽取 existing Harness action execution 模块。
