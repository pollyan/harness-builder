# Existing Harness Self-Improve Action Design

## North Star 能力模块

- CLI Experience：`init` 是已有 Harness 后续维护入口，专家命令可被向导编排。
- Experience & Self-Improve：把成熟度缺口、LLM maturity review 和 asset candidates 组合为 review-only 自改进包。
- Maturity & Evolution：围绕成熟度缺口生成下一步改进候选，并保持可审查、可追溯。

## Current State Gap Analysis

| 候选 gap | 目标态要求 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 排序 |
|---|---|---|---|---|---|---|---|
| guided `self-improve` | 维护入口能触发智能自改进包 | standalone `self-improve` 已有 review-only package、schema、benchmark 和 acceptance | 普通用户仍需记住专家命令 | 高，直接提升智能化主路径 | 中，涉及真实 LLM，测试需 mock | 高，integration 可覆盖 orchestration | 1 |
| guided apply with diff | 维护入口能应用候选 | standalone applied 已存在 | 需要 diff/summary/强确认 | 高 | 高，正式资产变更 | 中 | 2 |
| recommendation history | 多次 recommendation 可保留历史 | 当前单份 latest | 需要新 schema | 中 | 中 | 中 | 3 |

本轮只做 guided `self-improve` 入口，不改变底层 LLM prompt、package schema 或 asset candidate 应用方式。

## 设计

当 guided `init` 检测到已有 Harness 后，在菜单新增：

```text
- self-improve：生成 review-only 自改进审查包，不应用正式资产或执行 Runtime。
```

用户选择 `self-improve`、`self`、`自改进` 或 `智能改进` 后：

1. 输出简短边界说明：将运行 maturity assessment、deterministic improvements、LLM maturity review 和 LLM asset candidate generation；需要 DeepSeek 配置。
2. 调用现有 `run_self_improve(repo)`。
3. 读取 `.ai/review/self-improve-package.yaml`，通过 `SelfImprovePackageManifest` 校验。
4. 在 init trace 中记录 maturity、improvement、maturity review、asset candidates、self-improve package artifacts。
5. 打印候选计数、成熟度等级、review-only 文件路径和不创建 `.ai/task-runs` 的边界。

## 边界与失败模式

- LLM 不可用、返回非法 JSON 或 schema 无效时必须显式失败，不 fallback。
- 不重新扫描已有 Harness。
- 不应用正式 Guides、Sensors、Workflow Skills 或 routing policy。
- 不执行 Runtime、不运行业务任务、不创建 `.ai/task-runs`。
- `run_self_improve` 会刷新 maturity / improvements / review-only candidate 等派生产物；这不是只读动作。

## Assumptions / Risks

- Assumption：已有 Harness 维护入口中触发 self-improve 是显式用户动作，不违反“首次 init 不默认 self-improve”的原则。
- Risk：真实 DeepSeek 成本和耗时更高；测试使用 mock，真实 acceptance 已覆盖 standalone `self-improve`。
- Risk：用户可能误解自改进为自动修改 Harness；文案和 docs 必须强调 review-only。

## Sub Agent 使用

本轮启动 explorer 子代理审计 guided `self-improve` 是否适合作为小 milestone、交互边界、风险和验收标准。主线程并行写 RED 测试和实现；子代理结论返回后纳入实现或 Self-Harness Gate。

## 可执行验收标准

- guided existing-Harness 菜单包含 `self-improve`。
- 选择后生成 `.ai/review/self-improve-package.yaml` 和 `.md`。
- manifest 通过 `SelfImprovePackageManifest` schema，`review_status` 为 `pending_harness_maintainer_review`。
- 输出包含 candidate counts 和 review-only 路径。
- benchmark 对 `content:self-improve-package` 检查通过。
- 不扫描、不覆盖正式 Harness 资产、不创建 `.ai/task-runs`。
- trace summary 包含 `existing_harness_action: self-improve` 和 candidate counts。

