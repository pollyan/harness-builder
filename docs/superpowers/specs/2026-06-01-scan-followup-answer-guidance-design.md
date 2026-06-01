# 深度追问回答建议设计

## 背景

当前首次 guided `init` 已经能在扫描补充前展示 `ScanMetadata.followup_questions` 的“深度追问”，并在存在 `ScanMetadata.self_check` 时展示“LLM 二次自检”。这些能力解决了“系统发现了哪些不确定点”和“LLM 是否二次审查过这些不确定点”。

但用户看到问题后马上要输入 scan supplement。当前 CLI 只在通用提示中列出 `stack=`、`module=`、`command=`、`risk=` 格式，没有把每个追问映射成可复制、可理解的回答方式。对于第一次使用的 Harness Maintainer 来说，这仍然要求他们自己从问题反推内部补充格式，违背 `init-north-star.md` 中“交互低负担”和“对结构化修正提供清晰示例”的目标。

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`docs/evolution-log.md`。
- 已检查代码：`guided_scan_presentation.py`、`interactive_init.py`、`human_confirmation.py`、`tests/unit/test_guided_scan_presentation.py`、`tests/integration/test_init_on_fixture_projects.py`。
- 按需未展开：benchmark scoring、existing Harness action runner、LLM prompt 细节；本轮不改 schema、LLM 调用、benchmark 或已有 Harness 维护入口。
- Sub agent：按 playbook 尝试启动只读 explorer 审查 follow-up / self-check 展示链路，当前环境返回 `agent thread limit reached`；本轮由主线程完成调研、TDD 和实现。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. 深度追问回答建议 | init North Star / 本轮新发现 | 用户看到每个深度追问后，能立刻知道可以用自然语言或 `stack` / `module` / `command` / `risk` 哪类补充回应 | CLI 已展示深度追问和 LLM 二次自检，收集 scan supplement 前有通用格式提示 | 追问和补充格式没有逐项关联，用户仍要自己翻译问题 | 降低首次 init 输入成本，让动态追问真正变成可行动协作，而不是只读待办 | 低；只改 CLI renderer 和文档，不改 schema / LLM / writer | unit renderer、guided integration transcript、文档 diff | 无外部凭证 | CLI 在 scan supplement 前展示“深度追问回答建议”、每类追问对应示例、review-only 边界；现有 questionnaire 链路不漂移 | 本轮 |
| B. follow-up 回答建议写入 human-input action guidance | Gate 延伸 | 生成后的 `.ai/human-input-needed.md` 也能逐项给出更具体回答建议 | human-input 已有 generic scan follow-up guidance 和 `review-human-input` 命令 | 文档端仍偏通用 | 有利于会后处理，但不如首次输入前即时帮助关键 | 低到中；需要小心不要扩大 Markdown 契约 | unit + integration artifact assertion | 依赖 A 的 renderer 规则稳定化 | 作为后续文档端增强候选 | 下一轮候选 |
| C. follow-up 建议与 self-check resolution 结构化绑定 | 智能化闭环延伸 | self-check 的 suggested next action 能被 Python 转成更准确的补充建议 | self-check 已展示 status / action / rationale | action 仍是自然语言，不形成 answer guidance 的稳定输入 | 提升智能化，但需要约束 LLM 输出语义 | 中；涉及 LLM schema 或 parser 约束 | schema / LLM parser / transcript | 需要先验证 A 的确定性映射是否够用 | 后续 schema hardening | 后续候选 |
| D. push / full regression 工作包 | 远端同步候选 | 完整本地工作包 push 到远端 | 本地领先 origin/main 60 个提交 | 需要 full regression 和 acceptance 前置，且当前目标继续要求推进 init North Star | 同步价值高，但不是本轮最贴近首次 init 体验的产品切片 | 高；可能依赖 DeepSeek / `.benchmarks` 外部状态 | `scripts/test-full.sh`、push 结果 | 外部凭证 / 真实仓库 | 独立同步工作包处理 | 暂不进入本轮 |

