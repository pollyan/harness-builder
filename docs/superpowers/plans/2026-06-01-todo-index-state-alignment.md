# Todo 索引状态对齐实施计划

## 目标

收敛 `docs/todos` 的事实源表达，让当前 open todo、暂停背景项和已完成归档项一眼可分，避免目标模式误把历史文件当成待执行事项。

## 步骤

1. 审计 `docs/todos/*.md` 状态。
   - 用 `rg` 检查 `状态：implemented`、`状态：paused`、`open`、`当前优先事项` 等措辞。
   - 确认当前没有真正 open todo。

2. 更新 `docs/todos/README.md`。
   - 保留“当前待办：暂无”。
   - 新增“保留的历史事项状态索引”，列出 paused background 和 implemented archive 文件。
   - 修改管理规则：已完成条目进入 `archive.md` 索引，原文件可保留但必须标明状态。

3. 更新 paused 背景文件。
   - `guided-init-ai4se-real-repo-findings.md` 移除指向 `local-unique-capability-migration.md` 的过期优先事项说明。
   - 将“剩余 LLM-planned deep scan 仍保持 open”改为“如后续需要，基于最新代码重新拆成具体 gap”。
   - `maturity-driven-init-wizard.md` 同步去掉过期迁移优先说明。

4. 更新归档规则。
   - `docs/todos/archive.md` 明确归档索引不要求物理移动历史文件。

5. 记录演进。
   - 在 `docs/evolution-log.md` 顶部新增本轮摘要、验收和 Gate 结论。

6. 验证。
   - `rg "当前优先事项改为|仍保持 open" docs/todos`
   - `git diff --check`
   - `scripts/test-fast.sh`

## 验收边界

- 本轮只改文档事实源，不改产品代码。
- 不新增 open todo。
- 不 push；push 仍等待 `scripts/test-full.sh` 在具备 DeepSeek key 和 `.benchmarks` 后通过。
