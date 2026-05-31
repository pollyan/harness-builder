# 扫描后成熟度初评前置设计

## 背景

`docs/strategy/init-north-star.md` 要求首次 guided `init` 在扫描理解展示之后，立即把扫描结果放进 L0-L4 成熟度框架中解释，再让用户补充或修正关键判断。当前实现已经有写入前成熟度预览，但它发生在团队规则、候选审查和 Workflow 展示之后。用户在“扫描发现 -> 你的补充或修正”阶段还看不到当前扫描会如何影响成熟度、阻断项和下一步推荐。

本轮处于用户授权的全自动目标模式：Superpowers brainstorming 原始流程要求等待用户确认，但本目标明确要求不要把用户确认作为常规节点。因此本 spec 记录 assumptions / decisions / risks 后直接进入 plan 与 TDD。

## Current State Gap Analysis

候选 gap 排序：

1. **扫描后成熟度初评前置**
   - 目标态：扫描结果展示后、用户补充前，CLI 用 L0-L4 语言解释当前从 L0 起步、如果按当前扫描写入会建立什么基线、下一等级缺什么、哪些用户补充会影响判断。
   - 当前能力：`_show_prewrite_maturity_preview()` 只在最终确认前展示，用户补充 scan 前看不到成熟度语义。
   - 缺口：用户输入仍主要围绕扫描字段修正，而不是围绕成熟度缺口和 Harness 推荐可信度补充。
   - 价值：让用户在最关键的扫描修正阶段知道“为什么这些补充重要”，提升渐进式协作质量。
   - 风险 / 复杂度：低到中；复用现有 `build_maturity_report()`、`select_weapon_library()` 和 `HarnessConfig.default()`，只改 guided CLI 渲染，不改产物 schema。
   - 可测试性：高；guided integration 可断言阶段顺序和文案，unit 可覆盖 helper 输出较少但不必新增 schema。
   - 依赖项：无外部服务；不需要真实 LLM。
   - 验收方式：integration transcript 顺序、非交互边界、文档规则。
2. **写入后 CLI 交付摘要与 `init-summary.md` 深度对齐**
   - 目标态：CLI completion message 像交付报告，包含生成结果、最值得先看的文件、未运行 benchmark 和人工确认项。
   - 当前能力：已有成熟度、阻断项、下一步、benchmark readiness 和入口文件，但首行仍偏英文文件路径，人工确认摘要较弱。
   - 价值：写入后体验更完整，但它发生在用户已确认写入之后，不能改善扫描修正阶段。
   - 风险 / 复杂度：低；可作为后续切片。
3. **生成资产更仓库特异化**
   - 目标态：Guides / Sensors 更充分消费用户补充的风险、模块、命令和成熟度缺口。
   - 当前能力：project-context、verification、test-strategy 已消费部分事实和用户补充。
   - 价值：高，但涉及多个 writer、benchmark 内容检查和 asset 断言，范围更大。

本轮选择第 1 项，因为它直接服务 `init` North Star 的“扫描理解 -> 成熟度诊断 -> 用户补充 -> 后续推荐”链路。

## 用户故事

作为 Harness Maintainer，当我首次 guided `init` 扫描一个遗留仓库并准备补充或修正扫描理解时，我可以先看到基于当前扫描结果的 L0-L4 成熟度初评、下一等级差距和会影响判断的补充方向，从而知道应该优先确认哪些模块、命令、风险或团队规则，避免在不了解成熟度影响的情况下盲目回答。

## 范围

包含：

- 在首次 guided `init` 的“扫描发现”之后、“需要你补充或修正的地方”之前展示“扫描后的成熟度初评”。
- 初评复用当前内存中的 `inventory`、`commands`、`HarnessConfig.default()` 和当前技术栈的 `weapon_selection` 计算 planned maturity。
- 文案必须先讲 L0-L4：当前从 L0 起步、按当前扫描写入后预计建立的基线、下一目标、主要差距。
- 文案必须说明用户补充会影响成熟度判断和后续 Harness 推荐，例如模块边界、hard gate 命令、风险区域、团队规则。
- 非交互 `--non-interactive` 不输出该 guided transcript。
- 更新 `docs/engineering/init-workflow.md` 和 `docs/evolution-log.md`。

