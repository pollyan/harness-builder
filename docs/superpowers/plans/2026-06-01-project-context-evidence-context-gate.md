# Project Context Evidence Context Gate 迁移计划

## Milestone

作为 Harness Maintainer，当我运行 `init` 或 `benchmark` 审查一个刚生成的 Harness 时，我可以在 `.ai/guides/project-context.md` 看到扫描来源证据和 LLM evidence expansion 的 requested/read paths、risk focus、confidence 与 rationale，并且 `benchmark-report.yaml` 会用 `content:project-context-evidence-context` 防止这些证据上下文从 Guide 中丢失，从而让我能审计系统为什么深入读取了这些文件、哪些路径支撑了项目理解。

## TDD 步骤

1. 先补 `tests/unit/test_write_assets.py`：
   - 构造 inventory 时加入 `documents`、`configs`、`ci_files` 和 `scan_metadata.evidence_expansion`。
   - 断言 `project-context.md` 包含 `## LLM 证据扩展`、requested/read path、risk focus、confidence、read_file_count、rationale，以及来源证据中的 document/config/CI path。
2. 再补 `tests/integration/test_benchmark_command.py`：
   - 生成成功报告时包含 `content:project-context-evidence-context`。
   - 增加 helper 写入一致的 evidence expansion context。
   - 增加缺失 evidence path、缺失 LLM section、缺失 requested/read path 或 rationale 的负向断言。
3. 运行 targeted tests，确认新测试先失败。

## 实现步骤

1. 更新 `src/harness_builder_agent/tools/asset_writers/guides.py`：
   - 把 `_guide()` 的来源证据构造改为 helper，合并 `inventory.evidence`、`documents`、`configs`、`ci_files`。
   - 在 `project-context` 中加入 `## LLM 证据扩展`。
   - 从 `stack_extensions["scan_metadata"]["evidence_expansion"]` 渲染 requested/read paths、risk focus、confidence、read_file_count、rationale；缺失时渲染 `evidence_expansion=not_run`。
2. 更新 `src/harness_builder_agent/tools/benchmark.py`：
   - 在 `_content_checks()` 中加入 `_project_context_evidence_context_check()`。
   - 校验 `## 来源证据` 和 `## LLM 证据扩展` 稳定章节。
   - 校验 inventory evidence/doc/config/CI 路径、evidence expansion requested/read paths、risk focus、confidence、rationale。
   - 返回 `missing` 列表和 `evidence_path_count`。
3. 更新文档：
   - `README.md`、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/sensor-and-gate-rules.md`。
   - `docs/todos/local-unique-capability-migration.md` 标记该切片已迁移，并保留 scan-report/init-summary evidence visibility 为后续。
   - `docs/evolution-log.md` 追加本轮记录。

## 验证步骤

1. `scripts/test-unit.sh tests/unit/test_write_assets.py -q`
2. `scripts/test-integration.sh tests/integration/test_benchmark_command.py -q`
3. `git diff --check`
4. `scripts/test-fast.sh`

## Commit

- 本地 commit message：`迁移项目上下文证据门禁`
- 本轮属于迁移工作包中的一个独立切片，但整个 todo 尚未完成；完成后只本地提交，不 push。
