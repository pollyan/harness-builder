# LLM-Guided Evidence Expansion Design

## 用户故事

作为遗留仓库的 Harness Maintainer，当仓库文件结构不规范、关键风险代码没有落在固定采样前几项时，我希望 Harness Builder 先让 LLM 基于初始 evidence 规划需要深入读取的补充文件，再生成最终 scan proposal，从而让模块、风险区和验证建议更贴近真实代码，而不是只受确定性采样规则限制。

## Current State Gap Analysis

- North Star 要求 Harness Builder 是 AI Agent，LLM 负责理解、判断和推荐，Python 负责 schema、evidence、reconciler 和 validation。
- 当前扫描链路是 LLM-first：`collect_evidence -> analyze_evidence_with_llm -> reconcile_scan`。
- 当前 evidence collection 仍由确定性 bucket 和排序采样决定。大仓库中 source bucket 超过上限时，LLM 只能看到前 N 个 source sample、priority file、test/API/risk 文件。
- 这比纯脚本强，但还不是 LLM-guided evidence collection。模型无法先看初始文件索引，再请求更可能解释业务边界、风险区或验证命令的文件。
- 结果风险是：复杂企业仓库中命名不标准、关键文件排序靠后、业务风险隐藏在非典型路径时，最终 scan proposal 仍会被固定采样偏差限制。

## 目标

- 新增机器消费型 `llm-evidence-plan-v1` prompt 和 schema，让 LLM 基于初始 `EvidenceBundle` 选择最多 8 个补充文件。
- 补充文件只能来自 `EvidenceBundle.files` 中的已发现文件，且不能引用 `.ai`、依赖目录或仓库外路径。
- Python 只负责按 plan 读取被请求文件的摘要，并把它们加入 `EvidenceBundle.llm_requested_files`。
- 最终 scan prompt 消费扩展后的 evidence，因此 LLM scan analyzer 可以引用补充文件中的信息。
- 单元测试覆盖 planner JSON/schema/路径失败、evidence expansion、scan_repository 两阶段调用。

## 非目标

- 不让 LLM 直接读取任意路径或写文件。
- 不改变 `LLMScanProposal` 的最终 schema。
- 不改变 reconcile 的栈冲突 veto 和 no silent fallback 规则。
- 不把 planner 失败包装成确定性 fallback。
- 不运行真实 DeepSeek acceptance；本轮使用 mock LLM 验证契约。

## 设计

新增 schema：

- `LLMEvidencePlan`
  - `schema_version`
  - `requested_paths`
  - `risk_focus`
  - `rationale`
  - `confidence`

新增 prompt：

- `src/harness_builder_agent/prompts/llm_evidence_plan_v1.md`
- 通过 `prompts.registry` 注册。
- 要求只输出 JSON object，只能从 provided `files[].path` 选择路径，不得发明路径。

新增工具：

- `tools/llm_evidence_planner.py`
  - `build_evidence_plan_messages(evidence)`
  - `parse_llm_evidence_plan_response(content, allowed_paths)`
  - `plan_evidence_expansion_with_llm(evidence, caller=None, config=None)`

扩展 evidence collector：

- `EvidenceBundle` 增加 `llm_requested_files`。
- 新增 `expand_evidence_with_requested_paths(repo, evidence, requested_paths, max_summary_chars=1200)`。
- 被请求文件以 `kind="llm_requested"`、`priority="high"`、`bucket="llm_requested"`、`reason="LLM evidence planner requested this file."` 进入 bundle。

更新扫描链路：

- `scan_repository()` 在真实 LLM 路径默认执行 evidence planner，再运行最终 scan analyzer。
- 为测试兼容，`llm_caller` 仍可只注入最终 scan；需要测试 planner 时显式传入 `evidence_planner_caller`。

## 验收标准

- unit：planner 接受合法 JSON fence，并拒绝非法 JSON、schema 错误、仓库外路径和不在 allowlist 的路径。
- unit：evidence expansion 能读取原始采样未选中的文件，并加入 `llm_requested_files`。
- unit：`scan_repository(..., evidence_planner_caller=..., llm_caller=...)` 会先调用 planner，再让最终 scan 消费 `llm_requested_files`。
- unit：prompt registry 包含 `llm_evidence_plan_v1.md`，所有 prompt asset 测试不维护第二份静态清单。
- docs：LLM contracts、architecture、evolution log 说明 LLM-guided evidence expansion 的边界。

## Decisions / Responses

- 价值切分：本轮不是“加一个 prompt 文件”，而是让复杂仓库扫描从固定采样推进到 LLM 规划补充 evidence 的用户价值。
- 智能边界：LLM 决定“还需要看什么”，Python 负责路径 allowlist、读取摘要、schema 校验和最终 reconcile。
- 兼容取舍：既有单 caller 测试路径保留最终 scan 注入语义；真实无 caller 路径默认启用 planner。
- 风险取舍：planner 多一次 LLM 调用，会增加真实 acceptance 成本；但这是扫描智能化的核心投入，且失败必须显式暴露。

## Assumptions / Risks

- 假设最多 8 个补充文件足以作为第一版智能 evidence expansion，避免 prompt 体积失控。
- 真实 LLM 可能请求非法路径；这是 contract 失败，不 fallback。
- 后续可以把 planner 请求理由、未满足请求和效果指标写入 scan metadata；本轮先让最终 scan 消费扩展 evidence。
