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
| [guided init 在 ai4se 真实仓库上的体验与扫描深度问题](guided-init-ai4se-real-repo-findings.md) | open | high | 记录真实多栈仓库试跑暴露的 evidence 噪声、多栈建模、中文成熟度叙事、skipped files 展示、高风险突出和 LLM / 确定性扫描主从关系问题。 |
| [成熟度驱动的 init 主向导与命令信息架构重构](maturity-driven-init-wizard.md) | open | high | 将 `init` 强化为成熟度驱动的主入口，串联扫描、确认、成熟度初评、Harness 生成、benchmark 和下一步建议；再次执行时作为已有 Harness 的状态感知维护入口。 |

## 管理规则

1. 每个 todo 必须说明问题、当前现状、理想状态、影响范围和初步验收标准。
2. todo 不等于承诺立即开发；进入开发前需要升级为 spec 和 plan。
3. 已完成 todo 不删除，移动到 `archive.md`，保留完成说明和相关提交/文档链接。
4. 新增 todo 时优先用中文描述，路径、命令、字段名保持英文原样。
5. 如果 todo 影响 `init` 主链路、LLM、测试或 sensor，要在条目中明确对应的工程规则文档。
