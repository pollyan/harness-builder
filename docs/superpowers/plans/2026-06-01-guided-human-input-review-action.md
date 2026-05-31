# Guided Human Input Review Action 实施计划

目标：把 standalone `review-human-input` 接入已有 Harness guided `init` 维护入口，使 Maintainer 可以在同一入口内治理 scan follow-up confirmation。

## Steps

1. 红测：菜单 normalization
   - 修改 `tests/unit/test_interactive_init_preview.py`。
   - 断言新增编号映射为 `review-human-input`，并支持 `review-human-input`、`human-input`、`人工输入`、`待确认` 等别名。

2. 红测：guided existing Harness human-input review
   - 修改 `tests/integration/test_init_on_fixture_projects.py`。
   - 先用 guided `init` 制造 `confirm:scan-followup:test-evidence`，并 snapshot 正式资产。
   - 再次运行 `init`，输入 `review-human-input`、interaction id、`resolved`、rationale、reviewer。
   - 断言 questionnaire status、governance YAML / Markdown、human-input Markdown、trace summary / artifacts。
   - 断言正式资产不变、没有重新扫描、没有 `.ai/task-runs`。

3. 实现菜单和 action
   - 修改 `src/harness_builder_agent/tools/interactive_init.py`。
   - import `review_human_input` 与 `HumanInputGovernanceLog`（如需要）。
   - `_existing_harness_action_menu_lines()` 新增 `review-human-input`，保持 `reinit` 编号后移。
   - `_normalize_existing_harness_action()` 增加数字和别名。
   - `_handle_existing_harness_entry()` 增加 action 分支：收集 interaction id / decision / rationale / reviewer，调用 `review_human_input()`，记录 trace event / artifacts / summary，输出摘要。

4. 文档同步
   - README 的 existing Harness 菜单说明新增该动作。
   - `docs/engineering/init-workflow.md` 的 existing Harness 维护动作规则新增该动作和边界。
   - `docs/evolution-log.md` 增加本轮记录。

5. 验证
   - 运行目标 unit。
   - 运行目标 integration。
   - 运行完整 guided init integration。
   - `git diff --check`。
   - `scripts/test-fast.sh`。

6. 提交
   - 中文 commit message。
   - 不 push；当前 push 前 full regression 仍受 `DEEPSEEK_API_KEY` 与 `.benchmarks` 前置条件阻塞。
