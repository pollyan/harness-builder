# 武器库底线与模型增强机制

状态：implemented

落地记录：

- Spec：`docs/superpowers/specs/2026-05-30-weapon-library-llm-enhancement-design.md`
- Plan：`docs/superpowers/plans/2026-05-30-weapon-library-llm-enhancement-plan.md`
- 产物：`.ai/review/llm-enhancement-candidates.md`、`.ai/review/candidate-guides.md`、`.ai/review/candidate-sensors.md`、`.ai/experience/weapon-library-candidates.yaml`

来源：产品设计讨论 / 2026-05-30

相关范围：武器库、Guide/Sensor 生成、LLM 推理增强、生成质量评估

## 一句话

武器库应该提供稳定、可复用、可验证的底线能力，而不是限制 Harness Builder 的生成上限。生成流程应该在确定性武器库选择之后，允许大模型基于项目上下文补充合理的 Guide、Sensor 和改进建议。

## 为什么重要

- 武器库能降低大模型输出不稳定的问题，保证每次生成有基础质量。
- 但如果生成内容只允许来自武器库，未被收录的合理实践就可能无法进入 Harness。
- 不同团队、项目和技术栈会有武器库之外的特殊约束。
- Harness Builder 的目标不是只复制内置模板，而是结合代码事实、团队上下文和模型推理生成更有效的工程工作流资产。

## 设计原则

- 武器库是底线，不是天花板。
- 武器库负责稳定性、基础覆盖和可解释来源。
- 大模型负责基于具体项目补充上下文相关的上限建议。
- 模型补充内容必须标记来源、置信度和状态，不能直接伪装成已确认团队规则。
- 合理但未被武器库覆盖的建议，应进入 candidate 或 pending 区域，等待用户确认或后续评估。

## 需要检查的问题

- 当前生成逻辑是否只会输出武器库已列出的 Guide/Sensor？
- 武器库未覆盖的合理建议是否有进入 Harness 的通道？
- LLM 补充建议是否被明确标记为 `candidate`？
- benchmark 是否能区分“武器库底线覆盖”和“模型增强建议质量”？
- 用户确认或拒绝模型建议后，结果是否能反向沉淀为经验或武器库候选？

## 可能形态

```text
scan codebase
→ select deterministic weapon library items
→ generate baseline guides/sensors
→ ask LLM for project-specific enhancement candidates
→ validate and classify candidates
→ write confirmed baseline + candidate enhancements
→ wait for user confirmation
```

可能的输出：

- `.ai/weapon-library-selection.yaml`
- `.ai/review/llm-enhancement-candidates.md`
- `.ai/review/candidate-guides.md`
- `.ai/review/candidate-sensors.md`
- `.ai/experience/weapon-library-candidates.yaml`

## 暂时不做什么

- 不让模型绕过基础 schema 和安全约束。
- 不把模型补充建议直接写成已确认规则。
- 不要求现在立刻设计完整的武器库扩展机制。
- 不把所有项目差异都提前硬编码进武器库。

## 触发执行的信号

当我们开始检查现有武器库使用方式、增强 Guide/Sensor 生成质量、设计 candidate 资产机制，或者评估模型补充建议如何进入 Harness 时，再把这个 idea 提升为 spec 或 implementation plan。
