# Init Completion 优先下一步实施计划

## 目标

让首次 `init` 的终端完成摘要在 `建议下一步` 中直接给出优先动作，避免 Maintainer 在 Benchmark 健康度、待人工确认和成熟度建议之间自行推断顺序。

## 实施步骤

1. TDD：在 `tests/unit/test_init_summary.py` 中补充断言：
   - benchmark 未运行时，`建议下一步` 第一项是运行 benchmark 命令。
   - benchmark failed 时，第一项是查看 `.ai/benchmark-report.yaml` 的 failed checks。
   - questionnaire 有问题时，`建议下一步` 包含 `.ai/human-input-needed.md#处理方式`。
2. TDD：在 guided init integration completion summary 断言中补充 benchmark 优先动作。
3. 实现 `_completion_next_action_lines(ai, score)`：
   - 先读取 benchmark report 状态。
   - 再读取 questionnaire 是否有待确认。
   - 最后补充 `score.recommended_next_steps`，最多 3 条，并做简单文本去重。
4. 将 `render_init_completion_message()` 的 `next_steps` 改为使用新 helper。
5. 更新 `docs/evolution-log.md` 记录本轮 Gap Analysis、用户故事、取舍、验证和 Gate。
6. 运行 targeted unit / integration、`git diff --check`、`scripts/test-fast.sh`。
7. 本地中文 commit；不 push。

## 验证命令

```bash
.venv/bin/python -m pytest tests/unit/test_init_summary.py -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_completion_message_summarizes_user_supplements -q
git diff --check
scripts/test-fast.sh
```

## 非目标

- 不修改 `.ai/init-summary.md` 的长期 Markdown 章节。
- 不修改 benchmark report schema 或 failed check 判定。
- 不修改 questionnaire schema 或 human-input governance。
- 不压缩 completion summary 的其他区块。
- 不执行 benchmark，也不创建 Runtime 产物。
