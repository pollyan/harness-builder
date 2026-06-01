# LLM 候选成熟度影响机器契约

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划开篇、`docs/engineering/init-workflow.md`、`docs/engineering/architecture.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`guided_candidate_review.py`、`llm_enhancement_candidates.py`、`weapon_library_candidate.py`、candidate writer、benchmark schema check 和相关 tests。
- 按需未展开：`docs/engineering/llm-contracts.md`、`docs/engineering/sensor-and-gate-rules.md`。本轮不修改 LLM prompt、LLM response schema、Sensor 或 benchmark 规则，只增强本地生成的 candidate report 契约。
- Todo 状态：`docs/todos` 无 open todo；上一轮 Gate 候选包括是否把 candidate maturity impact 提升为机器契约、push / 远端同步。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. LLM candidate maturity impact 进入机器契约 | 上一轮 Gate / init North Star / 全景规划 | `.ai/experience/weapon-library-candidates.yaml` 结构化记录 candidate 对 Guides / Risk Control / Sensors / Verification 的成熟度影响、下一阶段贡献和 review-only 边界 | CLI candidate review 已展示成熟度影响；candidate YAML 只记录 type/title/rationale/evidence/status | 后续 self-improve、review 或维护入口只能读自然语言 rationale，无法稳定消费同一成熟度影响判断 | 把 maturity-driven 审查从终端文案推进到可审计机器资产，提升后续智能改进闭环一致性 | 中；涉及 schema，但字段可设默认以兼容旧资产 | schema unit、candidate generation unit、asset writer markdown/yaml unit、guided init integration、benchmark schema check | 无外部依赖 | YAML/Markdown/CLI 均包含同一 maturity impact；旧 payload 缺字段仍可 schema validate | 本轮 |
| B. Candidate maturity impact 驱动维护入口 triage | Gate / 新发现 | 已有 Harness 入口展示 pending candidate 时按 maturity impact 排序或解释 | 入口展示 asset candidates / governance 数量和信号 | 没有利用 weapon-library candidates 的 maturity impact 做下一步动作 | 维护价值高，但依赖 A 的机器契约先稳定 | 中；涉及 existing Harness 入口和 triage | existing Harness integration | 依赖 A | 下一轮候选 |
| C. push / 远端同步 | 交付节奏 | 完整工作包通过 full regression 后 push | 本地 `main` 领先远端 55 个提交 | push 前 full regression 需要真实 DeepSeek 与 `.benchmarks/*` | 让远端获得当前阶段成果 | 高；外部凭证 / 真实仓库前置 | `scripts/test-full.sh` + push | DeepSeek key、真实仓库 | 外部前置满足后处理 | 暂不处理 |

排序结论：

1. 选择 A，因为上一轮已经证明 maturity impact 对 CLI 审查有价值；把它写入机器契约能让 `.ai` 资产更接近 Maturity-driven Self-Improve 的目标态。
2. B 需要 A 先稳定字段，不适合反向依赖自然语言 CLI 文案。
3. C 仍受 full regression 外部前置限制。

本轮 milestone：

作为 Harness Maintainer / 后续 Self-Improve 审查流程，当我查看或消费 `.ai/experience/weapon-library-candidates.yaml` 中的 LLM Guide / Sensor 候选时，我可以获得结构化成熟度维度、成熟度影响摘要、下一阶段贡献和 review-only 边界，从而让候选审查不只停留在终端文案，而能被后续 review、benchmark 和自改进流程稳定审计。

## 验收标准

1. `WeaponLibraryCandidate` schema 新增向后兼容字段：
   - `maturity_dimensions`，默认空列表。
   - `maturity_impact_summary`，默认空字符串。
   - `next_stage_contribution`，默认空字符串。
   - `review_boundary`，默认 `review_only_no_formal_asset_change`。
2. `build_llm_enhancement_candidates()` 生成的 architecture / risk / sensor / no-enhancement candidates 都写入上述字段。
3. `guided_candidate_review.py` 复用同一结构化 helper 渲染 CLI，避免 CLI 与 YAML 两套判断漂移。
4. candidate Markdown review files 展示 maturity impact、next stage contribution 和 review boundary。
5. 旧 candidate payload 缺少新增字段时仍能通过 schema validation，避免 benchmark 对旧 Harness 产生破坏性 schema 失败。
6. 不修改 LLM scan proposal schema、不修改正式 Guide / Sensor 写入、不应用候选、不执行 Runtime 或创建 `.ai/task-runs`。

## 决策 / 取舍

- 使用本地确定性 helper 生成 maturity impact，而不是要求 LLM 输出新字段；这样 Python 负责 schema / validation / audit，符合“LLM 做判断候选，Python 做契约”的分工。
- 字段默认值保证旧资产兼容；本轮不要求 benchmark 因缺 maturity impact 失败，避免破坏既有 Harness。
- 不把 maturity impact 写入 `maturity-evidence.yaml`，先让候选资产自身稳定。

## Assumptions / Risks

- Assumption：候选成熟度影响是后续 self-improve / review 候选排序和解释的基础契约。
- Risk：当前 helper 仍是启发式，字段进入机器契约后可能显得权威。通过 `review_boundary` 和保守 summary 明确它仍是 review-only 候选解释，不是正式成熟度提升结论。

## Sub Agent

尝试启动 explorer 做只读审查，但当前会话返回 `agent thread limit reached`。本轮由主线程完成调研、实现和验证。
