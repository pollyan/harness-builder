# Human Input 深度追问处理建议设计

## 背景

上一轮已经在首次 guided `init` 的 scan supplement 前展示“深度追问回答建议”，把 `ScanMetadata.followup_questions` 的 trigger 映射成自然语言或 `stack` / `module` / `command` / `risk` 示例。这解决了用户当场输入时的低负担问题。

但 `init` 生成后的 `.ai/human-input-needed.md#处理方式` 仍然只给 scan follow-up 一个泛化建议：重新进入 guided `init`，补充 `stack=...`、`module=...`、`command=...` 或 `risk=...`，再用 `review-human-input` 标记。用户如果当场跳过、把结果交给团队，或后续从已有 Harness 维护入口回访，就需要重新从问题文本推断该用哪类补充。

这使“动态追问 -> 会后处理 -> 显式治理”的链路不够顺滑。`init-north-star.md` 要求 Markdown 产物承担审计、交付和后续维护材料；因此持久化处理入口也应保留同一套可行动建议。

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`docs/evolution-log.md`、上一轮深度追问回答建议 spec / plan。
- 已检查代码：`human_confirmation.py`、`guided_scan_presentation.py`、`asset_writers/human_confirmation.py`、`benchmark.py`、`tests/unit/test_human_confirmation.py`、`tests/unit/test_asset_writer_human_confirmation.py`、`tests/integration/test_init_on_fixture_projects.py`。
- 按需未展开：LLM prompt、scan reconciler、benchmark quality scoring；本轮不改扫描判断、LLM 调用、schema 或 benchmark。
- Sub agent：按 playbook 尝试启动只读 explorer 审查 human-input 生成链路，当前环境返回 `agent thread limit reached`；本轮由主线程完成调研、TDD 和实现。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. human-input follow-up action guidance | 上一轮 Gate / init North Star | `.ai/human-input-needed.md#处理方式` 对每个 scan follow-up 保留具体回答建议和结构化示例 | CLI 已有“深度追问回答建议”；human-input 有通用处理方式和 review-human-input 命令 | 会后处理入口没有按 trigger 给示例，团队接手时仍要自己翻译问题 | 补齐“跳过问题 -> 持久化待确认 -> 可执行处理 -> 显式复核”的闭环 | 低；Markdown 文案和共享 helper，不改 schema / writer 契约 | unit markdown、asset writer unit、guided integration artifact | 依赖上一轮 trigger guidance 稳定化 | `.ai/human-input-needed.md#处理方式` 包含 per-id 示例、不自动关闭边界和 review-human-input 命令 | 本轮 |
| B. self-check suggested action 结构化约束 | 上一轮 Gate | LLM self-check 的 suggested next action 可被机器稳定分类为补充类型 | self-check action 只是自然语言，questionnaire reason 会保留 | 无法从 action 直接推断更准确的处理动作 | 提升智能化，但需要 LLM schema / parser / acceptance 风险 | 中；涉及 schema、prompt、parser 和真实 LLM | schema / LLM parser / scan repo / acceptance | 需要产品确认 action taxonomy | 后续候选 |
| C. benchmark 校验 human-input 处理方式深度 | 新发现 | benchmark 能防止 `.ai/human-input-needed.md#处理方式` 丢失 scan follow-up 处理建议 | benchmark 只检查 init-summary 引用 human-input 入口 | human-input markdown 漂移不会被 content check 捕获 | 提升契约稳定性 | 中；新增 content check 需要定义所有 interaction type 规则 | benchmark integration | 依赖 A 的内容稳定 | 后续 benchmark hardening | 下一轮候选 |
| D. push / full regression 工作包 | 远端同步候选 | 将本地已完成工作包同步远端 | 当前本地 ahead 61 | push 前需要 full regression 和 acceptance 前置，不是本轮 init 体验最小闭环 | 同步价值高 | 高；可能依赖 DeepSeek / `.benchmarks` | `scripts/test-full.sh`、push | 外部凭证 / 真实仓库 | 独立同步工作包 | 暂不进入本轮 |

排序结论：

1. 选择 A，因为它直接延续上一轮已稳定的 CLI guidance，让同一个 scan follow-up 用户故事在持久化材料中也成立；它不改 LLM、schema、benchmark 或 Runtime，风险小且价值明确。
2. B 有长期价值，但需要修改 LLM self-check 契约，不适合紧跟一个 Markdown 体验切片混做。
3. C 应等 A 的文案稳定后再做，避免 benchmark 先锁住还在调整的表达。
4. D 保持为独立同步工作包，不和本轮产品切片混合。

本轮 milestone：

作为 Harness Maintainer，当我在首次 `init` 后查看 `.ai/human-input-needed.md#处理方式` 处理未解决或部分回应的 scan follow-up 时，我可以看到每个 follow-up 对应的具体补充建议和可复制示例，并继续通过 `review-human-input` 显式标记 resolved / reopened，从而让会后处理和已有 Harness 回访不依赖临时终端输出。

## 设计

### 共享 guidance helper

将上一轮 `guided_scan_presentation.py` 中的 trigger guidance 抽成轻量 helper：

- 新增 `tools/scan_followup_guidance.py`。
- 提供 `scan_followup_answer_guidance_line(question)` 和 `scan_followup_answer_guidance_lines(questions, limit=5)`。
- helper 不依赖 Typer、LLM、writer 或 schema，只处理 dict payload。
- guided CLI 和 human-input markdown 共用同一套确定性映射，避免两份文案漂移。

### Human Input Markdown

更新 `_scan_followup_action_guidance()`：

- 对 `scan_followup_confirmation` 读取 `trigger`。
- 在 generic “重新进入 guided init” 建议前或后追加“建议补充”片段。
- 对 resolved 状态仍以 resolved 边界为主，但可以保留“如需重新打开”的命令，不再要求补充示例。
- 对 partial 状态继续提示先人工复核是否足够关闭。
- 明确补充不会自动关闭追问，不会把用户输入伪装成已验证 evidence。

### 非目标

- 不新增 `Questionnaire` 字段；trigger 已经在 schema payload 中保留。
- 不修改 `response_status` 状态机。
- 不修改 `review-human-input` 命令语义。
- 不新增 benchmark content check。
- 不执行 Runtime，不创建 `.ai/task-runs`。

## 验收标准

1. unit：`human_input_markdown()` 对 coverage / stack / test scan follow-up 在 `## 处理方式` 中输出对应 id、结构化示例和“不自动关闭”边界。
2. unit：guided scan presentation 继续输出同一套回答建议，证明 helper 抽取没有破坏 CLI。
3. integration：首次 guided `init` 生成的 `.ai/human-input-needed.md` 对 follow-up question 包含 trigger-specific 示例，并保留 questionnaire / self-check 信息。
4. 文档：README 和 `docs/engineering/init-workflow.md` 同步说明 `.ai/human-input-needed.md#处理方式` 会保留具体 follow-up 处理建议。
5. 验证：targeted unit / integration、`compileall`、`git diff --check` 和 `scripts/test-fast.sh` 通过后提交。

## Assumptions / Risks

- 示例仍是输入格式帮助，不代表目标仓库真实存在这些路径或命令。
- Markdown 变长，但只对存在 scan follow-up 的问题增加可行动说明。
- 本轮不让 benchmark 锁定新文案，避免过早把表达形式硬编码成质量门；如后续出现漂移，再单独做 benchmark hardening。
