# Existing Harness Assess Action Design

## 背景

`docs/todos/maturity-driven-init-wizard.md` 要求 `init` 成为成熟度驱动的主入口。当前首次 `init` 已生成 `.ai/init-summary.md`，再次 guided `init` 也能识别已有 Harness 并提供 `exit` / `reinit`。剩余缺口是已有 Harness 的维护入口仍然偏只读，用户还需要记住底层 `assess` 命令才能刷新成熟度。

本轮选择最小纵切：在已有 Harness 的 guided `init` 菜单中接入 `assess` 动作。

## 目标

- 再次执行 guided `init` 检测到已有 `.ai` 时，展示 `assess` 动作。
- 用户选择 `assess` 后，复用现有成熟度评估能力刷新：
  - `.ai/maturity-score.yaml`
  - `.ai/maturity-report.md`
  - `.ai/maturity-evidence.yaml`
  - `.ai/init-summary.md`
- 本动作不重新扫描仓库、不调用 LLM、不覆盖正式 Guides、Sensors、Workflow Skills 或 `harness-config.yaml`。
- `init` trace 记录 `existing_harness_action: assess` 和刷新产物。

## 决策

- `assess` 是已有 Harness 维护菜单的第一个可写动作，因为它只刷新成熟度和证据摘要，风险低且能直接服务成熟度主线。
- 本轮不接入 `improve`、`benchmark`、候选治理或重新扫描更新建议；它们会作为后续切片。
- `--non-interactive` 语义不变，仍按自动化重新生成 Harness。
- `assess_maturity` 不应在已有 `project-inventory.json` 时触发扫描；测试会把 guided 入口中的 `scan_repository` 替换为失败函数来固定该边界。
- `.ai/init-summary.md` 必须随成熟度复评同步刷新，否则 CLI 完成摘要和推荐入口文件可能不同步。

## 验收标准

- Integration：先用 `init --non-interactive` 生成 Harness，再用 guided `init` 输入 `assess`，命令成功。
- 测试证明 `assess` 路径不调用 guided init 的扫描函数。
- 测试证明 `project-inventory.json` 和 `harness-config.yaml` 没有被覆盖。
- 测试证明 maturity 三件套和 `init-summary.md` 存在且包含稳定章节。
- 测试证明最新 init trace 为 `completed`，summary 包含 `existing_harness_action: assess`，artifacts 包含成熟度和 init summary 产物。
- 现有 `exit` / `reinit` 行为保持不变。

## 风险

- `assess_maturity` 当前有缺失 Harness 时自动扫描并写初始资产的兼容逻辑。本轮仅在已有 Harness 入口调用它，且入口已验证 `project-inventory.json` / `harness-config.yaml`，不会依赖该兼容路径。
- `init-summary.md` 刷新会写语义 Markdown。它是成熟度摘要，不是用户编辑的正式规则资产；该写入符合维护入口的复评语义。
