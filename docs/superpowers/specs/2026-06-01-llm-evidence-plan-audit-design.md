# LLM Evidence Plan 可审计设计

## 目标

作为 Harness Maintainer，当我在大型多栈仓库运行首次 guided `init`，如果系统让 LLM 从全量轻量 manifest 中选择少量关键文件补读，我可以在 `.ai/scan-metadata.yaml` 中审计 planner 的 rationale、risk_focus、requested_paths、实际读取文件和 confidence；如果 planner 低置信度，扫描结果会保留明确 warning 和 human confirmation 信号，从而知道深度扫描不是黑盒动作。

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划 Scanner & Analyzer 段落、`docs/todos/guided-init-ai4se-real-repo-findings.md`、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`。
- 已检查代码：`scan_repo.py`、`scan_reconciler.py`、`schemas/scan.py`、`asset_writers/core.py`、`write_assets.py`、`human_confirmation.py`、`benchmark.py`。
- 已检查测试：`test_scan_repo.py`、`test_scan_reconciler.py`、`test_schema_contracts.py`、`test_init_on_fixture_projects.py`、`test_asset_writer_core.py`。
- 按需未展开：Runtime task-run、candidate governance、workflow recommendation、maturity review；本轮不修改这些链路。

候选 gap：

| 候选 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Evidence plan 写入 scan metadata | `.ai/scan-metadata.yaml` 可审计 LLM planner 为什么请求文件、请求哪些、实际读了哪些、planner confidence | scan repo 已执行 planner 并把 `llm_requested_files` 注入最终 scan；metadata 只含 coverage/warnings/reasoning_summary | planner rationale/risk_focus/requested_paths 和实际读取结果不落盘 | 让 deep scan 从内部动作变成可 debug、可回溯、可验收的资产契约 | 中；需 schema 扩展和 scan_repo/reconciler 参数传递 | unit + integration + schema | 无外部凭证 | ScanMetadata schema 有 `evidence_expansion`；scan_repo/reconciler/unit 和 init integration 证明落盘 |
| B. LLMScanProposal 字段严格结构化 | modules/risk_areas/configs/ci_files 不再是 `dict[str, Any]`，最低字段被 schema enforce | prompt 已要求 path/reason/kind；Pydantic 仍接受空 dict | 合法 JSON 但机器契约空洞会漏过 parser | 降低 LLM 输出漂移风险 | 中到高；可能影响真实 LLM acceptance | schema/parser tests | 需要 prompt 与 acceptance 校准 | 缺字段 response 显式失败，真实 LLM prompt 同步 |
| C. Claim-level support/conflict/unknown | module path、risk path、config/CI path、architecture signal 都有 evidence support/conflict/unknown | 当前只验证 stack 和 command source | 模块、风险和架构信号仍缺少细粒度调和 | 进一步接近“Python 做 detector validation” | 高；涉及 schema、metadata、CLI 展示和 benchmark | 多层 unit/integration | 需要更大设计 | scan validation 增加 claim map，并进入 human confirmation |

排序结论：

1. 选择 A，因为它直接延续上一轮 manifest 语义增强，形成“LLM 规划 -> Python 安全读取 -> 最终 scan -> metadata 审计”的完整闭环，用户/维护者价值明确，风险可控。
2. B 暂不选，因为它会改变真实 LLM 输出契约，适合作为下一轮 hardening。
3. C 暂不选，因为它是更大的 detector/reconciler 迁移，需要独立 spec。

## 设计

新增一个稳定机器契约 `LLMEvidenceExpansionMetadata`，挂到 `ScanMetadata.evidence_expansion`：

- `schema_version`
- `planner_prompt_version`
- `requested_paths`
- `risk_focus`
- `rationale`
- `confidence`
- `read_paths`
- `read_file_count`

数据流：

1. `scan_repository()` 调用 `plan_evidence_expansion_with_llm()` 后保留 `LLMEvidencePlan`。
2. `expand_evidence_with_requested_paths()` 读取补充文件后，`EvidenceBundle.llm_requested_files` 作为实际读取结果。
3. `scan_repository()` 把 `evidence_plan` 传入 `reconcile_scan()`。
4. `reconcile_scan()` 用 `LLMEvidencePlan` 和 `EvidenceBundle.llm_requested_files` 生成 `ScanMetadata.evidence_expansion`。
5. 如果 planner confidence 为 `low`，追加 `llm_evidence_plan_low_confidence` warning，并把 `ProjectInventory.stack_extensions["needs_human_confirmation"]` 置为 true。
6. `write_initial_assets()` 继续通过现有 `scan_metadata(inventory)` 写出 `.ai/scan-metadata.yaml`，无需新增 writer 分支。

## 验收标准

1. `ScanMetadata` schema 能解析 `evidence_expansion`，并要求其字段结构稳定。
2. `scan_repository()` 在 mock planner 场景下把 planner rationale、risk_focus、requested_paths、read_paths 和 read_file_count 放进 inventory 的 `scan_metadata`。
3. `reconcile_scan()` 在 planner confidence 为 `low` 时增加 warning，并把 human confirmation signal 保留到 inventory。
4. `init --non-interactive` 的 fixture 输出 `.ai/scan-metadata.yaml` 包含 `evidence_expansion`，文件可由 `ScanMetadata` schema 校验。
5. 未执行 planner 的旧/测试路径保持兼容：`evidence_expansion` 可以为 null / absent，benchmark schema 仍通过。

## 取舍与非目标

- 不新增第二轮 LLM scan，不改变 requested_paths allowlist，不扩大读取预算。
- 不把 planner metadata 写进 `llm-scan-proposal.json`，因为它不是最终 scan proposal。
- 不本轮严格化 `modules/risk_areas/configs/ci_files`，但把它作为下一轮候选。
- 不把 coverage warning 直接变成扫描失败；保持 warning + human confirmation 机制。

## Sub Agent 使用

本轮启动一个 explorer 子代理只读调研 scan metadata 数据流、测试落点和 benchmark 影响。主线程负责 spec、plan、TDD、验证和提交。
