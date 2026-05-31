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
| 暂无 | - | - | 当前没有由旧 61 个本地提交迁移驱动的 open todo。后续目标模式按 `docs/strategy/init-north-star.md` 和 Current State Gap Analysis 重新选择具体 gap。 |

`local-unique-capability-migration.md` 已归档为 implemented，用于记录本地 61 个提交迁移收口过程、已迁移切片和未迁移取舍。`guided-init-ai4se-real-repo-findings.md` 与 `maturity-driven-init-wizard.md` 暂停为背景参考；如果后续仍有价值，应基于最新代码和 North Star 拆成新的具体 gap，而不是直接重新打开旧宽泛 todo。

## 管理规则

1. 每个 todo 必须说明问题、当前现状、理想状态、影响范围和初步验收标准。
2. todo 不等于承诺立即开发；进入开发前需要升级为 spec 和 plan。
3. 已完成 todo 不删除，移动到 `archive.md`，保留完成说明和相关提交/文档链接。
4. 新增 todo 时优先用中文描述，路径、命令、字段名保持英文原样。
5. 如果 todo 影响 `init` 主链路、LLM、测试或 sensor，要在条目中明确对应的工程规则文档。
