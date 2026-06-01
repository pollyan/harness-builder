# Init Completion 下一步动作去重实施计划

## 目标

让首次 `init` 完成摘要的 `建议下一步` 保持行动优先且不重复：基础 benchmark / failed check / human-input 治理动作排在前面，成熟度建议只补充不同语义的下一步。

## 实施步骤

1. TDD：更新 `tests/unit/test_init_summary.py`：
   - 修改 completion happy path 断言，证明 benchmark 建议不重复，第三条来自 distinct maturity step。
   - 修改 failed benchmark 断言，证明 failed-report 处理动作不会再跟重复 benchmark 建议同时出现。
   - 增加或调整 score fixture，让测试能区分重复和非重复 maturity recommended next steps。
2. TDD：更新 guided init integration transcript 断言：
   - `建议下一步` 包含 benchmark 第一动作和 human-input 第二动作。
   - 不再断言重复 benchmark 建议。
3. 实现 `_completion_next_action_lines()` 的语义去重：
   - 为基础治理动作和 maturity recommended next steps 生成轻量 action key。
   - 已加入 benchmark / failed benchmark key 后，跳过同类 maturity 建议。
   - 保持最多 3 条，保留 distinct maturity 建议。
4. 运行 targeted unit，先确认 RED，再实现到 GREEN。
5. 运行 targeted integration completion 测试，确认真实 guided transcript 不再重复。
6. 更新 `docs/evolution-log.md`，记录本轮 Gap Analysis、用户故事、取舍、验证结果和 Self-Harness Gate。
7. 运行 `git diff --check` 和 `scripts/test-fast.sh`。
8. 创建中文本地 commit；本轮是小型体验修正，不单独 push。

## 验证命令

```bash
.venv/bin/python -m pytest tests/unit/test_init_summary.py -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_restates_user_supplements_before_write_and_persists_them -q
git diff --check
scripts/test-fast.sh
```

## 非目标

- 不修改 `init-summary.md` 的长期 Markdown 章节。
- 不修改 maturity report 原始 recommended next steps。
- 不修改 benchmark report schema、questionnaire schema 或 human-input governance。
- 不压缩 completion summary 的资产概览。
- 不执行 benchmark，不创建 Runtime 产物，不推送远端。
