# Human Input Triage Recommendation 实施计划

目标：让已有 Harness 的 Maintenance triage 在 scan follow-up backlog 存在时主动推荐 `review-human-input`。

## Steps

1. 红测：unit
   - 修改 `tests/unit/test_maintenance_triage.py`。
   - 增加 helper 写 `.ai/questionnaire.yaml`。
   - 覆盖 benchmark passed / experience clean / human-input backlog 存在时，唯一 top action 是 `review-human-input`。
   - 覆盖 benchmark missing 时，`benchmark` 仍在第一位，`review-human-input` 在第二位。
   - 覆盖 resolved-only scan follow-up 不进入 triage。

2. 红测：integration
   - 修改 `tests/integration/test_init_on_fixture_projects.py`。
   - 在已有 Harness exit 场景中制造 scan follow-up，并断言输出包含 `top_action_2=review-human-input`、`human_input_scan_followups_pending`、首个 `confirm:*` detail 和中文 guidance。
   - 断言该路径不重新扫描、不覆盖正式资产、不创建 `.ai/task-runs`。

3. 实现
   - 修改 `src/harness_builder_agent/tools/maintenance_triage.py`。
   - 引入 `Questionnaire` schema。
   - 新增 helper 统计未解决 scan follow-up count 和首个 interaction id。
   - 在 benchmark / Experience action 之后加入 priority=25 的 `review-human-input` action。
   - 更新 `_maintenance_action_guidance()`。

4. 文档
   - README 的 Maintenance triage 示例加入 `review-human-input`。
   - `docs/engineering/init-workflow.md` 增加 triage 推荐 human-input backlog 的长期规则。
   - 更新 `docs/evolution-log.md`。

5. 验证
   - 目标 unit。
   - 目标 integration。
   - 完整 guided init integration。
   - `git diff --check`。
   - `scripts/test-fast.sh`。

6. 提交
   - 中文 commit message。
   - 本轮不 push；push 仍需 full regression 和外部前置。
