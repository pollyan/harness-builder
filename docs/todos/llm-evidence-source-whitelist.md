# LLM Evidence Source Whitelist Hardening

## 状态

- 状态：open
- 优先级：high
- 发现日期：2026-05-31
- 相关模块：`recommend-workflow`、`review-maturity`、`generate-asset-candidates`、`benchmark`
- 相关工程规则：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`

## 背景

当前多个 LLM 输出契约会要求 `evidence_sources` 使用 `.ai/` 路径。实现已经能拒绝 `.ai/` 外路径，但还没有统一校验这些路径必须来自本轮提供给 LLM 的 evidence source map、maturity inputs、Experience sources 或真实存在的 Harness artifact。

这会留下一个可审计性缺口：模型可能返回一个以 `.ai/` 开头但并未提供或不存在的路径，产物看起来像有证据，实际无法追溯。

## 理想状态

- Workflow recommendation、maturity review、asset candidates 和 experience summary 的 parser 都能接收允许引用的 evidence source 集合。
- LLM 返回的 `evidence_sources` 必须属于该集合，或属于明确允许的核心 Harness artifact。
- benchmark 能检查已落盘 review-only artifact 的 evidence source 是否可追溯。
- 错误必须显式失败，不能把未知 `.ai/` 路径当作有效证据。

## 初步验收标准

- 单元测试覆盖未知 `.ai/` evidence source 被拒绝。
- integration / benchmark 覆盖落盘 review artifact 引用未知 source 时失败。
- prompt 仍要求引用 provided evidence paths，不扩大为任意 `.ai/` 路径。
- 不引入 silent fallback。
