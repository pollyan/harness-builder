# 写入前 Workflow Skills 预览实施计划

目标：在首次 guided `init` 的写入前 Harness 设计预览中展示将生成的 Workflow Skills，以及它们与 routing rule、Guides、Sensors 的关系。

## Steps

1. 红测：unit / integration
   - 修改 `tests/unit/test_interactive_init_preview.py`，断言 preview 输出 `将生成的 Workflow Skills`、三个 Skill 路径、关键 stage、routing rule、引用 Guides / Sensors。
   - 修改相关 guided init integration，断言终端预览包含 Workflow Skills section 和 `standard` Skill 路径。
   - 先运行目标测试，确认当前 preview 缺少该 section 导致失败。

2. 实现
   - 修改 `src/harness_builder_agent/tools/prewrite_preview.py`。
   - 新增 `_show_workflow_skills_preview(config)`，从 `config.workflows` 和 `config.workflow_routing.rules` 渲染用户可读 preview。
   - 控制输出长度：stage、Guide、Sensor 只展示前几项，避免完整 YAML 展开。

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
