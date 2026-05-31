# Guided Init 写入前推荐项成熟度关联设计

## 背景

`docs/strategy/init-north-star.md` 要求写入前 Harness 设计预览不仅展示会生成哪些 Guides / Sensors / Workflow Skills，还要说明每个推荐项对应哪个成熟度维度、解决哪个阻断项、预计帮助进入哪个下一阶段能力。当前 `_show_prewrite_maturity_preview()` 已展示 L0 起步、写入后预计基线、下一目标、主要阻断项、推荐补齐动作、将生成的 Guides / Sensors 和 Workflow routing，但 Guide / Sensor 条目仍只展示 `recommended_action`，用户无法逐项判断这些资产为什么服务成熟度提升。

本轮处于用户授权的全自动目标模式：过程文档记录 assumptions / decisions / risks，但不等待额外人工确认。

## Current State Gap Analysis

候选 gap 排序：

1. **写入前推荐项成熟度关联**  
   - 目标态：每个 Guide / Sensor 推荐都说明关联成熟度维度、解决阻断、下一阶段贡献。  
   - 当前能力：preview 有整体成熟度和整体 blockers，但推荐项缺少逐项关联。  
   - 价值：让 Harness Maintainer 在确认写入前理解资产不是模板堆叠，而是围绕 L0-L4 缺口建立基线。  
   - 风险/复杂度：低；可从现有 `MaturityReport` 和 weapon tags 推导，不改 schema。  
   - 可测试性：高；guided integration 可断言 CLI transcript。
2. **真正 scan 内部阶段 callback**  
   - 价值高，但会改 `scan_repository()` 签名并影响大量 monkeypatch 测试，适合后续独立切片。
3. **生成资产 Markdown 内逐项成熟度来源**  
   - 价值中高，但涉及多个 writer 和 benchmark 内容契约，范围大于本轮。

本轮选择第 1 项。

## 用户故事

作为 Harness Maintainer，当我在首次 guided `init` 写入 `.ai/` 前审查 Harness 设计预览时，我可以看到每个即将生成的 Guide / Sensor 推荐对应的成熟度维度、正在缓解的阻断项和下一阶段贡献，从而判断这套 Harness 是围绕当前仓库的成熟度缺口生成，而不是固定模板拼装。

## 范围

包含：

- 在写入前 `将生成的 Guides` 和 `将生成的 Sensors` 列表中，为每个展示的 weapon 增加成熟度关联说明。
- 说明使用中文标签：`关联成熟度`、`解决阻断`、`下一阶段贡献`。
- 基于 weapon kind / tags / gate 推导成熟度维度标签。
- 基于 `planned.dimensions` 读取对应 blocker 和 next level requirement，并翻译常见维度目标。
- 保持机器契约不变。
- 增加 guided integration 测试。

不包含：

- 不修改 `WeaponLibraryEntry` schema。
- 不修改 `maturity-score.yaml` 或 `weapon-library-selection.yaml` 结构。
- 不修改 asset writers 或 benchmark。
- 不让 recommendation 自动应用正式 policy。

## 设计

新增渲染 helper：

- `_show_weapon_preview_item(weapon, planned)`
- `_weapon_maturity_dimension_keys(weapon)`
- `_maturity_dimension_labels(keys)`
- `_weapon_blocker_summary(keys, planned)`
- `_weapon_next_lift_summary(keys, planned)`

维度推导规则：

- Guide 默认关联 `guides`。
- Guide 或 Sensor 若 tags 包含 `risk`、`auth`、`sql`、`config`、`review`，追加 `risk_control`。
- Sensor 默认关联 `sensors`。
- Sensor 若 gate 为 `hard` 或 tags 包含 `hard-gate`、`test`、`gap`，追加 `verification_sophistication`。

中文维度标签：

- `guides` -> `Guides 上下文`
- `sensors` -> `Sensors 验证`
- `risk_control` -> `Risk Control 风险控制`
- `verification_sophistication` -> `Verification 验证成熟度`

常见下一阶段贡献使用中文短句，避免直接暴露内部字段名或长英文 blocker。

## Assumptions / Risks

- 这是 preview 叙事增强，不代表成熟度评分模型变化。
- weapon tags 是内置库稳定线索，足以支持第一版维度映射；未来若增加更多 weapon，可补充映射。
- 对没有 blocker 的维度，展示“保持该维度基线并为后续 benchmark / Runtime 验证提供依据”。
- 不应直接展示 `dimension_scores`、`overall_level`、`primary_stack` 等机器字段名。

## 验收标准

1. guided init happy path 的写入前 preview 中，`将生成的 Guides` 下每个展示项包含 `关联成熟度`、`解决阻断`、`下一阶段贡献`。
2. guided init happy path 的 `将生成的 Sensors` 下每个展示项包含 `关联成熟度`、`解决阻断`、`下一阶段贡献`。
3. preview 至少展示 `Guides 上下文`、`Sensors 验证` 和 `Verification 验证成熟度` 三类中文维度标签。
4. CLI 不暴露 `dimension_scores`、`overall_level`、`primary_stack` 等机器字段名。
5. 相关 guided integration、`scripts/test-fast.sh` 和 push 前 `scripts/test-full.sh` 通过。
