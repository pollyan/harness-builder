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
| [旧 scanner v2 实现审查与迁移评估](scanner-v2-review-and-migration.md) | open | high | 在当前 evidence depth v1 已完成的基础上，审查历史 scanner v2 是否还有可吸收的扫描能力 |
| [删除 run 命令并收缩 Runtime 职责边界](remove-run-command-runtime-boundary.md) | open | high | `run` 命令承担了任务级 runtime/workflow 模拟职责，可能不属于 Harness Builder 的边界，应评估并移除 |

## 管理规则

1. 每个 todo 必须说明问题、当前现状、理想状态、影响范围和初步验收标准。
2. todo 不等于承诺立即开发；进入开发前需要升级为 spec 和 plan。
3. 已完成 todo 不删除，移动到 `archive.md`，保留完成说明和相关提交/文档链接。
4. 新增 todo 时优先用中文描述，路径、命令、字段名保持英文原样。
5. 如果 todo 影响 `init` 主链路、LLM、测试或 sensor，要在条目中明确对应的工程规则文档。
