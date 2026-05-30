# Wizard Human Confirmation Design

## 背景

`docs/ideas/wizard-style-human-confirmation.md` 提出 Harness Builder 不能只依赖代码扫描。团队规范、架构约束、测试策略、代码风格通常存在于外部文档或团队经验中；低置信度推断如果直接写进正式 Harness，会降低用户信任。

当前 POC 已生成候选态 guide/sensor，并在 frontmatter 中标记 `needs_human_confirmation: true`，但还缺少两个能力：

- 用户如何把组织级上下文提供给 `init`。
- 系统如何结构化告诉用户“哪些地方需要确认”。

## 目标

为 `init` 增加轻量向导式确认基础：

1. 支持 `harness-builder-agent init --context <path>`，可重复传入多个上下文文件。
2. 在 `.ai/context-inputs.yaml` 记录用户传入的上下文文件摘要。
3. 在 `.ai/questionnaire.yaml` 生成结构化确认问题。
4. 在 `.ai/human-input-needed.md` 生成中文人工确认清单。
5. 在 generation trace 中记录 context 和 questionnaire 产物。

## 非目标

- 不做完整交互式问答 UI。
- 不在本轮实现 `init --update` 的 merge/覆盖策略。
- 不把用户上下文直接提升为 confirmed 规则；本轮只把它们作为 `provided_context` 来源记录下来。
- 不要求 LLM 基于 context 重新生成第二轮输出；后续可把 context 注入 scan prompt。

## CLI 设计

```bash
harness-builder-agent init --repo <repo> --context docs/team-rules.md --context docs/test-policy.md
```

行为：

- `--context` 可重复。
- 路径必须存在且是文件。
- 上下文文件只记录摘要：路径、字节数、前 1200 字符预览、是否截断。
- 未传 `--context` 时仍生成空的 `context-inputs.yaml`，并在 questionnaire 中提示可补充组织规范。

## 产物

### `.ai/context-inputs.yaml`

```yaml
schema_version: '1.0'
contexts:
  - path: docs/team-rules.md
    size_bytes: 320
    summary: 团队要求所有 Controller 只能调用 Service...
    truncated: false
```

### `.ai/questionnaire.yaml`

```yaml
schema_version: '1.0'
questions:
  - interaction_type: low_confidence_confirmation
    interaction_id: confirm:team-context
    question: 是否有组织级架构规范、代码规范或测试策略需要加入 Harness？
    options:
      - 提供 --context 文档后重新运行 init
      - 暂时保持候选状态
    confidence: low
    reason: 当前 init 未收到外部团队上下文。
  - interaction_type: candidate_asset_confirmation
    interaction_id: confirm:guide-candidates
    question: 是否将候选 Guides 提升为团队确认规则？
    options:
      - 保持 candidate
      - 人工确认后提升为 confirmed
    confidence: medium
    reason: Guides 当前由扫描、武器库和模型建议生成，尚未经过维护者确认。
```

### `.ai/human-input-needed.md`

中文可读文件，包含：

- 已提供上下文。
- 待确认问题。
- 候选资产状态说明。
- 下一步建议命令。

## 数据状态

本轮只使用这些状态：

- `detected`：扫描出的事实。
- `provided_context`：用户通过 `--context` 输入的文档。
- `candidate`：系统生成但待确认的 guide/sensor/workflow 建议。

后续版本再引入：

- `confirmed`
- `customized`
- `rejected`

## 生成规则

Questionnaire 至少包含：

1. `confirm:team-context`
   - 无 context 时提示用户补充。
   - 有 context 时提示用户确认这些 context 是否可作为 Harness 输入。
2. `confirm:guide-candidates`
   - 提醒用户候选 Guides 尚未正式确认。
3. `confirm:sensor-gates`
   - 提醒用户 hard gate sensors 需要在本机和 CI 中确认稳定性。

如果 scan metadata 中存在 warning，则每个 warning 生成一条 `scan_warning_confirmation`。

## 测试策略

单元测试：

- context reader 能读取文件摘要并标记 truncated。
- questionnaire builder 能根据 context 有无、scan warnings 和 command catalog 生成问题。

集成测试：

- `init --context docs/team-rules.md` 会生成 `context-inputs.yaml`、`questionnaire.yaml`、`human-input-needed.md`。
- 文件字段级断言：schema、questions、interaction_id、confidence、reason。
- 未提供 context 时，也应生成 `confirm:team-context`。

Benchmark：

- 新增 `schema:questionnaire` 和 `content:human-confirmation` 检查。

## 验收标准

- 默认测试通过。
- 真实 DeepSeek fixture acceptance 通过。
- 真实开源仓库 e2e 通过。
- 用户运行 `init --context <file>` 后，能在 `.ai/human-input-needed.md` 看见上下文摘要和待确认事项。

