# Harness Builder Todos

这里存放 Harness Builder 后续需要优化、深化或重新设计的事项。

它和 `docs/superpowers/specs/` 的区别：

- `todos`：记录已经发现但尚未进入详细设计和实施计划的问题。
- `specs`：记录已经决定要做、并进入设计阶段的方案。
- `plans`：记录已经可以执行的实施步骤。

它和旧的 `docs/ideas/` 的区别：

- `ideas` 曾用于记录早期增强方向，目前其中条目已经完成。
- 新增优化项统一记录在 `docs/todos/`。
- 已完成条目统一进入 `archive.md`。

## 当前待办

| Todo | 状态 | 优先级 | 说明 |
| --- | --- | --- | --- |
| [全局交互式 CLI 与强引导式 Harness 生成](interactive-guided-cli.md) | open | high | 将 `init` 从命令式工具升级为阶段性确认、信息收集、候选项审查和人工修正的强引导式 CLI Agent |
| [大仓库 Evidence 扫描深度增强](evidence-depth-for-large-repositories.md) | open | high | 当前 evidence collector 适合 POC，但大仓库场景可能遗漏关键模块、测试、配置和风险证据 |
| [测试覆盖深度与 Acceptance 策略增强](testing-coverage-and-acceptance-strategy.md) | open | high | 默认测试只有 38 个，关键模块的失败路径、边界条件和 acceptance 运行策略需要系统补强 |
| [Benchmark 质量评分细化](benchmark-quality-scoring.md) | open | medium-high | 当前 benchmark 偏结构验收，需要补充 guide/sensor/command/evidence 的质量评分和扣分原因 |
| [Asset Writer 拆分重构](asset-writer-refactor.md) | open | medium | `write_assets.py` 职责过重，后续需要按产物类型拆分并补单元测试 |

## 管理规则

1. 每个 todo 必须说明问题、当前现状、理想状态、影响范围和初步验收标准。
2. todo 不等于承诺立即开发；进入开发前需要升级为 spec 和 plan。
3. 已完成 todo 不删除，移动到 `archive.md`，保留完成说明和相关提交/文档链接。
4. 新增 todo 时优先用中文描述，路径、命令、字段名保持英文原样。
5. 如果 todo 影响 `init` 主链路、LLM、测试或 sensor，要在条目中明确对应的工程规则文档。
