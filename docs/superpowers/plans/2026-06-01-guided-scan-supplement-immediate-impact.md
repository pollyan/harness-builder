# Guided Init 扫描补充即时影响说明实施计划

## 用户故事

作为 Harness Maintainer，当我在首次 guided `init` 的扫描理解阶段补充自然语言说明或结构化 `module` / `command` / `risk` 修正时，我可以在进入团队规则和设计候选前立即看到 Harness Builder 如何理解这些补充、会如何影响成熟度缺口判断和后续 Harness 推荐，从而确认交互输入已经进入决策链路，而不是只在最终确认阶段被动展示。

## 实施步骤

1. 先写失败测试：
   - 修改 `tests/integration/test_init_on_fixture_projects.py::test_guided_init_structured_scan_corrections_update_modules_commands_and_risks`。
   - 输入同时包含自然语言 note、`module=...`、`command=...`、`risk=...`。
   - 断言 `扫描补充理解` 和 `扫描补充影响` 出现在 `你的补充或修正` 之后、`\n团队规则` 之前。
   - 断言区块包含 note、module path、command、risk path/reason，以及 maturity / Guides / Sensors / Workflow / human-input-needed 影响说明。

2. 实现 CLI helper：
   - 在 `interactive_init.py` 增加 `_show_scan_supplement_immediate_summary()`。
   - 复用 `GuidedScanOverrides`，按自然语言 note、primary stack、modules、commands、risk_areas 分组输出。
   - 在首次 scan supplement 和 back-to-scan 修改后，`_apply_scan_overrides()` 之后立即调用该 helper。

3. 保持现有契约：
   - 不改 `InteractionDecisions` schema。
   - 不改 `ProjectInventory` / `CommandCatalog` schema。
   - 不改 final confirmation 的 `_show_supplement_impact_summary()`，避免丢失最终汇总。

4. 更新长期规则与演进记录：
   - `docs/engineering/init-workflow.md` 补充：首次 guided `init` 收到 scan 补充后，必须在进入团队规则和候选设计前立即复述理解和影响。
   - `docs/evolution-log.md` 追加本轮中文记录，包含 Gap Analysis 摘要、决策、sub agent 状态、验证和 Gate。

5. 验证：
   - 先运行目标 integration 测试。
   - 再运行 `scripts/test-fast.sh`。
   - 本轮只本地 commit；push 仍需等待 `scripts/test-full.sh` 满足 DeepSeek key 和真实 `.benchmarks` 先决条件。

## 预期修改文件

- `src/harness_builder_agent/tools/interactive_init.py`
- `tests/integration/test_init_on_fixture_projects.py`
- `docs/engineering/init-workflow.md`
- `docs/evolution-log.md`
- `docs/superpowers/specs/2026-06-01-guided-scan-supplement-immediate-impact-design.md`
- `docs/superpowers/plans/2026-06-01-guided-scan-supplement-immediate-impact.md`

## 验证命令

```bash
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_structured_scan_corrections_update_modules_commands_and_risks -q
scripts/test-fast.sh
```

## Commit

- commit message：`增强扫描补充即时影响说明`
