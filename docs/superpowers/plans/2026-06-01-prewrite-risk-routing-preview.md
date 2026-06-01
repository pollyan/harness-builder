# 写入前风险路由预览一致性实施计划

目标：让首次 guided `init` 的写入前 Workflow routing 预览使用正式 Harness config builder，并展示 scan / 用户补充风险路径会进入 `standard-escalation` 的 `risk_area:*` trigger。

## Steps

1. 红测：unit / integration
   - 修改 `tests/unit/test_interactive_init_preview.py`，在包含 `risk_areas` 的 preview case 中断言输出 `risk_area:frontend/package.json` 和风险升级说明。
   - 修改相关 guided init integration，在已有结构化 scan supplement case 中断言 prewrite preview 包含 `risk_area:frontend/package.json`，并断言最终 `harness-config.yaml` 也包含同一 trigger。
   - 先运行目标测试，确认当前 preview 缺少 risk trigger 导致失败。

2. 实现
   - 把正式 config 构造逻辑从 `write_assets.py` 抽到独立 helper，或让 preview 直接复用不会产生循环依赖的 builder。
   - 修改 `show_prewrite_maturity_preview()` 使用该 config 构造结果来计算 planned maturity 和渲染 Workflow routing。
   - 在 routing preview 中对 `risk_area:*` trigger 增加用户可读说明，避免只输出内部 trigger 字符串。

3. 目标验证
   - 运行新增 / 相关 unit。
   - 运行相关 guided init integration。
   - 运行 `python -m compileall src tests`。
   - 运行 `git diff --check`。

4. 文档记录
   - 更新 `docs/evolution-log.md`，记录 Gap Analysis 摘要、用户故事、取舍、验证结果和 Self-Harness Gate。
   - 评估 README / engineering docs 是否需要同步；如果只是实现既有 `init-workflow.md` 的预览契约，不新增长期规则。

5. 最终验证与提交
   - 运行 `scripts/test-fast.sh`。
   - 创建中文本地 commit。
   - 本轮不 push；除非后续形成完整工作包并完成 full regression。
