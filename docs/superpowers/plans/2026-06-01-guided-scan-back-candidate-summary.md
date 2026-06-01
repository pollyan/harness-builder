# Guided Scan Back Candidate Summary 计划

## 用户故事

作为 Harness Maintainer，当我在首次 guided `init` 最终确认阶段返回 scan 修改扫描理解后，我可以在下一次最终确认摘要中看到候选已刷新、旧决策已清空、当前仍有多少候选待重新审查且默认保持候选，从而不会把“候选决策 0 条”误解为“没有候选需要审查”。

## 步骤

1. 增加失败测试
   - 扩展 `test_guided_init_back_to_scan_resets_previous_candidate_decisions`。
   - 断言最终确认摘要中出现“待重新审查 3 条”和默认保持候选边界。
   - 先运行 targeted pytest，记录 RED。

2. 实现候选摘要
   - `_confirm_summary()` 增加 `candidate_count` 参数。
   - 从 `run_guided_init()` 传入 `len(candidate_ids)`。
   - 抽取或内联候选摘要渲染：有决策时保留现有统计；无决策但有候选时显示待复核数量；无候选时显示暂无候选。

3. 同步文档和演进记录
   - `docs/engineering/init-workflow.md` 沉淀返回 scan 后最终确认必须展示候选待复核状态。
   - 如用户可见 README 需要，补充最终确认摘要会说明刷新候选待复核边界。
   - `docs/evolution-log.md` 记录本轮 gap、决策、验收和 Gate。

4. 验证与提交
   - targeted integration。
   - guided init integration 切片。
   - `compileall`、`git diff --check`、`scripts/test-fast.sh`。
   - 创建中文本地 commit。
   - push 前运行 `scripts/test-full.sh`；如果仍缺 DeepSeek key 或真实 benchmark 仓库，不 push。
