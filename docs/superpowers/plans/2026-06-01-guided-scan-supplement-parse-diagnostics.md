# Guided Scan 补充解析诊断计划

目标：让首次 guided `init` 的扫描补充输入在结构化片段格式错误时显式说明未结构化生效，同时抽出可单测解析器。

## 实施步骤

1. 写 RED 测试
   - 新增 `tests/unit/test_guided_scan_supplements.py`。
   - 覆盖合法 `stack`、`module`、`command`、`risk` 混合输入。
   - 覆盖非法 `command=unit|mvn test|test|hard` 不生成 `CommandDefinition`，并产生中文诊断 note。
   - 覆盖自然语言补充不被误报为结构化错误。
   - 先运行 targeted unit，确认缺少新模块 / 新诊断导致失败。

2. 新增解析模块
   - 新增 `src/harness_builder_agent/tools/guided_scan_supplements.py`。
   - 提供 `parse_guided_scan_supplement(answer, current_stack, stack_resolver=None)`。
   - 返回 `GuidedScanOverrides`，合法片段保持现有 note 文案。
   - 对格式不完整或非法字段生成明确诊断 note，并保留原始片段作为自然语言补充边界。

3. 接入 guided init
   - 修改 `interactive_init.py` 的 `_collect_scan_supplement()`，保留当前 CLI 提示和 invalid stack 二次输入体验。
   - 将解析工作委托给新模块。
   - 确保 `_show_scan_supplement_immediate_summary()` 能展示诊断 note。

4. 文档与演进记录
   - 更新 `docs/evolution-log.md`，记录本轮 Gap Analysis 摘要、用户故事、取舍、验证结果、Self-Harness Gate。
   - 长期 README / engineering 文档已说明结构化修正格式和边界；本轮不新增稳定规则，除非实现过程中发现事实源冲突。

5. 验证
   - 运行 targeted unit：`./.venv/bin/python -m pytest tests/unit/test_guided_scan_supplements.py -q`。
   - 运行相关 guided scan supplement integration 切片。
   - 运行 `git diff --check`。
   - 提交前运行 `scripts/test-fast.sh`。

## 非目标

- 不修改 `.ai` schema、`interaction-decisions.yaml` schema 或 writer 契约。
- 不改变合法结构化补充的现有语义。
- 不修改 LLM scan、evidence planner、scan reconciler 或 benchmark。
- 不 push；当前 push gate 仍受本地 acceptance 外部依赖阻塞。
