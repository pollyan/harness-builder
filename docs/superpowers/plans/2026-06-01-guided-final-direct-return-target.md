# Guided Final Direct Return Target 计划

## 用户故事

作为 Harness Maintainer，当我在首次 guided `init` 的最终确认摘要中发现扫描、团队规则、候选或 Workflow 需要修改时，我可以直接输入对应目标 `扫描`、`团队规则`、`候选` 或 `工作流` 返回该部分，从而不必先输入 `返回` 再选择目标，也不会因为直接输入目标而触发未知输入。

## 步骤

1. 增加失败测试
   - 在 guided init integration 中新增直接输入 `候选` 的测试。
   - 断言当前会失败或无法进入候选复核，记录 RED。

2. 实现直接返回目标
   - 复用 `_normalize_final_back_stage()`。
   - `_confirm_summary()` 对非 confirm / back / cancel 的输入再尝试解析 stage。
   - stage 命中时返回对应 action 并输出 `返回修改`。
   - 更新 prompt 和未知输入提示。

3. 更新长期规则与演进记录
   - `docs/engineering/init-workflow.md` 增加最终确认可直接输入返回目标的稳定规则。
   - `docs/evolution-log.md` 记录本轮 gap、取舍、验证和 Gate。

4. 验证与提交
   - targeted integration。
   - guided init integration 切片。
   - `compileall`、`git diff --check`、`scripts/test-fast.sh`。
   - 创建中文本地 commit。
   - push 前评估 `scripts/test-full.sh`；若 DeepSeek 外部访问仍受限，不 push。
