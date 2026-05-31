# Guided Init LLM Evidence Plan 可见化设计

## 背景

上一轮已经把 LLM evidence planner 的 `requested_paths`、`risk_focus`、`rationale`、`confidence` 和实际读取结果写入 `.ai/scan-metadata.yaml`。这解决了机器审计问题，但首次 guided `init` 的主界面仍只展示通用的扫描不确定性，用户需要事后打开 YAML 才能知道：

- LLM 为什么要求补读文件。
- 哪些文件实际被安全读取。
- planner 低置信度为什么会影响扫描可信度。
- 这个低置信度是否进入后续人工确认清单。

这和 `init-north-star.md` 的 CLI-first、可解释、渐进式协作目标仍有缺口。Markdown 和 YAML 是审计材料，CLI 才是首次初始化过程中的主要对齐界面。

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/strategy/init-north-star.md`、全景规划、`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`、`docs/todos/README.md`、`docs/todos/guided-init-ai4se-real-repo-findings.md`、`docs/todos/maturity-driven-init-wizard.md`、近期 spec / plan / evolution log、`interactive_init.py`、`human_confirmation.py`、相关测试。
- 按需未展开：`docs/engineering/architecture.md`、`sensor-and-gate-rules.md`，本轮不调整模块边界、Sensor hard gate 或 benchmark 规则。

候选 gap：

| 候选 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Guided CLI 展示 LLM evidence plan | 用户在扫描发现阶段看到 planner 补读原因、请求路径、实际读取路径和低置信度影响 | metadata 已落盘，progress 已显示 “请求 LLM 规划补充 evidence” | CLI 不展示 `evidence_expansion` 细节，低置信度只以通用 warning 表达 | 让 Maintainer 在补充输入前理解深度扫描覆盖边界和应确认的路径 | 低，主要是展示与 questionnaire 映射，不改 schema 主链路 | integration transcript、unit questionnaire | 依赖上一轮 `ScanMetadata.evidence_expansion` | CLI 输出包含补读说明；低置信度进入待确认项和 `human-input-needed.md` |
| B. Claim-level support / conflict / unknown 调和 | LLM 对 stack/module/command/risk 的 claim 有逐条支持状态 | stack claim 已有有限验证，command evidence 有降级 | module/risk/config claim 仍多为自由 dict，缺少统一 support matrix | 提升扫描可信度，为下一步成熟度推荐提供更强 evidence | 中高，涉及 schema、reconciler、prompt、benchmark | unit / integration / acceptance | 需要设计 claim schema 和迁移 | 新增 claim validation report，并驱动 warnings / maturity |
| C. `LLMScanProposal` 中 modules/risk_areas 等字段结构化 | 机器消费字段有更强 schema，避免 LLM 返回任意 dict | 顶层 schema 有 Pydantic，部分字段仍是 `list[dict]` | 下游只能弱解析，测试难覆盖字段语义 | 降低真实 LLM 输出漂移风险 | 中，涉及 prompt 和多处测试 fixture | schema unit、LLM parser tests、integration | 需要同步真实 LLM prompt | 缺字段和类型错误显式失败，fixture 更新 |

排序结论：

1. 选择 A。它直接服务 init North Star 的“扫描结果友好呈现 / 可解释 / 渐进式协作”，继续完成上一轮 LLM-planned deep scan 的用户可见闭环，风险小且可独立验收。
2. B 保留为下一轮候选。它价值更大，但会触碰 schema 和 prompt，需要单独 spec，不能和本轮 CLI 可见化混在一起。
3. C 保留为下一轮候选或与 B 合并评估。它是工程信任切片，但用户价值不如 A 立即可见。

## Milestone

用户故事：

作为 Harness Maintainer，当我在大型或多栈仓库首次运行 guided `init`，且系统触发 LLM-guided evidence expansion 时，我可以在扫描发现阶段看到 LLM 补读了哪些文件、为什么补读、实际读到了哪些文件，以及低置信度补读计划为何需要人工确认，从而在补充上下文前校准扫描理解和风险边界。

## 设计

### CLI 展示

在 guided `init` 的“扫描发现”之后、“风险区域 / 不确定性 / 验证缺口 / 建议补充”之前，新增稳定分组：

```text
LLM 深度补充
- LLM 规划补读：`src/auth/AuthService.py`、`src/payment/RefundService.py`
- 关注原因：auth flow、refund flow
- 规划说明：认证和退款文件未进入初始源码摘要。
- 实际读取：`src/auth/AuthService.py`、`src/payment/RefundService.py`
- 置信度：low，需要人工确认这些文件是否代表真实关键路径。
```

如果没有 `evidence_expansion`，不额外输出该分组，避免旧 Harness 或无 planner 路径产生噪声。

如果 planner 请求了路径但实际读取为空，CLI 应明确说明“未读取到补充文件”，并建议用户确认路径或关键模块。这是警示，不是静默成功。

### 不确定性与待确认

现有 low-confidence planner warning 已进入 `scan_metadata.warnings`。本轮新增一个专门的 questionnaire 交互类型：

- `interaction_type`: `evidence_expansion_confirmation`
- `interaction_id`: `confirm:evidence-expansion`
- question 面向用户确认补读路径是否代表关键模块或风险路径。
- confidence 使用 planner confidence。
- reason 汇总 rationale、requested / read paths 和 risk focus。

如果 `evidence_expansion.confidence == "low"`，该问题必须进入 `.ai/questionnaire.yaml` 和 `.ai/human-input-needed.md`。中高置信度可以不新增问题，避免问卷过载。

### 非目标

- 不改变 LLM planner prompt、读取预算或 allowlist。
- 不新增第二轮 LLM scan。
- 不把低置信度 planner 自动升级为正式风险 rule。
- 不调整 benchmark scoring。
- 不把 `evidence_expansion` 作为所有旧 metadata 的必填字段。

## 验收标准

1. guided init transcript 在有 `evidence_expansion` 时展示 `LLM 深度补充` 分组，包含 requested paths、risk focus、rationale、read paths 和 confidence。
2. requested paths 存在但 read paths 为空时，CLI 显示“未读取到补充文件”或等价中文提示。
3. planner confidence 为 `low` 时，`.ai/questionnaire.yaml` 通过 schema 校验，并包含 `confirm:evidence-expansion`。
4. `human-input-needed.md` 包含 evidence expansion 待确认问题，说明补读路径和原因。
5. 无 `evidence_expansion` 的旧路径不新增空分组，现有 guided init 输出保持兼容。
6. 相关工程文档、todo 和演进记录同步本轮稳定决策。

## Assumptions / Risks

- Assumption：`ScanMetadata.evidence_expansion` 的 rationale 已由 planner prompt 控制为短文本，可以安全进入 CLI 和待确认文档。
- Risk：真实 LLM rationale 可能仍偏英文；本轮不做翻译，后续可通过 prompt 或渲染层统一中文化。
- Risk：questionnaire 新增 interaction type 会影响 schema；必须先更新 schema 和测试，再实现。

## Sub Agent 使用

本轮已启动一个 explorer 子代理做只读 gap 调研。主线程先推进 CLI / questionnaire 的明确切片；若子代理结果返回不同高优先级风险，会在 Self-Harness Gate 中记录或调整下一轮候选。
