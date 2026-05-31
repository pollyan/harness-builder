# 本地独有 / 更细能力迁移 Todo 计划

**目标：** 在最新 `origin/main` 基线上收敛合并策略，只保留“本地独有 / 更细能力迁移”为当前 open todo，并记录旧本地实现的备份位置。

## 计划

- [x] 建立备份：创建 `backup/local-61-before-migration`，stash reset 前未提交工作树。
- [x] 收敛基线：将 `main` reset 到最新 `origin/main`。
- [x] 恢复迁移 todo：从 stash 未跟踪文件 parent 恢复 `docs/todos/local-unique-capability-migration.md`。
- [x] 收敛 open todo：更新 `docs/todos/README.md`，暂停 `guided-init-ai4se-real-repo-findings.md` 和 `maturity-driven-init-wizard.md`。
- [ ] 记录：新增 spec / plan / evolution log。
- [x] 验证：运行 open todo 检查、`git diff --check` 和 `scripts/test-fast.sh`。
- [ ] 提交：中文 commit message；本轮不 push。

## 验证命令

```bash
rg "状态：open|\\| .* \\| open \\|" docs/todos -g '*.md'
git branch --list 'backup/local-61-before-migration'
git status --short --branch
git diff --check
scripts/test-fast.sh
```

## Self-Harness Gate 关注点

- 是否改变运行逻辑：否。
- 是否新增 schema：否。
- 是否需要 acceptance：否，本轮只收敛合并策略与 todo 事实源。
- 下一轮候选：从 `local-unique-capability-migration.md` 的推荐顺序中选择第一个小步迁移切片。

## 验证结果

- `rg "状态：open|\\| .* \\| open \\|" docs/todos -g '*.md'`：只返回迁移 todo。
- `git branch --list 'backup/local-61-before-migration'`：备份分支存在。
- `git diff --check`：通过。
- `scripts/test-fast.sh`：334 passed。
