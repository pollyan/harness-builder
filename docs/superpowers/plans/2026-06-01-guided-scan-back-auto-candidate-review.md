# Guided Scan Back 自动候选复核计划

## 用户故事

作为 Harness Maintainer，当我在首次 guided `init` 的最终确认阶段返回 `scan` 修改扫描理解后，我可以立即重新审查基于新扫描状态刷新的 Guide / Sensor 候选，并让最终 `.ai` 产物只记录这次新审查的决策，从而不会因为旧决策被清空后忘记再次进入候选审查而把候选默认保持。

## 步骤

1. 增加失败测试
   - 在 guided init integration 中新增或调整 `back -> scan` candidate 测试。
   - 输入第二轮候选复核的 `a/r/e` 决策，先证明当前实现不会自动进入第二轮复核。
   - 断言 transcript 有两次“逐项审查模型候选”、最终决策来自第二轮且旧备注不进入产物。

2. 实现 scan back 后自动候选复核
   - 修改 `run_guided_init()` 的 `action == "scan"` 分支。
   - 刷新 `candidate_report` 后清空旧决策并输出刷新边界。
   - 候选非空时立即调用 `_review_candidates(...)`。
   - 调整候选刷新提示文案。

3. 更新稳定文档与过程记录
   - 更新 `docs/engineering/init-workflow.md` 的 scan back candidate 规则。
   - 如 README 的用户说明需要同步，补一句 scan back 会重新审查候选。
   - 更新 `docs/evolution-log.md` 记录本轮 gap、取舍、验证和 Gate。

4. 验证与提交
   - 跑相关 targeted integration。
   - 跑完整 guided init integration。
   - 跑 `compileall`、`git diff --check`、`scripts/test-fast.sh`。
   - 创建中文本地 commit。
   - push 前评估 `scripts/test-full.sh`；若外部 DeepSeek 数据外发仍未获授权，不 push。
