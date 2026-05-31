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
| [本地独有 / 更细能力合并与迁移](local-unique-capability-migration.md) | open | high | 以最新 `origin/main` 为基线，只迁移本地 61 个提交中远端未覆盖或更细的能力，避免整包 merge 并行实现。 |

当前只有上表这一项 open todo。`guided-init-ai4se-real-repo-findings.md` 与 `maturity-driven-init-wizard.md` 暂停为背景参考，后续迁移完成后再基于最新代码重新拆分具体 gap。

## 管理规则

1. 每个 todo 必须说明问题、当前现状、理想状态、影响范围和初步验收标准。
2. todo 不等于承诺立即开发；进入开发前需要升级为 spec 和 plan。
3. 已完成 todo 不删除，移动到 `archive.md`，保留完成说明和相关提交/文档链接。
4. 新增 todo 时优先用中文描述，路径、命令、字段名保持英文原样。
5. 如果 todo 影响 `init` 主链路、LLM、测试或 sensor，要在条目中明确对应的工程规则文档。