不包含：

- 不改变 `maturity-score.yaml` schema。
- 不改变 `build_maturity_report()` 评分规则。
- 不新增 LLM prompt 或真实 LLM 调用。
- 不改变 Guide / Sensor 正式资产内容。
- 不把该前置初评伪装成已写入成熟度；它只是“基于当前扫描的写入前预测”。

## 设计

新增 helper：

```python
def _show_scan_maturity_snapshot(repo: Path, inventory: ProjectInventory, commands: CommandCatalog) -> None:
    weapon_selection = select_weapon_library(inventory, commands)
    planned = build_maturity_report(
        ai=None,
        inventory=inventory,
        commands=commands,
        config=HarnessConfig.default(),
        weapon_selection=weapon_selection,
    )
    ...
```

展示结构：

- `扫描后的成熟度初评`
- `当前从 L0 起步...`
- `按当前扫描写入后预计建立：<planned.overall_level> 基线`
- `下一目标：<planned.target_next_level>`
- `主要差距`：取 `planned.blocking_reasons[:3]`
- `建议优先补充`：固定把成熟度影响翻译为用户可回答的问题
  - 真实 hard gate / soft gate 命令。
  - 模块边界、入口目录和职责。
  - 高风险路径、权限 / 数据 / 配置变更区域。
  - 团队规范、架构边界和测试策略。

调用位置：

```python
_show_scan_findings(inventory, commands)
_show_scan_maturity_snapshot(repo, inventory, commands)
scan_overrides = _collect_scan_supplement(inventory)
```

后续 `_show_prewrite_maturity_preview()` 保留不变，用于用户补充、候选审查和 workflow 展示后的最终写入前设计预览。这样形成两次不同语义：

- 扫描后初评：帮助用户决定要补什么。
- 写入前预览：帮助用户决定是否写入。

## Assumptions / Risks

- 当前没有完整 `.ai/project-inventory.json` 和 `.ai/harness-config.yaml` 时，首次 init 均按 L0 起步解释；如果存在部分 `.ai` 资产但未构成完整 Harness，后续可扩展为 L1 起步提示。
- `build_maturity_report(ai=None, ...)` 表达的是“如果写入本轮基线后的 planned maturity”，不是目标仓库当前工程质量。
- 该前置初评不落盘；正式机器契约仍由写入后的 `maturity-score.yaml` 和 `maturity-evidence.yaml` 承担。
- 如果后续用户修正扫描结果，最终写入前成熟度预览仍会用修正后的 inventory / commands 重新计算。
- Push 前真实 RuoYi-Vue acceptance 可能暴露与本轮 UI 改动无关的 LLM 契约问题；如果问题来自 LLM evidence plan 违反 allowlist，允许补一次显式契约修正重试，但不能放宽 allowlist、自动纠正路径或 fallback 到确定性扫描成功。

## 验收标准

1. guided init happy path 在 `扫描发现` 之后、`需要你补充或修正的地方` 之前输出 `扫描后的成熟度初评`。
2. 该区域包含 L0-L4 主线信息：`当前从 L0 起步`、`按当前扫描写入后预计建立`、`下一目标`、`主要差距`。
3. 该区域说明用户补充会影响成熟度判断和后续 Harness 推荐，至少提到 hard gate 命令、模块边界、风险区域和团队规则 / 测试策略。
4. 用户在最终确认前仍能看到原有 `当前 Harness 成熟度初评` / `写入前 Harness 设计预览`，证明前置初评没有替代写入前预览。
5. `--non-interactive` 输出不出现 `扫描后的成熟度初评`。
6. 现有 guided init、scan unit、fast regression 通过；push 前 full regression 通过。
