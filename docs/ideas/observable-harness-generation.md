# 可观测的 Harness 生成过程

状态：idea

来源：JiuwenSwarm Auto-Harness 调研 / 2026-05-30

相关范围：Harness Builder POC 后续增强

## 一句话

让 `harness-builder-agent init`、`assess`、`improve` 的生成过程可追溯：为什么扫描出这些技术栈、为什么选择这些 weapon、为什么生成这些 guide、sensor 和 skill。

## 为什么重要

- 提升用户对生成结果的信任。
- 方便调试生成质量和 benchmark 失败原因。
- 支撑真实开源仓库 E2E 验收。
- 让每条重要规则都能追溯来源，而不是看起来像模型即兴生成。

## 暂时不做什么

- 不做 UI。
- 不做后台服务。
- 不做复杂任务调度。
- 不替代现有测试体系。

## 可能形态

- `.ai/runs/<run_id>/events.jsonl`
- `.ai/runs/<run_id>/decision-log.md`
- `.ai/runs/<run_id>/trace.yaml`
- `.ai/runs/<run_id>/artifacts/`

## 触发执行的信号

当我们开始增强生成质量、benchmark、真实仓库 E2E、InfoCode 集成时，再把这个 idea 提升为 spec 或 implementation plan。

