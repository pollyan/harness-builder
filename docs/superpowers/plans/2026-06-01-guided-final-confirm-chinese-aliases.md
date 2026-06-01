# Guided Final Confirm Chinese Aliases 计划

## 用户故事

作为 Harness Maintainer，当我在中文 guided `init` 的最终确认阶段准备写入或返回修改时，我可以直接输入 `确认`、`返回`、`取消`，并在返回修改时输入 `扫描`、`团队规则`、`候选` 或 `工作流` 选择目标，从而不必在中文界面记住英文控制词，同时仍保留英文命令和未知输入保护。

## 步骤

1. 增加失败测试
   - 在 guided init integration 中覆盖中文 `确认` 能完成写入。
   - 覆盖中文 `返回 -> 团队规则 -> 确认` 能替换团队规则并写入资产。
   - 先运行 targeted pytest，记录 RED。

2. 实现控制词归一化
   - 在 `interactive_init.py` 为最终确认动作和返回目标增加别名字典与归一化 helper。
   - 更新最终确认 prompt、返回目标 prompt 和未知输入提示。
   - 保留未知输入继续 reprompt，不允许 silent confirm。

3. 更新长期文档与演进记录
   - `docs/engineering/init-workflow.md` 写入最终确认支持中英文控制词的稳定规则。
   - `README.md` 同步用户可见 init 流程说明。
   - `docs/evolution-log.md` 记录本轮 gap、决策、验收和 Gate。

4. 验证与提交
   - 运行新增 targeted tests。
   - 运行完整 guided init integration 切片。
   - 运行 `compileall`、`git diff --check`、`scripts/test-fast.sh`。
   - 创建本地 commit。
   - push 前运行 `scripts/test-full.sh`；如果外部 acceptance 前置缺失导致失败，记录原因且不 push。
