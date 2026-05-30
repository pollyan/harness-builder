# Weapon Library Floor And LLM Enhancement Design

## 背景

Harness Builder 已经实现内置武器库：`common + primary_stack` 的 Guide/Sensor 条目会被稳定摘取，并写入 `.ai/weapon-library-selection.yaml`。这解决了“每次生成必须有稳定底线”的问题。

但 `docs/ideas/weapon-library-floor-and-llm-enhancement.md` 还要求另一半能力：武器库不能成为上限。项目扫描和 LLM 分析中发现的合理实践、风险区域、验证建议，如果未被武器库覆盖，应进入候选通道，而不是丢失或伪装成已确认规则。

## 目标

在不新增额外 LLM 调用的前提下，复用已有 `llm-scan-proposal.json`，生成模型增强候选资产：

- `.ai/review/llm-enhancement-candidates.md`
- `.ai/review/candidate-guides.md`
- `.ai/review/candidate-sensors.md`
- `.ai/experience/weapon-library-candidates.yaml`

这些资产必须明确标记：

- `source: llm_scan_proposal`
- `status: candidate`
- `human_confirmation_required: true`
- evidence/rationale 来源于 scan proposal 的 `architecture_signals`、`risk_areas`、`command_candidates`

## 非目标

- 不让模型动态改写内置武器库。
- 不把增强建议写成 confirmed 规则。
- 不新增第二次 DeepSeek 调用。
- 不实现用户确认后自动沉淀到武器库的完整流程。

## 数据来源

输入来自：

- `ProjectInventory.stack_extensions["llm_scan_proposal"]`
- `ProjectInventory.stack_extensions["risk_areas"]`
- `ProjectInventory.stack_extensions["architecture_signals"]`
- `CommandCatalog.commands`
- `WeaponLibrarySelection`

## 产物设计

### `.ai/review/llm-enhancement-candidates.md`

面向人工审查，汇总候选 Guide/Sensor：

- 候选来源。
- 候选状态。
- 关联 evidence。
- 建议下一步。

### `.ai/review/candidate-guides.md`

只包含 guide 类候选：

- 架构信号候选。
- 风险区域候选。
- 团队上下文候选。

### `.ai/review/candidate-sensors.md`

只包含 sensor 类候选：

- LLM 提出的命令候选。
- 风险区域对应的验证建议。
- 缺失能力提示。

### `.ai/experience/weapon-library-candidates.yaml`

机器可读候选：

```yaml
schema_version: '1.0'
source: llm_scan_proposal
candidates:
  - id: llm-guide-risk-001
    candidate_type: guide
    status: candidate
    title: 认证配置风险
    rationale: LLM scan detected risk area in application.yml
    evidence:
      - application.yml
    human_confirmation_required: true
```

## 生成规则

Guide candidates：

- 每个 `architecture_signals` 生成一条 guide candidate。
- 每个 `risk_areas` 生成一条 guide candidate。

Sensor candidates：

- 每个 `command_candidates` 生成一条 sensor candidate。
- 如果某个 command id 已经在 `CommandCatalog` 中存在，仍可进入候选，但 rationale 要说明它是“建议审查是否提升/保留为 gate”。

去重规则：

- 根据 `candidate_type + title + evidence` 去重。
- 不和内置武器库 id 混用，候选 id 使用 `llm-guide-*` / `llm-sensor-*`。

## Benchmark

Benchmark 新增检查：

- `exists:review/llm-enhancement-candidates.md`
- `schema:weapon-library-candidates`
- `content:llm-enhancement-candidates`

要求：

- YAML schema 正确。
- candidates 非空。
- 所有 candidate 都是 `status=candidate`。
- 所有 candidate 都要求 `human_confirmation_required=true`。

## 验收标准

- Java 和 .NET fixture 都生成 review/experience 候选资产。
- Benchmark 能区分内置武器库底线和 LLM 增强候选质量。
- 默认测试通过。
- 真实 DeepSeek fixture acceptance 通过。
- 真实开源仓库 e2e 通过。

