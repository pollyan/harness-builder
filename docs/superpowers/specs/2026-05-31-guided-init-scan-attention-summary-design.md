# Guided Init 扫描关注点分组设计

## 背景

`docs/strategy/init-north-star.md` 要求首次 guided `init` 在扫描完成后，以用户能快速判断的方式展示技术栈、模块、验证能力、风险、不确定性和仍需补充的问题。当前 `_show_scan_findings()` 已展示技术栈、证据、模块和验证命令，但风险、不确定性和验证缺口仍分散在内部 `stack_extensions`、`CommandCatalog` 或后续资产中，用户在输入扫描补充前无法快速判断“我应该纠正哪里”。

本轮处于用户授权的全自动目标模式：过程文档记录 assumptions / decisions / risks，但不等待额外人工确认。

## Current State Gap Analysis

候选 gap 排序：

1. **扫描关注点分组展示**  
   - 目标态：扫描结果展示包含风险区域、不确定性、验证缺口和需要用户补充的问题。  
   - 当前能力：只展示技术栈、证据、模块、命令；风险和 scan warning 未形成明确 CLI 分组。  
   - 价值：直接提升首次 `init` 的判断和补充效率，服务 North Star 的“扫描结果友好呈现”和“与用户对齐扫描理解”。  
   - 风险/复杂度：低；只读消费已有字段，不改 schema / LLM / 写入契约。  
   - 可测试性：高；guided integration 可断言 CLI transcript。
2. **真正阶段化 scan callback**  
   - 目标态：`collect evidence -> LLM evidence plan -> expansion -> final LLM scan -> reconcile` 每阶段实时输出。  
   - 当前能力：已有扫描前/后提示，但 scan 内部仍是阻塞调用。  
   - 价值高但涉及 `scan_repository()` 签名和大量 monkeypatch 测试，适合作为后续切片。
3. **Guide / Sensor 推荐精确关联成熟度维度**  
   - 目标态：每个推荐说明补齐哪个成熟度维度、哪个 blocker。  
   - 当前能力：写入前 preview 已显示整体推荐，但逐项关联较弱。  
   - 价值高，依赖扫描关注点更清晰后再推进。

本轮选择第 1 项。

## 用户故事

作为 Harness Maintainer，当我首次 guided `init` 扫描完成并准备补充或修正扫描理解时，我可以在 CLI 中看到按“风险区域”“不确定性”“验证缺口”“建议补充”分组的关注点摘要，从而知道哪些判断需要优先确认、哪些验证能力会影响后续 Guides / Sensors / 成熟度预览。

## 范围

包含：

- 在 `_show_scan_findings()` 中新增扫描关注点分组。
- 从现有 `inventory.stack_extensions` 和 `commands.commands` 推导风险、不确定性、验证缺口和建议补充。
- 支持无风险/无 warning/验证较完整时给出简短正向说明。
- 用户返回 `back -> scan` 时复用同一展示逻辑，确保修正前仍能看到关注点。
- 增加 guided integration 测试覆盖 transcript。

不包含：

- 不新增或修改 Pydantic schema。
- 不修改 LLM prompt、scan reconciler 或 `scan_repository()`。
- 不把自然语言补充自动转成正式 routing policy。
- 不改变非交互输出。
- 不新增 benchmark 检查。

## 设计

在 `src/harness_builder_agent/tools/interactive_init.py` 中新增：

- `_show_scan_attention_summary(inventory, commands)`
- `_risk_attention_lines(inventory)`
- `_uncertainty_attention_lines(inventory, commands)`
- `_verification_gap_lines(commands)`
- `_human_followup_lines(inventory, commands)`

`_show_scan_findings()` 在展示“识别到的验证命令”后调用 `_show_scan_attention_summary()`。

分组契约：

- `风险区域`：来自 `inventory.stack_extensions["risk_areas"]`，展示 path 和 reason；无风险时说明暂未识别高风险区域但仍可人工补充。
- `不确定性`：来自 `needs_human_confirmation`、`scan_warnings`、`llm_scan_proposal.confidence`、`primary_stack == "unknown"`、low confidence command。
- `验证缺口`：无命令、无 hard gate、hard gate 缺 source 或 low confidence、只有 soft gate、缺少 test/build/lint/typecheck 类型。
- `建议补充`：根据上面风险和缺口生成用户可行动的问题，例如补充高风险目录、真实 hard gate 命令、测试目录、团队验证规则。

CLI 文案必须是中文用户语言，不直接暴露 `primary_stack`、`overall_level`、`dimension_scores` 等内部字段名。

## Assumptions / Risks

- `stack_extensions["scan_warnings"]` 和 `llm_scan_proposal` 已由 scan reconciler 生成；本轮只读消费，不要求所有旧 inventory 都有这些字段。
- 风险摘要是“关注点”，不是正式成熟度评分；成熟度仍由后续 preview / `maturity-score.yaml` 负责。
- 命令类型缺失不一定代表项目没有该验证能力，只表示扫描未发现或未确认，必须用“建议补充/确认”表达。
- 文案会进入测试契约，后续大幅改写需同步测试和工程文档。

## 验收标准

1. guided init happy path 输出包含 `风险区域`、`不确定性`、`验证缺口`、`建议补充`，且这些分组出现在“扫描发现”之后、“团队规则”之前。
2. 当 fake scan 返回 risk area、scan warning、low confidence soft command 且无 hard gate 时，CLI 明确展示风险路径、warning 信息、low confidence 命令、无已确认 hard gate、建议补充真实验证命令。
3. CLI 不暴露 `primary_stack`、`overall_level`、`dimension_scores` 等机器字段名。
4. 用户后续补充仍按现有逻辑写入 `interaction-decisions.yaml`、Guides 和 `human-input-needed.md`。
5. 相关 guided integration、`scripts/test-fast.sh` 和 push 前 `scripts/test-full.sh` 通过。
