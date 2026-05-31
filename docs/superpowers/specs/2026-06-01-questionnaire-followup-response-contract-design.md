# Questionnaire Follow-up 回应状态契约设计

## Current State Gap Analysis

事实源快照：

- 已读取：`AGENTS.md`、`README.md`、`docs/strategy/README.md`、`docs/strategy/goal-mode-playbook.md`、`docs/engineering/init-workflow.md`、`docs/engineering/testing-strategy.md`、`docs/engineering/llm-contracts.md`、`docs/strategy/init-north-star.md`、全景 North Star、`docs/todos/README.md`、`docs/evolution-log.md`、上一轮 scan follow-up supplement status spec / plan。
- 已核对代码：`schemas/human_confirmation.py`、`tools/human_confirmation.py`、`tools/interactive_init.py`、`tools/write_assets.py`、`tests/unit/test_human_confirmation.py`、`tests/unit/test_interactive_init_preview.py`、`tests/integration/test_init_on_fixture_projects.py`。
- 按需未展开：`architecture.md`、`sensor-and-gate-rules.md`。本轮不改模块边界、benchmark gate 或 Sensor 规则。
- 当前 todo 状态：`docs/todos/README.md` 显示没有 open todo；本轮从 init North Star 和上一轮 Self-Harness Gate 候选重新选择。

候选 gap：

| 候选 | 来源 | 目标态 | 当前能力 | 缺口 | 价值 | 风险/复杂度 | 可测试性 | 依赖项 | 验收方式 | 去向 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Questionnaire follow-up 回应状态机器契约 | 上轮 Gate / 新发现 | scan follow-up 是否被同轮 scan supplement 部分回应，能被 schema 稳定读取，并在已有 Harness 维护入口显示计数 | 上轮已在 `scan_followup_confirmation.reason` 追加“可能已部分回应”说明 | 状态只在自然语言 reason 中，后续维护入口 / self-improve / 审计无法稳定识别 | 把用户补充闭环从可读说明升级为可消费契约；再次进入 init 能看到 partially addressed 计数 | 中低；新增可选 Pydantic 字段和维护入口摘要，不改变正式事实 | schema / unit / guided integration / existing Harness preview | 依赖上一轮 `interaction_decisions` 传入 questionnaire | 本轮 |
| B. Workflow note review-only routing candidate 安全设计 | 上轮 Gate | workflow note 可生成 review-only routing 改进候选，仍不改正式 policy | workflow note 已有结构化 impact/review-only 边界 | 尚无自由文本到结构化 `workflow_policy_patch` 的安全候选化路径 | 更接近 Workflow Toolkit 定制闭环 | 中高；涉及候选 schema、patch 安全、benchmark 和治理 | candidate schema / integration / benchmark | 需要谨慎设计 patch 生成边界 | 后续候选 |
| C. push 前 full regression / 远端同步 | Gate / git 状态 | 本地完整工作包经 full regression 后 push | 当前 `main` 本地领先 `origin/main` 26 个 commit | 本轮仍在增量目标模式开发，尚未形成新的 push 边界 | 降低远端分叉风险 | 中；可能依赖 DeepSeek、真实仓库、网络和 GitHub 访问 | `scripts/test-full.sh` + push 结果 | 外部凭证 / 网络 / 完整工作包判断 | 后续工作包 |

排序结论：

1. 选择 A，因为它直接补上一轮 Gate 发现的契约短板：用户补充已被吸收，但机器只能解析 reason 文本。`init-north-star.md` 要求关键用户输入留下可消费结果；本轮让 questionnaire schema 与已有 Harness 维护入口都能消费该状态。
2. B 暂不选，因为从 workflow note 生成 `workflow_policy_patch` 容易跨越 review-only 边界，需要比本轮更完整的安全设计。
3. C 暂不选，因为本轮未形成适合 push 的完整远端工作包；push 前仍需 full regression。

## 本轮 Milestone

作为 Harness Maintainer，当我再次运行 guided `init` 查看已有 Harness 的 human-input 信号时，我可以看到 scan follow-up 中有多少项已被上一次 guided `init` 的 scan supplement 部分回应、多少仍待确认；同时后续 Self-Improve / 审计链路可以通过 `questionnaire.yaml` 的结构化字段读取该状态，而不是解析自然语言 reason。

## 设计

### Questionnaire schema

给 `QuestionnaireQuestion` 增加默认兼容字段：

- `response_status`: `unaddressed | partially_addressed_by_current_scan_supplement`
- `response_sources`: `list[str]`

默认值：

- 旧 questionnaire 或非 scan follow-up 问题默认 `response_status=unaddressed`、`response_sources=[]`。

当 `build_questionnaire()` 判定某个 follow-up 被当前 scan supplement 部分回应时：

- `response_status=partially_addressed_by_current_scan_supplement`
- `response_sources` 写入稳定摘要，例如 `command=unit_test:mvn test`、`module=src/main/java`、`risk=src/main/java/...`
- `reason` 继续保留面向人的说明和 `pending_harness_maintainer_review` 边界。

### Existing Harness 维护入口

`_human_input_needed_status_lines()` 读取 `Questionnaire` schema 后增加：

- `human_input_scan_followups_partially_addressed=<count>`
- `human_input_scan_followups_unaddressed=<count>`

计数范围只覆盖 `interaction_type == scan_followup_confirmation`，不混入 scan warning / risk area / evidence expansion。

### 边界

- 不把 partial response 当作 resolved。
- 不删除任何 `scan_followup_confirmation`。
- 不修改正式 `ProjectInventory` / `CommandCatalog` / `HarnessConfig` 语义。
- 不生成 workflow policy candidate。
- 不执行 Runtime，不创建 `.ai/task-runs`。

## 验收标准

1. `QuestionnaireQuestion` schema 接受新增字段，并对旧 payload 使用默认值。
2. `build_questionnaire()` 在 matching scan supplement 场景下写入 `response_status=partially_addressed_by_current_scan_supplement` 和稳定 `response_sources`；unrelated supplement 保持 `response_status=unaddressed`。
3. guided init integration 证明 `.ai/questionnaire.yaml` 包含结构化 response 字段，`human-input-needed.md` 仍保留可读 reason 和处理入口。
4. `_human_input_needed_status_lines()` 对已有 Harness 的 questionnaire 输出 partial / unaddressed follow-up 计数。
5. 文档同步 `docs/engineering/init-workflow.md` 和 `docs/evolution-log.md`。
6. 按 TDD 先看目标测试失败，再实现；提交前运行目标测试、完整 guided init integration、`git diff --check` 和 `scripts/test-fast.sh`。

## Assumptions / Risks

- Assumption：`response_status` 先只表达当前 Builder 可证明的状态：未回应或被本轮 scan supplement 部分回应。完整 resolved 需要后续 Maintainer 明确确认或 targeted scan，不在本轮新增。
- Risk：字段名未来可能扩展到其他 interaction 类型；本轮保持通用字段，但只有 scan follow-up writer 设置非默认值。
- Risk：维护入口计数可能让用户误解为“已解决”；因此命名使用 `partially_addressed`，并在 reason 中保留 pending review。

## Sub Agent

按目标模式尝试启动只读 explorer 审查最小安全改动路径，但当前环境返回 `agent thread limit reached`；本轮由主线程完成调研、TDD、实现和验证。
