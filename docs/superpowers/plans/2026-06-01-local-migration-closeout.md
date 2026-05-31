# 本地独有能力迁移收口计划

## Milestone

作为 Harness Maintainer，当我查看 `docs/todos/` 和当前 git 分支时，我可以看到本地独有 / 更细能力迁移工作包已经收口归档、已迁移切片和未迁移取舍清楚可追溯，并且本地 commits 已通过 full regression 后同步远端，从而后续目标模式可以回到 init North Star 的新 gap，而不是继续围绕旧 61 提交做重复合并。

## 实施步骤

1. 更新 `docs/todos/local-unique-capability-migration.md`：
   - 状态改为 `implemented`。
   - 增加完成说明。
   - 明确未迁移项的取舍：顶层 evidence schema 扩展、benchmark failed detail 全量审计、helper 去重均转为后续候选，不阻塞迁移包。
2. 更新 `docs/todos/README.md`：
   - 移除当前 open todo 表里的迁移项。
   - 说明当前没有由旧 61 提交迁移驱动的 open todo；后续按 North Star gap 重新选题。
3. 更新 `docs/todos/archive.md`：
   - 增加本地独有 / 更细能力合并与迁移的归档行。
4. 更新 `docs/evolution-log.md`：
   - 记录本轮 closeout 的 Gap Analysis 摘要、取舍和验证方式。

## 验证步骤

1. `rg -n "local-unique-capability-migration|open \\| high" docs/todos/README.md docs/todos/local-unique-capability-migration.md docs/todos/archive.md`
2. `git diff --check`
3. `scripts/test-fast.sh`
4. 本地提交：`归档本地独有能力迁移`
5. 因完整迁移工作包完成，运行 `scripts/test-full.sh`
6. full regression 通过后 push 当前分支。

## Commit / Push

- commit message：`归档本地独有能力迁移`
- push 前必须 full regression；如果 full 因缺少 DeepSeek key、真实仓库或网络失败，记录失败并不 push。
