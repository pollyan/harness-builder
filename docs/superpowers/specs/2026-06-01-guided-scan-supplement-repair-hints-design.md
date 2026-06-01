# Guided Scan 结构化补充修正提示

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/architecture.md`、`docs/strategy/init-north-star.md`、全景规划开篇与 Runtime 边界、`docs/todos/README.md`、当前 `docs/superpowers/specs` / `plans` 索引、`guided_scan_supplements.py`、相关 unit / integration tests、`docs/evolution-log.md`。
- 按需未展开：`docs/engineering/llm-contracts.md` 与 `sensor-and-gate-rules.md`，本轮不修改 LLM、Prompt、schema、benchmark 或 Sensor 规则。
- Todo 状态：`docs/todos/README.md` 显示当前没有 open todo；`local-unique-capability-migration.md` 已是 implemented，本轮不再继续旧 61 个提交迁移。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 结构化 scan 补充修正格式提示 | init North Star / 上轮 Gate | 用户输错 `module` / `command` / `risk` / `stack` 时，CLI 不只说明未生效，还给出可复制的正确格式 | 解析器已显式说明片段没有进入 inventory / command catalog / risk hints，只作为自然语言保留 | 缺少“下一次怎么写才会生效”的格式提示；用户仍要回头找 prompt 或 README | 降低 guided init 输入成本，避免用户误以为结构化补充生效，并让同一轮可以快速返回修改 | 低；只改解析诊断文案和测试，不改 schema / writer / LLM | unit 覆盖四类 invalid fragment；integration 覆盖 guided init CLI 与 decisions note | 无外部依赖 | CLI immediate summary 和 `interaction-decisions.yaml` notes 均包含未生效边界与可用格式 | 本轮 |
| B. 团队规则 / Workflow 补充 renderer 抽取 | 上轮 Gate / 工程架构 | 继续缩小 `interactive_init.py`，让补充展示逻辑可单测 | scan presentation 已抽取，但 team / workflow / supplement impact 展示仍在主状态机 | 后续打磨团队规则与 Workflow 补充时仍要改主向导文件 | 降低后续迭代误伤风险 | 中；行为保持重构但搬迁函数较多 | 新 renderer unit + targeted guided integration | 无 | transcript 不变，`interactive_init.py` 继续缩小 | 下一轮候选 |
| C. push / 远端同步 | 交付节奏 | 完整工作包通过 full regression 后统一 push | 本地领先远端多个提交，迁移工作包已收口 | push 前 `scripts/test-full.sh` 仍依赖 `DEEPSEEK_API_KEY` 和真实 `.benchmarks/*` | 让远端获得当前阶段成果 | 高；外部凭证 / 真实仓库缺失会阻塞 | full regression + push + 可选 CI 查询 | DeepSeek key、真实仓库 | `scripts/test-full.sh` 通过后 push | 外部前置满足后处理 |

排序结论：

1. 选择 A，因为它直接服务 `init-north-star.md` 的“对结构化修正提供清晰示例和容错提示”，属于首次 guided init 的用户可感知纵向体验切片；实现小、风险低、可用 unit + integration 证明。
2. B 仍有价值，但本轮若只做重构，用户输入体验没有进一步改善；保留为下一轮工程信任候选。
3. C 不进入本轮，因为 push 需要 full regression，而当前已知外部 acceptance 前置不足；继续保持本地提交节奏。

本轮 milestone：

作为 Harness Maintainer，当我在首次 guided `init` 的扫描对齐阶段输入格式不完整或字段非法的结构化补充时，我可以立即看到该片段没有进入结构化资产，并看到可复制的正确格式示例，从而能低成本修正输入并信任 Harness 没有把错误补充伪装成已验证事实。

## 验收标准

1. `parse_guided_scan_supplement()` 对 invalid `stack`、`module`、`command`、`risk` 片段都返回中文诊断 note，包含：
   - 原始片段。
   - 未进入的结构化目标。
   - 只作为自然语言补充保留。
   - 对应的 `可用格式：...` 示例。
2. 合法结构化片段行为不变：仍更新 `GuidedScanOverrides` 的 primary stack、modules、commands、risk areas。
3. 自然语言补充行为不变：不会被误报为结构化错误。
4. guided `init` immediate summary 会显示 invalid `command=` 的可用格式提示，`interaction-decisions.yaml` notes 也保留该提示；command catalog 不会新增非法 command。
5. README 与 `docs/engineering/init-workflow.md` 同步稳定行为：格式错误会说明未进入结构化资产，并给出可用格式提示。
6. 不修改 LLM、schema、writer、benchmark、Runtime 分工，不创建 `.ai/task-runs`。
7. 验证命令：
   - `tests/unit/test_guided_scan_supplements.py`
   - invalid structured guided init integration
   - `git diff --check`
   - `scripts/test-fast.sh`

## 决策 / 取舍

- 将格式提示保留在 parser 生成的 note 中，而不是只改 prompt 文案。原因是 note 会进入 immediate summary、prewrite preview、interaction decisions 和后续审计链路，能证明错误片段没有结构化生效。
- 不新增 `GuidedScanOverrides` 字段。当前机器契约已经能表达合法结构化补充，invalid fragment 属于用户输入诊断，放入 notes 最小且兼容。
- 不对非法 command 的第 6 个 confidence 字段做额外严格失败；现有逻辑会把非法 confidence 降为 `medium`，本轮不扩大行为范围。

## Assumptions / Risks

- Assumption：诊断 note 增加格式示例会进入语义资产，文本略长但比静默不指导更符合 guided init 低负担原则。
- Risk：测试如果只断言局部片段，可能漏掉 notes 文案漂移；因此 unit 对关键格式进行明确断言，integration 覆盖 CLI 与 decisions note。

## Sub Agent

按 playbook 尝试启动 explorer 做只读复核，但当前会话返回 `agent thread limit reached`。本轮由主线程完成调研、实现和验证，并在 Self-Harness Gate 中记录该限制。
