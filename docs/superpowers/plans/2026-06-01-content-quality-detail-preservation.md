# Content Quality Detail Preservation 迁移计划

## Milestone

作为 Harness Maintainer，当我运行 `benchmark` 发现 Guide、Sensor、Workflow Skill 或 stack-specific Guide 内容质量失败时，我可以在 `benchmark-report.yaml` 中看到具体缺失章节、缺失 workflow skill marker 或缺失 weapon id，从而知道应该修哪份语义资产，而不是只看到 `passed=false`。

## TDD 步骤

1. 更新 `tests/integration/test_benchmark_command.py`：
   - `test_benchmark_content_checks_fail_when_guide_required_sections_are_missing` 断言 `content:guides-quality.missing` 包含缺失章节，`content:stack-specific-guides.missing` 包含缺失 weapon id。
   - `test_benchmark_content_checks_fail_when_workflow_skill_file_is_missing` 断言 `content:workflow-skills.missing` 包含缺失 standard skill。
   - 新增 sensor required section 缺失测试，断言 `content:sensors-quality.missing` 包含缺失章节或 hard marker。
2. 先运行 targeted tests，确认新断言失败。

## 实现步骤

1. 更新 `src/harness_builder_agent/tools/benchmark.py`：
   - `_workflow_skills_check()` 返回 missing list。
   - `_guide_quality_check()` 返回 missing list。
   - `_sensor_quality_check()` 返回 missing list。
   - `_stack_specific_guide_check()` 返回 missing list。
2. 更新文档记录：
   - `docs/todos/local-unique-capability-migration.md` 记录 content quality check detail preservation 已迁移。
   - `docs/evolution-log.md` 追加本轮记录。

## 验证步骤

1. `scripts/test-integration.sh tests/integration/test_benchmark_command.py -q`
2. `git diff --check`
3. `scripts/test-fast.sh`

## Commit

- 本地 commit message：`迁移内容质量失败详情`
- 本轮仍属于迁移工作包中的一个切片；todo 尚未整体结束，不 push。
