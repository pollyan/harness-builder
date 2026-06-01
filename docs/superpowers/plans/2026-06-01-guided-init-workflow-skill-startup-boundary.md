# Guided Init Workflow Skill 启动边界计划

## 用户故事

作为 Harness Maintainer，当我刚运行首次 guided `init` 并看到启动说明或查阅 README 的 `.ai/` 产物树时，我可以明确知道本次会生成 `lightweight`、`bugfix` 和 `standard` 三类 Workflow Skill，从而在继续扫描前就理解 Harness 会包含低风险、缺陷修复和高风险升级三条工作流基线。

## 验收标准

- 启动说明在继续扫描前列出 `lightweight`、`bugfix`、`standard` 三类 Workflow Skill。
- README `.ai/skills/` 树包含 `standard/SKILL.md`。
- skill writer 仍生成三类 Skill。
- 文档和演进记录同步。
- fast regression 通过；push 前 full regression 按规则执行。

## 步骤

1. 更新 guided init startup integration 的 RED 断言。
2. 修改 `_show_guided_init_startup_boundary()` 文案。
3. 更新 README `.ai/` 产物树。
4. 更新 `docs/evolution-log.md`。
5. 运行 targeted integration / skill writer tests、compileall、diff check、`scripts/test-fast.sh`。
6. 创建本地提交。
7. 运行 `scripts/test-full.sh`；若通过则 push，若外部 acceptance 前置失败则不 push 并报告。
