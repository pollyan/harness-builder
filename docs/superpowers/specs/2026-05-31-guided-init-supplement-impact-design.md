# Guided Init 用户补充复述与影响说明设计

## 当前状态与差距分析

本轮重新读取 AGENTS、README、全景 North Star、init North Star、init workflow 和测试策略后，候选 gap 如下：

1. CLI 阶段进度不足：扫描期间仍偏静默，用户不知道当前是否在 evidence、LLM scan 还是 reconcile。
2. 扫描结果呈现不够完整：风险、不确定性、CI / 测试缺失没有稳定分组。
3. 用户补充缺少即时复述与影响说明：自然语言和结构化修正会进入部分资产，但 CLI 没有说明“我如何理解这些补充、它们会影响什么”。
4. 成熟度叙事还没有贯穿每个推荐项：写入前 preview 已有 L0/L2 主线，但 Guide / Sensor / Workflow 推荐尚未逐项关联维度。
5. 写入后 summary 与 preview 还没有强一致验收。

本轮选择第 3 项。它最直接服务 init North Star 的渐进式协作状态机：用户输入必须发生在设计决策前，被系统复述，并影响后续成熟度、推荐或资产生成。只加进度提示能改善等待体验，但不能证明用户补充进入了决策链路。

## 用户故事

作为 Harness Maintainer，当我在首次 guided `init` 中补充“模块边界、真实验证命令、风险区域、团队规则或工作流说明”时，我可以在写入前看到系统如何理解这些补充，以及它们会影响哪些 Guides、Sensors、成熟度预览或 Workflow 说明，从而确认 Harness Builder 不是只记录文本，而是在用我的输入调整 Harness 设计。

## 关键决策

- 本轮不新增 LLM 语义理解，不假装把任意自然语言解析成结构化事实。
- 结构化 `module=...`、`command=...`、`risk=...` 继续更新 inventory / command catalog / risk areas。
- 非结构化自然语言继续作为 scan notes 和 human overrides 进入 Guide 与 human-input-needed，但 CLI 必须明确标记为“人工补充说明”，不能伪装成扫描事实。
- 最终确认摘要必须展示具体补充内容和影响面，避免只显示“团队规则 1 条”。
- 写入前 maturity preview 可以继续基于现有 `ProjectInventory`、`CommandCatalog` 和 `WeaponLibrarySelection` 计算，不扩大成熟度模型。

## 可执行验收标准

- guided `init` 输入 scan note、团队规则和 workflow note 后，`最终确认` 之后的摘要包含具体补充内容，不依赖 prompt echo。
- 最终确认摘要展示“补充影响”，至少说明扫描补充影响 Guides / 成熟度预览，团队规则影响 Guides / human-input-needed，workflow note 影响 Workflow 说明。
- `interaction-decisions.yaml` 保留 scan / context / workflow notes。
- `.ai/guides/project-context.md` 和 `.ai/human-input-needed.md` 保留这些补充。
- 结构化补充的 command / risk 仍进入 `command-catalog.yaml`、`project-inventory.json` 和 `sensors/verification.md`。
- 不改变非交互 `init` 行为，不新增正式资产 schema。

## 假设与风险

- 自然语言补充的语义边界必须保守：本轮只把它作为人工补充说明和后续审核输入，不自动改 routing policy。
- 如果用户输入很长，CLI 只展示前几条影响摘要；完整内容仍落在 machine-readable decisions 和 Markdown 产物中。
- Workflow note 当前不修改 `harness-config.yaml`，只进入 interaction decisions 和语义 guide；后续可做独立 milestone，让 workflow note 形成 review-only routing 候选。
