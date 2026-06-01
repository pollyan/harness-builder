# 写入前待确认边界预览实施计划

目标：在首次 guided `init` 的写入前 Harness 设计预览中汇总低置信度和待人工确认边界，让 Maintainer 在最终 `confirm` 前理解哪些判断仍需复核。

## Steps

1. 红测：unit / integration
   - 修改 `tests/unit/test_interactive_init_preview.py`，构造包含 `followup_questions`、`self_check.resolutions` 和低置信度命令的 inventory / command catalog，断言 preview 输出 `待确认与低置信度边界`、interaction id、action type、低置信度命令和不会自动关闭追问边界。
   - 修改相关 guided init integration，复用已有 scan follow-up mocked 流程，断言最终确认前 preview 也包含待确认边界 section。
   - 先运行目标测试，确认当前 preview 缺少该 section 导致失败。

2. 实现
   - 修改 `src/harness_builder_agent/tools/prewrite_preview.py`。
   - 新增 `_show_confirmation_boundary_preview(inventory, commands)`，从 scan metadata 和 command catalog 生成摘要。
   - 控制输出长度，最多展示少量 follow-up、自检 resolution、scan warning 和低置信度命令。

3. 目标验证
   - 运行新增 / 相关 unit。
   - 运行相关 guided init integration。
   - 运行 `python -m compileall -q src tests`。
   - 运行 `git diff --check`。

4. 文档记录
   - 更新 `README.md` 和 `docs/engineering/init-workflow.md` 的写入前 preview 描述。
   - 更新 `docs/evolution-log.md`，记录 Gap Analysis 摘要、用户故事、取舍、验证结果和 Self-Harness Gate。

5. 最终验证与提交
   - 运行 `scripts/test-fast.sh`。
   - 创建中文本地 commit。
   - 本轮不 push；除非后续形成完整工作包并完成 full regression。
