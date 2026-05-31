# Existing Harness Assess Action Plan

## 目标

把 `docs/todos/maturity-driven-init-wizard.md` 的下一步切片落地：已有 Harness 再次 guided `init` 时支持 `assess` 复评成熟度。

## 步骤

1. 新增 integration 测试
   - 生成一个 fixture Harness。
   - 保存 `project-inventory.json`、`harness-config.yaml`。
   - guided `init` 输入 `assess`。
   - 断言不重新扫描、不覆盖正式资产、刷新 maturity / init summary、trace 记录 action 和 artifacts。

2. 实现 summary 写入复用
   - 在 `init_summary.py` 增加写入 `.ai/init-summary.md` 的小 helper。
   - `asset_writers/reports.py` 改用该 helper，避免首次 init 和复评路径重复逻辑。

3. 接入已有 Harness 菜单
   - `interactive_init.py` 导入 `assess_maturity` 和 init summary helper。
   - 菜单增加 `assess`。
   - 用户选择后运行成熟度复评，记录 trace event/artifacts/summary，返回 `.ai`。

4. 更新文档
   - `docs/engineering/init-workflow.md` 记录已有 Harness 入口支持 `assess`。
   - `docs/todos/maturity-driven-init-wizard.md` 增加已完成切片说明。
   - `docs/evolution-log.md` 增加本轮演进记录。

5. 验证
   - 先运行新增 integration 测试，确认红绿。
   - 运行相关 init integration 测试。
   - commit 前运行 `scripts/test-fast.sh`。
