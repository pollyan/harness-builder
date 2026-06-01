# 初始候选治理 Benchmark 契约实施计划

## 目标

让 benchmark 能正确理解初始 LLM Guide / Sensor 候选已经被 `review-initial-candidate` 治理后的状态，并校验 `.ai/review/weapon-candidate-governance.*` 作为可选 review-only artifact。

## 步骤

1. 失败测试
   - 在 `tests/integration/test_benchmark_command.py` 导入新的 `_weapon_candidate_governance_check`。
   - 添加 helper 写出合法的 `weapon-candidate-governance.yaml/.md`。
   - 添加测试证明 `accepted` 后的 `confirmed` candidate 不会让 `_llm_enhancement_checks()` 失败。
   - 添加测试证明合法 governance artifact 通过，未知 candidate / 状态不一致 / Markdown 缺章节会失败。
   - 添加完整 `run_benchmark()` 回归，证明候选治理后 benchmark 仍 passed 且不创建 `.ai/task-runs`。

2. 实现 benchmark 契约
   - 在 `benchmark.py` 引入 `WeaponCandidateGovernanceLog`。
   - 重写 `_llm_enhancement_checks()`：schema 通过后校验候选状态与 human confirmation 的一致性、Markdown id / status / boundary。
   - 新增 `_weapon_candidate_governance_check(ai)`：按可选 artifact 规则校验配对、schema、source report、candidate 引用、decision/new status/current report 状态一致性和 Markdown 章节。
   - 把新 check 加入 `_content_checks()`。

3. 文档同步
   - 更新 `README.md` 的 benchmark 描述，加入 `weapon-candidate-governance` 可选治理产物。
   - 更新 `docs/engineering/init-workflow.md` 和 `docs/engineering/sensor-and-gate-rules.md`，沉淀稳定 benchmark 规则。
   - 更新 `docs/evolution-log.md`，记录 Gap Analysis 摘要、用户故事、决策、验证结果和 Gate。

4. 验证
   - 先运行新增 / 相关 targeted tests，确认 RED -> GREEN。
   - 运行 `python -m compileall src tests`。
   - 运行 `git diff --check`。
   - commit 前运行 `scripts/test-fast.sh`。
   - 创建中文本地 commit；本轮不 push，除非后续形成完整可同步工作包并通过 full regression。
