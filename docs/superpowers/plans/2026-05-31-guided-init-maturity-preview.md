# Guided Init 写入前成熟度预览实施计划

## 目标

让首次 guided `init` 在写入 `.ai/` 前展示成熟度初评和 Harness 设计预览，帮助 Harness Maintainer 在最终确认前理解当前 L0 起点、写入后预计建立的基线、下一等级缺口，以及 Guides / Sensors / Workflow routing 如何补齐这些缺口。

## 约束

- 不新增 LLM 调用，不提前写入 `.ai/`。
- 预览只消费内存中的 `ProjectInventory`、`CommandCatalog`、默认 `HarnessConfig` 和 `WeaponLibrarySelection`。
- 输出面向用户，避免暴露 `overall_level`、`dimension_scores`、`primary_stack` 等内部字段名。
- 修改 `init` 主链路时，同步更新 integration 测试和工程文档。

## 实施步骤

1. 在 guided init integration 测试中增加写入前成熟度预览断言。
   - 验证 `当前 Harness 成熟度初评` 出现在 `最终确认` 前。
   - 验证首次仓库从 `L0` 起步。
   - 验证展示写入后预计基线、下一目标、阻断项、推荐补齐动作。
   - 验证展示 Guides、Sensors、Workflow routing，并包含 `standard` 高风险升级语义。
   - 验证不暴露内部 schema 字段名。

2. 在 `interactive_init.py` 中新增预览 helper。
   - 使用 `build_maturity_report(ai=None, inventory=..., commands=..., config=HarnessConfig.default(), weapon_selection=...)` 计算 planned baseline。
   - 明确区分“当前状态：L0，无项目级 `.ai` Harness”和“确认写入后预计建立：Lx”。
   - 展示前 3 条 blocker / next step；缺失时给出自然语言占位。
   - 展示前 3 条 Guide / Sensor 推荐和默认 workflow routing rule。

3. 将预览插入 guided init 的最终确认前。
   - 首次路径在 `_show_workflows()` 后、`_confirm_summary()` 前展示。
   - 用户从最终确认返回 scan 后，重新选择武器库和候选报告，使下一次预览基于更新后的 inventory / commands。

4. 更新文档。
   - `README.md` 说明 guided `init` 写入前会给出成熟度初评和设计预览。
   - `docs/engineering/init-workflow.md` 固化该流程约束。
   - `docs/evolution-log.md` 记录本轮用户价值、边界、测试和后续 gap。

5. 验证。
   - 先运行新增/相关 guided init integration 测试。
   - 再运行 `scripts/test-fast.sh` 后提交。
