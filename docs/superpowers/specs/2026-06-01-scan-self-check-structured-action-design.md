# Scan Self-Check 结构化建议动作设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划前半部分、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、近期 evolution log、`scan.py`、`llm_scan_self_checker.py`、`llm_scan_self_check_v1.md`、`guided_scan_presentation.py`、`human_confirmation.py` 和相关测试。
- 按需未展开：`docs/engineering/sensor-and-gate-rules.md`，本轮不修改 benchmark / Sensor 规则；`docs/engineering/architecture.md`，本轮不改目录结构或模块边界。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Scan self-check 结构化建议动作 | 上一轮 Gate / LLM 契约 | LLM 二次自检不仅给自由文本建议，还输出可 schema 校验的动作类型，让 CLI / questionnaire 能稳定表达下一步是补 `stack`、`module`、`command`、`risk`、复核 evidence 还是 targeted scan | `ScanSelfCheckReport` 已有 schema、prompt、parser、evidence allowlist、guided CLI 展示和 questionnaire reason | `suggested_next_action` 是自由文本；parser 不能拒绝缺失结构化动作，CLI 也无法稳定映射到输入格式 | 强化“LLM 做判断，Python 做 schema/validation”的闭环，降低 Maintainer 从自然语言推断输入格式的负担 | 中；触碰 schema、prompt、parser、CLI 和 tests，但不改正式资产 writer 或 Runtime | schema unit、LLM parser unit、prompt content test、guided scan presentation unit / integration、human confirmation unit | 无外部凭证；依赖现有 self-check schema | 新 LLM response 缺 `suggested_action_type` 时 parser 显式失败；合法 response 展示动作类型和格式提示；旧 persisted metadata 仍可读取 | 本轮 |
| B. Existing Harness action execution 抽模块 | 上一轮 Gate / 架构债 | 主向导只负责编排，维护动作执行由独立模块承接 | summaries / signals 已抽出；action runner 部分已存在 | 仍有 action execution / trace 等复杂边界需要审 | 降低维护入口后续演进成本 | 中高；跨多个 guided actions 和 trace artifacts | unit + existing Harness integration | 无外部依赖 | 后续工程信任故事 | 下一轮候选 |
| C. Full regression / push 工作包 | Git / Gate | 本地 ahead 批次形成完整工作包后 full regression 并 push | 当前 `main` ahead origin 63，本地 commits 已 fast 验证 | push 前必须运行 `scripts/test-full.sh`，可能依赖 DeepSeek / `.benchmarks` / 网络 | 降低长期分叉 | 高；外部前置可能阻塞 | `scripts/test-full.sh`、git push | DeepSeek key、真实仓库、网络 | 完整批次后处理 | 暂缓 |
| D. Human-input benchmark 后续扩展 | 上一轮完成项 Gate | benchmark 覆盖更多 human-input edge cases，如 resolved/reopened governance pair | 当前已校验章节、示例、review command 和 Runtime 边界 | resolved/reopened 的治理日志跨文件一致性还可以更深 | 增强质量门禁 | 中；与上一轮相邻但价值递减 | benchmark integration | 无 | 后续按需 | 暂缓 |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 的“渐进式深入”和“智能化闭环”：LLM 自检已经存在，但建议动作仍不可机器约束。把动作类型结构化后，CLI 和 human-input reason 可以更稳定地把自检结果翻译成用户可执行输入。
2. B 暂不选，因为它主要是工程结构优化，对 Maintainer 当前 scan 对齐体验的直接价值弱于 A。
3. C 暂不选，因为它依赖外部 full regression / push 前置，不是本地实现 milestone。
4. D 暂不选，因为上一轮已经补齐 human-input 的核心质量门禁，本轮应推进另一个仍弱的 LLM 契约点。

## 本轮 Milestone

作为 Harness Maintainer，当首次 guided `init` 的 LLM 二次自检判断某个扫描追问仍需处理时，我可以看到一个稳定的结构化动作类型和对应输入提示，例如补 `stack`、`module`、`command`、`risk`、复核 evidence 或运行 targeted scan；同时 Harness Builder 会拒绝缺少结构化动作的新 LLM self-check 响应，从而避免把不可消费的自由文本建议伪装成可审计结论。

## 验收标准

1. `ScanSelfCheckResolution` 新增结构化动作字段，旧 persisted metadata 缺字段仍能读取，但 fresh LLM parser 必须要求每个 resolution 显式返回该字段。
2. 结构化动作必须是有限枚举，例如 `provide_stack`、`provide_module`、`provide_command`、`provide_risk`、`review_current_evidence`、`run_targeted_scan`、`maintainer_review`。
3. Prompt 示例和字段要求必须明确枚举动作类型，要求 LLM 不能只给自由文本。
4. Parser 对未知 interaction id、未知 evidence source 的既有校验保持不变，并新增缺结构化动作时显式失败。
5. Guided CLI 的“LLM 二次自检”输出必须展示动作类型和对应低负担提示；questionnaire reason 必须保留 action type，便于 `.ai/human-input-needed.md` 后续审计。
6. 不自动修改 ProjectInventory、CommandCatalog、Guides、Sensors、Workflow routing 或 Runtime；不创建 `.ai/task-runs`。
7. 更新 README / `docs/engineering/llm-contracts.md` / `docs/engineering/init-workflow.md` 中的稳定契约说明，并记录 evolution log。

## 设计决策

- Schema 字段命名为 `suggested_action_type`，保留原 `suggested_next_action` 作为人类说明；不把动作类型藏在自然语言里。
- Pydantic schema 为旧 metadata 提供默认值 `maintainer_review`，但 `parse_scan_self_check_response()` 对 fresh LLM payload 执行显式必填检查，避免 silent default 包装新响应。
- CLI 使用轻量 helper 把 action type 翻译成输入提示，不把 self-check 动作直接写成正式 Harness 变更。
- 本轮不新增 benchmark 检查；self-check 已经由 `scan-metadata.yaml` schema 和 LLM parser 契约保护。

## Assumptions / Risks

- Assumption：动作类型只是下一步意图，不代表 Builder 已执行动作；`run_targeted_scan` 仍是未来能力或人工路径，不在本轮实现真实 targeted scan。
- Risk：真实 LLM 可能一开始漏字段；prompt 和 parser 会让它显式失败，而不是默认成功。真实 acceptance 需在 push 前 full regression 中覆盖。
- Risk：旧 metadata 缺字段时默认 `maintainer_review`，这是兼容读取旧产物；fresh parser 的显式检查避免新 LLM 响应 silent fallback。

## Sub Agent 使用

本轮尝试启动 explorer 做只读审查，当前环境返回 `agent thread limit reached`。主线程继续完成调研、TDD、实现、验证和提交。
