# Guided Init 采样不确定性中文化设计

## 背景

本轮继续消化 `docs/todos/guided-init-ai4se-real-repo-findings.md`。上一轮已经降低 `.claude` / `.opencode` 等工具工作区 evidence 噪声，但真实多栈仓库仍会在 CLI 中直接展示 `source:.py skipped 73 files` 这类内部 warning。

这类信息有审计价值，但作为 guided `init` 的用户界面过于内部化。Harness Maintainer 需要知道的是：哪些源码类型覆盖不足、已经抽样了多少、可能遗漏什么、下一步该补充什么，而不是直接阅读 bucket 和 skipped 字段。

## Current State Gap Analysis

- 产品能力：`init` 已能展示扫描发现、风险、不确定性、验证缺口和成熟度初评，但不确定性仍可能泄露英文和内部 bucket 表达。
- init 用户旅程：问题发生在“扫描结果的友好呈现”和“对齐扫描理解”阶段，用户尚未补充上下文前就需要理解覆盖不足。
- CLI 体验：`_uncertainty_attention_lines()` 直接输出 `scan_warnings[].message`，导致 `source:.py skipped 73 files` 进入终端。
- 仓库理解深度：`EvidenceCoverage.bucket_coverage` 已记录 total / selected / skipped，`scan-metadata.yaml` 可审计；缺口是 CLI 没把这些 metadata 翻译成用户可行动的说明。
- 成熟度叙事：覆盖不足会影响 stack、module、risk 和 Sensor 推荐置信度，但当前输出没有说明影响。
- schema / 数据：`coverage.bucket_coverage` 已有 `skipped_count`；`coverage.warnings` 目前只带 code、bucket、message，直接 warning 里缺少 selected / total / skipped 的便捷字段。
- 测试：已有 guided init integration 测试覆盖风险 / 不确定性 / 验证缺口展示，可扩展 transcript 断言；evidence collector unit 可补充 warning detail 断言。

## 用户故事

作为 Harness Maintainer，当我对一个源码文件很多的真实仓库运行首次 guided `init` 并看到扫描不确定性时，我可以用中文看到“某类源码只被抽样读取、还有多少文件未进入初始摘要、这会影响哪些判断、下一步该补充什么”，从而知道如何校准仓库理解，而不是被内部 bucket warning 干扰。

## 设计

采用小范围 CLI 翻译层，不改变扫描主链路：

1. `evidence_collector._coverage()` 在 `source_sampling_truncated` warning 中补充 `total_count`、`selected_count`、`skipped_count`，让机器 metadata 更容易审计。
2. `interactive_init._uncertainty_attention_lines()` 不再直接输出 warning message，而是调用 `_format_scan_warning_for_cli()`。
3. 对 `source_sampling_truncated`：
   - 从 warning evidence / bucket 和 `scan_metadata.coverage.bucket_coverage` 找到 bucket 覆盖数据。
   - 输出中文说明：源码类型、已抽样数量、未进入初始摘要数量、可能影响技术栈 / 模块 / 风险判断、建议补充关键目录或入口文件。
   - 不把 `source:.py skipped 73 files` 作为 CLI 主表达。
4. 对 `test_evidence_not_found` 输出中文测试证据不足说明，避免同一不确定性区块继续泄露英文。
5. 对未知 warning 保留原 message，但加上“扫描 warning”前缀；这保持调试信息不丢失，同时不为未知 code 伪造解释。

## 验收标准

- guided init transcript 中出现 source sampling warning 时，`不确定性` 区块用中文说明抽样覆盖不足，包含 `.py`、已抽样数量、未进入初始摘要数量和补充建议。
- 同一 transcript 不再出现 `source:.py skipped 73 files` 这类内部表达。
- `test_evidence_not_found` 在 CLI 中被翻译成中文测试证据不足说明。
- `EvidenceCoverage.warnings` 保留稳定 `code` / `bucket`，并包含 `total_count`、`selected_count`、`skipped_count`，不破坏 `scan-metadata.yaml` 的审计价值。
- 本轮只处理 skipped / sampled 信息中文化，不实现完整多栈建模、高风险风险项突出或 LLM-planned deep scan。

## 决策与取舍

- 不新增新的 Pydantic warning schema 字段。`coverage.bucket_coverage` 已是权威覆盖数据，CLI 翻译层读取该结构即可。
- 不把覆盖不足自动升级为失败。它是用户需要理解和补充的扫描不确定性，后续 deep scan / targeted scan 会作为单独切片。
- 不修改 `--non-interactive` 语义。该切片只影响 guided CLI transcript 和 metadata detail。

## Assumptions / Risks

- 假设 `scan_metadata.coverage.bucket_coverage` 在真实扫描中可用；如果旧 inventory 缺少 coverage，CLI 会退化为中文通用说明。
- 风险是 warning 翻译过度隐藏调试细节；因此未知 warning 仍保留原 message，机器 metadata 继续完整落盘。
- 子代理用于并行审查代码路径和选题优先级；主线程负责最终实现和验证。
