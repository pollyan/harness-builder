# Guided Init 团队规则影响与预览实施计划

## 用户故事

作为 Harness Maintainer，当我在 guided `init` 中输入团队代码规范、架构约束或测试策略时，我可以在进入候选审查前立即看到系统如何理解这些规则、它们会进入哪些 Harness 资产，并在写入前设计预览中看到这些规则作为 Guides / human-input-needed / 后续审查的约束，从而确认团队隐性规则已经进入本次 Harness 设计，而不是只在最终确认阶段被动记录。

## 实施步骤

1. 先写失败测试：
   - 扩展 `tests/integration/test_init_on_fixture_projects.py::test_guided_init_records_scan_notes_and_team_rules_in_assets`。
   - 断言团队规则输入后、`建议生成的规则` 前出现 `团队规则理解` 和 `团队规则影响`。
   - 断言写入前 preview 中出现 `团队规则约束`，包含具体规则和 Guides / human-input-needed / Workflow policy 边界。
   - 保留现有 decisions、project-context 和 workflow note 持久化断言。

2. 实现即时反馈：
   - 在 `interactive_init.py` 新增 `_show_team_rules_immediate_summary(inline_contexts)`。
   - 在首次 `_collect_team_rules()` 后立即调用；在 final summary `back -> rules` 重新收集后也立即调用。
   - 无团队规则时不输出新区块。

3. 实现 preview 可见性：
   - 扩展 `_show_prewrite_maturity_preview(..., inline_contexts)`。
   - 在 `写入前 Harness 设计预览` 中加入 `团队规则约束` 小节。
   - 有团队规则时列出前若干条，并说明进入 Guides / human-input-needed / 后续审查；无规则时提示当前按扫描证据和内置基线生成。

4. 更新文档：
   - `docs/engineering/init-workflow.md` 补充团队规则输入后的即时复述和写入前预览规则。
   - `docs/evolution-log.md` 追加本轮记录。

5. 验证：
   - 运行目标 integration 测试。
   - 运行相关 guided init tests。
   - 提交前运行 `scripts/test-fast.sh`。

## 预期修改文件

- `src/harness_builder_agent/tools/interactive_init.py`
- `tests/integration/test_init_on_fixture_projects.py`
- `docs/engineering/init-workflow.md`
- `docs/evolution-log.md`
- `docs/superpowers/specs/2026-06-01-guided-team-rules-impact-preview-design.md`
- `docs/superpowers/plans/2026-06-01-guided-team-rules-impact-preview.md`

## 验证命令

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_records_scan_notes_and_team_rules_in_assets -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_init_default_guided_mode_accepts_happy_path tests/integration/test_init_on_fixture_projects.py::test_guided_init_records_scan_notes_and_team_rules_in_assets tests/integration/test_init_on_fixture_projects.py::test_guided_init_restates_user_supplements_before_write_and_persists_them tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_team_rules -q
scripts/test-fast.sh
```

## Commit

- commit message：`增强团队规则影响预览`