排序结论：

1. 选择 A，因为它直接发生在首次 guided `init` 的扫描理解对齐阶段，用户马上要输入补充；相比 B，它更靠前、更能减少交互摩擦；相比 C，它不需要扩大 LLM 或 schema 契约；相比 D，它更符合当前短中期 `init-north-star.md` 优先级。
2. B 保留为后续候选：如果本轮 CLI 建议稳定，再考虑把同一套建议写入 `.ai/human-input-needed.md`。
3. C 需要更明确的 self-check action schema，不适合在本轮用自然语言推断事实。
4. D 留给完整同步工作包，不和本轮产品切片混做。

本轮 milestone：

作为 Harness Maintainer，当我首次 guided `init` 一个存在扫描深度追问和二次自检的仓库时，我可以在输入 scan supplement 前看到每个追问对应的低负担回答建议和可复制结构化示例，从而知道该用自然语言、`stack=`、`module=`、`command=` 或 `risk=` 补充什么，并理解这些补充只会部分回应追问、不会自动关闭人工复核。

## 设计

### CLI 呈现

在 `guided_scan_presentation.py` 中新增深度追问回答建议 renderer：

- 仅当 `scan_metadata.followup_questions` 非空时展示。
- 位置放在“LLM 二次自检”之后、“风险区域”之前，保证用户先看到问题和二次自检，再看到如何回答。
- 标题稳定为 `深度追问回答建议`。
- 每条建议包含 follow-up interaction id、对应补充类型和示例：
  - `coverage_gap`：建议补充关键模块路径或高风险路径，例如 `module=src/main/java|backend|核心模块` / `risk=src/main/java/payments|支付或权限高风险`。
  - `stack_claim_without_evidence` / `unknown_stack`：建议补充真实技术栈，例如 `stack=java-spring`。
  - `module_boundary_unclear`：建议补充模块边界，例如 `module=src/main/java|backend|核心业务`。
  - `test_evidence_missing`：建议补充验证命令，例如 `command=unit_test|mvn test|test|hard|pom.xml|high`。
  - 其他 trigger：建议用自然语言说明真实边界，并可按需使用结构化格式。
- 结尾明确边界：这些补充会进入本轮 scan supplement / questionnaire 回应状态，但不会自动关闭追问；仍需 `review-human-input` 复核。

### 非目标

- 不修改 `ScanMetadata`、`Questionnaire` 或 `interaction-decisions.yaml` schema。
- 不把用户补充自动标记为 verified evidence。
- 不从 LLM self-check 自然语言中推断结构化事实。
- 不改 `.ai/human-input-needed.md` 的稳定章节，本轮只做扫描补充前的 CLI 即时帮助。
- 不改 benchmark、asset writer、Runtime 契约或已有 Harness 维护入口。

## 验收标准

1. unit renderer：给定包含 coverage / stack / unknown stack / module / test follow-up 的 inventory，输出包含 `深度追问回答建议`、对应 interaction id、结构化示例和 review-only 边界。
2. guided integration：首次 guided `init` 的 transcript 在收集 scan supplement 前包含回答建议，并且后续 `questionnaire.yaml` / `human-input-needed.md` 仍保留原有 follow-up 与 self-check 信息。
3. 文档：README 和 `docs/engineering/init-workflow.md` 同步说明 guided `init` 会把深度追问翻译成可回答建议，且补充不自动关闭人工复核。
4. 验证：targeted unit / integration、`compileall`、`git diff --check` 和 `scripts/test-fast.sh` 通过后提交。

## Assumptions / Risks

- 这些示例是输入格式帮助，不是对用户仓库的事实判断；示例路径使用常见占位，不声明真实存在。
- 输出略增加，但只在存在 follow-up questions 时出现，且发生在用户最需要输入帮助的阶段。
- 本轮不把建议写入 Markdown 产物，避免先扩大 artifact 契约；如果后续发现会后处理同样困难，再按新 milestone 扩展 human-input guidance。
