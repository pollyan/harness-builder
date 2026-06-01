# 已有 Harness 维护入口焦点前置实施计划

## 目标

调整 guided `init` 在已有 Harness 入口的终端输出顺序：让 Maintainer 先看到维护建议和菜单编号，再看 raw audit signals，减少第一屏内部字段干扰。

## 步骤

1. 失败测试
   - 更新 `test_guided_init_existing_harness_can_exit_without_overwriting_assets`，断言 `维护建议（Maintenance triage guidance）` 和 `推荐动作快捷选择` 出现在 `质量门禁信号（Benchmark signals）` 之前。
   - 断言新增 `审计明细（Audit signals）` 文案出现在 raw signals 之前。
   - 断言 guidance / shortcuts 不重复输出。
   - 保留 raw section 和只读 exit 断言。

2. 实现
   - 调整 `_handle_existing_harness_entry()` 的渲染顺序。
   - 在 raw signals 前新增一行中文审计说明。
   - 删除原先 raw signals 后面的 guidance / shortcuts 输出块，避免重复。

3. 文档
   - 更新 `README.md` 的已有 Harness 维护入口段落，说明先展示 maintenance guidance / shortcuts，再展示 raw audit signals。
   - 更新 `docs/engineering/init-workflow.md` 中 existing Harness 入口规则。
   - 更新 `docs/evolution-log.md` 记录本轮 Gap Analysis、验收和 Gate。

4. 验证
   - 运行 targeted guided init integration。
   - 运行相关 existing harness unit / integration 切片。
   - 运行 `python -m compileall src tests` 和 `git diff --check`。
   - commit 前运行 `scripts/test-fast.sh`。
