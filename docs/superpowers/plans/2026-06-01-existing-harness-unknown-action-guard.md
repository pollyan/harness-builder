# Existing Harness 维护动作未知输入保护计划

## 用户故事

作为 Harness Maintainer，当我再次运行 guided `init` 进入已有 Harness 维护入口并误输入不存在的维护动作时，我可以看到明确的未知输入提示并重新选择有效菜单项，从而不会把一次 typo 静默记录成有意退出，也不会误以为推荐维护动作已经执行。

## 步骤

1. 增加失败测试
   - 在 existing Harness integration 中新增未知维护动作测试。
   - 输入 `not-a-real-action` 后再输入 `1`。
   - 断言当前 RED：旧实现直接默认退出，缺少重新提示。

2. 实现未知输入保护
   - 在 `existing_harness_actions.py` 增加 `is_existing_harness_action()`。
   - `_handle_existing_harness_entry()` 对维护动作 prompt 增加循环校验。
   - 未知输入输出有效动作提示并重新等待。
   - `run_existing_harness_action()` unknown fallback 改为显式失败，防止绕过 prompt 的调用 silent fallback。

3. 更新长期规则与演进记录
   - `docs/engineering/init-workflow.md` 增加未知维护动作必须重新提示、runner 必须显式失败的规则。
   - `docs/evolution-log.md` 记录本轮 gap、取舍、验证和 Gate。

4. 验证与提交
   - targeted existing Harness integration。
   - 完整 guided init integration。
   - `compileall`、`git diff --check`、`scripts/test-fast.sh`。
   - 创建中文本地 commit。
   - push 前评估 `scripts/test-full.sh`；若 DeepSeek 外部 evidence 发送仍未获授权，不 push。
