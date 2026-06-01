# Guided Scan Presentation Renderer 抽取计划

目标：把首次 guided `init` 的扫描呈现 helper 从 `interactive_init.py` 抽到独立模块，保持用户行为不变，并增加 direct unit 覆盖。

## 实施步骤

1. 写 RED 测试
   - 新增 `tests/unit/test_guided_scan_presentation.py`。
   - 覆盖 `show_llm_evidence_expansion()` 的低置信度输出。
   - 覆盖 `risk_attention_lines()` / `uncertainty_attention_lines()` / `verification_gap_lines()` 的关键文案。
   - 覆盖 `show_scan_maturity_snapshot()` 的 L0 起步和预计基线输出。
   - 覆盖 `guided_scan_progress()` 的 started / completed 文案。
   - 先运行 targeted unit，确认新模块不存在导致失败。

2. 新增 renderer 模块
   - 新增 `src/harness_builder_agent/tools/guided_scan_presentation.py`。
   - 搬迁 scan progress、scan findings、attention summary、LLM evidence expansion、followup questions、self-check、maturity snapshot、risk / uncertainty / verification / followup lines、stack label helper。
   - 只依赖 schema、maturity model、risk signals、weapon library、prewrite partial-harness helper 和 `typer.echo`。

3. 接入 `interactive_init.py`
   - 从新模块导入 public functions，并用原 `_show_*` / `_risk_*` / `_stack_*` 私有名称 alias。
   - 删除 `interactive_init.py` 中被搬迁的函数定义。
   - 保留 `_scan_repository_for_guided_init()` 与 scan execution / trace 逻辑在主向导文件中。

4. 验证行为不漂移
   - 运行 renderer unit。
   - 运行 guided init 相关 integration 切片：扫描进度、扫描关注点、LLM evidence expansion、followup / self-check、scan supplement。
   - 运行 `git diff --check`。

5. 记录与提交
   - 更新 `docs/evolution-log.md`。
   - 提交前运行 `scripts/test-fast.sh`。
   - 创建中文本地 commit；不 push。

## 非目标

- 不修改扫描决策、LLM prompt、schema、writer、benchmark 或 Runtime 边界。
- 不改变 CLI 文案和 transcript 语义。
- 不拆团队规则、候选审查、Workflow 补充或最终确认。
- 不推送远端；push 前 full regression 仍需要外部 acceptance 依赖。
