# Scan Evidence Failed Check Triage 迁移计划

## Milestone

作为再次运行 guided `init` 进入已有 Harness 维护入口的 Harness Maintainer，当最近 benchmark 因 `content:scan-report` 或 `content:init-summary` 失败时，我可以在 Benchmark signals 和 Maintenance triage guidance 中看到中文解释、具体 missing detail 和下一步动作，从而知道要补齐 scan-report / init-summary 的扫描证据审计，而不是只能打开 YAML 猜测失败含义。

## TDD 步骤

1. 更新 `tests/unit/test_interactive_init_preview.py`：
   - 构造 benchmark report，包含 `content:scan-report` 和 `content:init-summary` failed checks。
   - 断言 `_benchmark_signal_lines()` 输出专门中文 label，并保留 missing detail。
2. 更新 `tests/unit/test_maintenance_triage.py`：
   - 构造 `content:scan-report` 或 `content:init-summary` failed check。
   - 断言 top action reason 为 `scan_evidence_audit_incomplete`，source 指向具体 check，detail 为第一条 missing，guidance 说明补齐 scan evidence audit。
3. 先运行 targeted tests，确认新测试失败。

## 实现步骤

1. 更新 `src/harness_builder_agent/tools/interactive_init.py`：
   - 在 `_benchmark_failed_check_label()` 中增加 `content:scan-report` 和 `content:init-summary` 的中文解释。
2. 更新 `src/harness_builder_agent/tools/maintenance_triage.py`：
   - 新增 scan evidence failed check 识别 helper，覆盖 `content:scan-report` 和 `content:init-summary`。
   - 在 `build_maintenance_triage()` 中将其转换为专门 top action。
   - 在 `_maintenance_action_guidance()` 中增加中文处理建议。
3. 更新文档记录：
   - `docs/todos/local-unique-capability-migration.md` 标记 failed check detail preservation 的 scan evidence 小切片。
   - `docs/evolution-log.md` 追加本轮记录。

## 验证步骤

1. `scripts/test-unit.sh tests/unit/test_interactive_init_preview.py tests/unit/test_maintenance_triage.py -q`
2. `git diff --check`
3. `scripts/test-fast.sh`

## Commit

- 本地 commit message：`迁移扫描证据失败项分诊`
- 本轮仍属于迁移工作包中的一个切片；todo 尚未整体结束，不 push。
