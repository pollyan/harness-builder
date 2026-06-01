# Guided Scan Back Candidate Review Reset 计划

## 用户故事

作为 Harness Maintainer，当我在首次 guided `init` 的最终确认阶段返回 scan 修改扫描理解后，我可以看到候选审查决策已随 scan 状态刷新而清空，并且最终写入不会把上一版 scan 状态下的 accept / reject / edit 决策静默套用到当前候选，从而相信“返回修改”真的只使用当前生效的扫描理解和审查状态。

## 验收标准

- `back -> scan` 后 CLI 提示候选项已刷新、上一轮候选审查决策已清空，并说明可通过 `back -> candidates` 重新审查。
- 最终 `interaction-decisions.yaml` 不保留 scan 修改前的 candidate accept / reject / edit 决策；当前候选默认为 `kept`。
- `.ai/experience/weapon-library-candidates.yaml` 不因旧决策出现 `confirmed`、`rejected` 或旧 `decision_notes`。
- 不修改 schema、LLM、benchmark、Runtime 分工。
- targeted integration、candidate review regression、compileall、diff check 和 fast regression 通过。

## 步骤

1. 新增 guided init integration RED test：
   - 初次候选审查输入 `a` / `r` / `e`。
   - 最终确认输入 `back -> scan` 修改 scan supplement。
   - 直接 `confirm`。
   - 断言旧 candidate 决策不会进入最终产物。
2. 修改 `run_guided_init()`：
   - `action == "scan"` 重算 candidate report 后清空 `candidate_decisions`。
   - 输出清空提醒。
3. 如有必要，抽一个小 helper 渲染候选审查重置提示，保持主流程可读。
4. 更新 `docs/evolution-log.md`。
5. 运行 targeted tests：
   - 新增 integration test。
   - 相关 scan back tests。
   - candidate review test 或完整 guided integration。
6. 运行 `compileall`、`git diff --check`、`scripts/test-fast.sh`。
7. 本地提交。
8. 执行 `scripts/test-full.sh` 作为 push gate；若仍缺外部 acceptance 前置则不 push。

## Self-Harness Gate 检查点

- `docs/engineering/init-workflow.md` 是否需要增加稳定规则：返回 scan 后清空候选审查决策。
- `README.md` 是否需要更新：该细节属于 guided back 行为，若只在工程规则中沉淀即可不更新 README。
- `docs/todos/` 是否需要新增：预计不需要，本轮直接处理上一轮 Gate 候选。
- 是否存在相关后续 gap：自动重审 candidates、返回 scan 后 refresh 更多 review-only 候选上下文，留作下一轮候选而不是当前扩大。
