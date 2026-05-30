# 向导式 Harness 生成与人机确认机制

状态：idea

来源：JiuwenSwarm Auto-Harness 调研 / 产品设计讨论 / 2026-05-30

相关范围：Harness Builder 交互设计、上下文收集、候选资产确认、增量更新

## 一句话

把 Harness Builder 设计成向导式对话过程：先扫描代码仓库，再针对低置信度信息向用户提问，并允许用户输入组织级规范、架构规范、代码规范和团队文档，最后把这些上下文用于生成更可信的 Harness。

## 为什么重要

- 代码扫描只能识别项目现状，不能完整推断团队共识。
- 组织级规范、架构约束、测试策略和代码风格通常存在于文档或团队经验里。
- 低置信度信息如果不确认，容易被错误写成正式规则。
- 用户参与确认后，生成出来的 guide、sensor、skill 更容易被信任和长期维护。
- 后续 `init --update` 或 `improve` 需要知道哪些内容是候选、已确认、被用户定制或被拒绝。

## 和 JiuwenSwarm 的差异

JiuwenSwarm 的人机确认主要是后置闸门：extension 生成并验证后，在 activate 前让用户 accept 或 reject。

Harness Builder 更需要前置和生成中的确认：

- 生成前：收集团队规范、架构文档、代码规范、测试要求。
- 生成中：针对低置信度推断提出问题。
- 生成后：让用户确认候选 guide、sensor、skill 是否进入正式 Harness。

## 可能形态

- `harness-builder-agent init --interactive`
- `harness-builder-agent init --context docs/team-rules.md`
- `harness-builder-agent init --non-interactive`
- `.ai/human-input-needed.md`
- `.ai/questionnaire.yaml`
- `.ai/review/candidate-guides.md`
- `.ai/review/candidate-sensors.md`

## 交互请求的结构化字段

```yaml
interaction_type: low_confidence_confirmation
interaction_id: confirm:test-command
question: "检测到多个测试命令，哪个是团队推荐命令？"
options:
  - mvn test
  - mvn verify
  - ./mvnw test
confidence: 0.62
reason: "pom.xml 存在，但 README 中未发现统一测试说明"
```

## 资产状态

- `detected`：代码扫描得到的事实。
- `candidate`：系统推荐但尚未确认。
- `confirmed`：用户确认采用。
- `customized`：用户已经手动修改。
- `rejected`：用户明确拒绝。

## 暂时不做什么

- 不做完整 Web UI。
- 不要求一次性设计所有交互问题。
- 不把用户未确认的候选建议伪装成团队正式规则。
- 不在后续更新时覆盖用户定制过的 Harness 文件。

## 触发执行的信号

当我们开始增强现有 CLI 交互、上下文输入、低置信度识别、候选资产管理或增量更新策略时，再把这个 idea 提升为 spec 或 implementation plan。

