# Guided review-candidate 失败 trace 实施计划

目标：让已有 Harness 入口的 guided `review-candidate` 在候选报告缺失或候选 ID 不存在时留下 action-specific trace，而不是退化成泛化 init failure。

## Steps

1. 红测
   - 在 `tests/integration/test_init_on_fixture_projects.py` 新增缺失 `.ai/review/asset-candidates.yaml` 的 guided `review-candidate` 失败测试。
   - 新增 unknown candidate id 失败测试，断言 trace summary 包含 `existing_harness_action=review-candidate`、candidate id 和 error。
   - 先运行目标测试，确认当前实现失败。

2. 实现
   - 修改 `src/harness_builder_agent/tools/existing_harness_action_runner.py`。
   - 在 `review-candidate` 分支开始时先记录 action-specific started event。
   - 捕获候选报告读取 / schema / candidate lookup 失败，写 `existing-harness` failed event 和 failed summary，再抛出 `typer.BadParameter`。
   - 成功路径避免重复 started event。

3. 验证
   - 运行新增 targeted integration。
   - 运行 `review-candidate` 相关 existing Harness regression。
   - 运行 `python -m compileall -q src tests` 和 `git diff --check`。

4. 文档记录
   - 更新 `docs/evolution-log.md`。
   - 如稳定行为需要，补充 README / init workflow 对 failure trace 的描述；若只是错误路径内部 trace 修复，则不扩写用户文档。

5. 最终验证与提交
   - 运行 `scripts/test-fast.sh`。
   - 创建中文本地 commit。
   - 本轮不 push。
