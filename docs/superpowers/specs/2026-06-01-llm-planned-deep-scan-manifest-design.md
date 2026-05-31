# LLM 规划式深度扫描 Manifest 语义增强设计

## 目标

作为 Harness Maintainer，当我对一个大型、多栈、目录不规范的仓库运行首次 guided `init` 时，我可以相信 LLM evidence planner 在最终扫描前看到的不只是被确定性采样选中的少量源码摘要，还能看到全量轻量文件索引中每个文件的 bucket、priority 和 reason，从而让 LLM 更容易主动选择被跳过但关键的入口、测试、风险或业务文件做深度读取。

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划中 Scanner / Maturity / LLM 分工相关段落、`docs/todos/guided-init-ai4se-real-repo-findings.md`、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`。
- 已检查代码：`evidence_collector.py`、`llm_evidence_planner.py`、`llm_scan_analyzer.py`、`scan_repo.py`、`scan_reconciler.py`、`schemas/scan.py`、`llm_evidence_plan_v1.md`、`llm_first_scan_v2.md`。
- 已检查测试：`test_evidence_collector.py`、`test_llm_evidence_planner.py`、`test_scan_repo.py`、`test_llm_scan_analyzer.py`。
- 按需未展开：已有 Harness 维护入口、候选治理、Runtime task-run、benchmark hard gate 细节；本轮不修改这些链路。

候选 gap：

| 候选 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 全量轻量 manifest 带语义 | LLM planner 基于全量文件树、目录语义、稳定入口和 coverage gap 主动选择深度读取文件 | `EvidenceBundle.files` 已包含全量路径，但条目只有 `path/kind/size`；采样文件才有 bucket/priority/reason | 未采样文件对 LLM 仍像普通路径列表，planner 难以区分入口、风险、测试、源码和配置优先级 | 提升 deep scan 的智能探索主线，减少确定性采样对理解边界的主导 | 低到中；不改 schema，只填充已有字段并收紧 prompt/test | unit + scan_repo mock LLM | 无外部凭证 | 全量 `files[]` 中未采样风险/测试/入口文件带 bucket、priority、reason；planner prompt 明确消费这些字段；scan_repo 测试证明 planner 可选未采样文件 |
| B. LLM plan 结果进入 scan metadata | 最终 `.ai/scan-metadata.yaml` 可审计 planner requested_paths、risk_focus、rationale、confidence | progress details 只显示 requested_path_count；metadata 只存 coverage/warnings/reasoning_summary | 审计者无法从正式 scan metadata 看到 LLM plan 的目标和理由 | 增强可观测性和 debug 能力 | 中；需要 schema 扩展和 writer/benchmark 影响评估 | unit + integration | 可能影响现有 metadata snapshot | scan metadata schema 增加 planner summary 并被 init 产物测试覆盖 |
| C. 二次 self-check / 用户确认触发 | coverage gap、conflict 或 unknown 触发二次 LLM self-check 或更精准用户追问 | coverage warning 进入 scan warning，CLI 会中文解释抽样不足 | 仍不会自动让 planner 对冲突做第二轮自查，也不会按 gap 动态追问 | 更接近目标态完整 deep scan | 高；涉及交互、LLM 调用次数、错误边界和 transcript | integration / acceptance | 需要更大 spec | CLI transcript 或 scan pipeline 覆盖二次 self-check / targeted question |

排序结论：

1. 选择 A，因为它直接推进剩余 todo 的 LLM-planned deep scan 主线，且能在一个清晰 milestone 内完成“全量 manifest -> planner prompt -> LLM requested file -> final scan evidence”的纵向闭环。
2. B 暂不选，因为它更偏可观测性和 schema 迁移；应在 planner 语义增强稳定后作为下一轮候选。
3. C 暂不选，因为它涉及二次 LLM 调用和 guided 交互流程，范围明显大于本轮。

## 设计

本轮不新增 schema 字段。`EvidenceFile` 已有 `bucket`、`priority`、`reason`，当前只是没有给 `EvidenceBundle.files` 的全量索引填充这些字段。

变更点：

1. `collect_evidence()` 在构造 `files` 全量轻量索引时复用 `_bucket_for()`、`_priority_for()` 和 `_reason_for()`。
2. 全量索引仍然不读取正文摘要，`summary` 保持 `None`，避免变成无限制全仓读取。
3. `llm_evidence_plan_v1.md` 明确告诉 LLM：`files[]` 是全量轻量 manifest，包含 bucket / priority / reason；在 coverage warning 或 skipped source bucket 存在时，优先从未进入初始摘要但 priority 较高、风险/入口/测试/业务路径明确的文件中选择补充读取。
4. `scan_repo` 现有 LLM evidence expansion 流程保持不变：LLM 仍只能从 allowlist 中逐字复制路径，Python 仍负责路径校验和预算读取。

## 验收标准

1. `collect_evidence()` 的全量 `files[]` 对未采样文件也保留 bucket、priority、reason；未采样源码仍不读取 summary。
2. 当一个大仓库存在被 source sampling 跳过的高价值文件时，evidence planner prompt 中能看到该文件的 bucket / priority / reason 和 coverage gap。
3. `scan_repository()` 的 planner 可以基于增强后的 full manifest 请求一个未进入 `source_samples` 的文件，最终 scan prompt 包含 `llm_requested_files` 摘要。
4. 仍保持 no silent fallback：planner 请求未知路径继续显式失败，不做近似匹配。
5. 文档更新只记录当前 todo 的稳定进展和下一轮 gap，不把临时推理写入长期工程规则。

## 取舍与风险

- 这不是完整 deep scan 终局，不实现二次 LLM self-check、不扩展 vector index、不无限制读取全仓。
- bucket / priority / reason 是确定性 evidence classification，不是最终业务判断；最终技术栈、模块、风险、命令仍由 LLM proposal 和 reconciler 决定。
- prompt 收紧可能改变真实 LLM requested_paths，但仍受 max 8、allowlist、schema 和 retry 约束。

## Sub Agent 使用

本轮启动一个 explorer 子代理做只读调研：检查当前 LLM evidence planner、scan repo、prompt 和测试覆盖，输出当前能力、关键 gap、推荐 milestone 和测试断言。主线程负责本 spec、实现、验证和提交。
