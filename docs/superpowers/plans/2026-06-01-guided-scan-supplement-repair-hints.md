# Guided Scan 结构化补充修正提示实施计划

## 目标

让 guided `init` 的 scan 补充解析在结构化片段格式错误时，不只说明“未进入结构化资产”，还给出用户可复制的正确格式示例。

## 步骤

1. TDD：更新 `tests/unit/test_guided_scan_supplements.py`
   - invalid `command=` 断言 `可用格式：command=ID|命令|类型(build/test/lint/typecheck/other)|gate(hard/soft)|来源|置信度(low/medium/high)`。
   - invalid `module=` / `risk=` 断言各自可用格式。
   - 新增 invalid `stack=` 断言可用 stack 值。
2. TDD：更新 `tests/integration/test_init_on_fixture_projects.py`
   - `test_guided_init_explains_invalid_structured_scan_correction_does_not_update_catalog` 断言 CLI immediate summary 和 `interaction-decisions.yaml` notes 都包含 command 可用格式。
3. 运行 targeted tests，确认 RED 失败来自缺少格式提示。
4. 实现 `src/harness_builder_agent/tools/guided_scan_supplements.py`
   - 增加每类结构化片段的可用格式常量。
   - 增加统一 invalid note helper，保留原有“未进入 ... 只作为自然语言补充保留”语义。
   - 四类 invalid fragment 复用 helper。
5. 同步文档
   - `README.md` 的 guided init 说明补充“并给出可用格式提示”。
   - `docs/engineering/init-workflow.md` 的 scan reconcile / 补充规则补充同一稳定行为。
6. 更新 `docs/evolution-log.md`
   - 记录 Gap Analysis 摘要、用户故事、取舍、验证结果、Self-Harness Gate。
7. 验证
   - `.venv/bin/python -m pytest tests/unit/test_guided_scan_supplements.py tests/integration/test_init_on_fixture_projects.py::test_guided_init_explains_invalid_structured_scan_correction_does_not_update_catalog -q`
   - `git diff --check`
   - `scripts/test-fast.sh`
8. 本地 commit
   - commit message：`补充扫描结构化输入修正提示`
   - 本轮不 push；push 仍以 full regression 通过和完整工作包边界为准。

## 非目标

- 不修改 LLM / Prompt / schema / benchmark。
- 不改变合法结构化补充的结构化生效逻辑。
- 不把自然语言补充当作结构化错误。
- 不执行 Runtime，不创建 `.ai/task-runs`。
