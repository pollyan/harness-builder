# Existing Harness Action Dispatch Registry 实施计划

## 目标

把已有 Harness 维护入口的 action runner 从手写 `if action == ...` 分支收敛为显式 dispatch registry，并用 unit test 固定菜单动作与 handler 覆盖一致，保护后续维护入口继续演进。

## 实施步骤

1. TDD：更新 `tests/unit/test_existing_harness_action_boundaries.py`：
   - 从 `existing_harness_actions.EXISTING_HARNESS_ACTIONS` 取菜单 action 集合。
   - 断言 `existing_harness_action_runner.EXISTING_HARNESS_ACTION_HANDLERS` 覆盖同一集合。
   - 断言 runner source 不再出现逐个 `if action == "..."` 分支。
2. 运行 targeted unit，确认 RED：当前 runner 没有 handler registry。
3. 实现 `existing_harness_action_runner.py`：
   - 增加统一 handler 类型和小 wrapper。
   - 建立 `EXISTING_HARNESS_ACTION_HANDLERS`，覆盖 `exit`、`assess`、`improve`、`benchmark`、`recommend-workflow`、`review-candidate`、`review-human-input`、`self-improve`、`reinit`、`review-initial-candidate`。
   - `run_existing_harness_action()` 只做 registry lookup、dispatch 和 unknown failure。
4. 运行 targeted unit，确认 GREEN。
5. 运行现有 action contract unit 与 existing Harness targeted integration，确认菜单 / action 行为不漂移。
6. 更新 `docs/evolution-log.md` 记录本轮 Gap Analysis、工程信任故事、取舍、验证和 Self-Harness Gate。
7. 运行 `git diff --check`、`scripts/test-fast.sh`。
8. 创建中文本地 commit；本轮不 push，除非 full regression 后续满足外部前置。

## 验证命令

```bash
.venv/bin/python -m pytest tests/unit/test_existing_harness_action_boundaries.py tests/unit/test_existing_harness_actions.py -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q
git diff --check
scripts/test-fast.sh
```

## 非目标

- 不修改已有 Harness 菜单编号、文案或别名。
- 不修改 action 成功 / 失败输出、trace artifact、trace summary 或返回值。
- 不新增维护动作。
- 不修改 `.ai` schema、LLM、benchmark、writer、Sensor 或 Runtime 契约。
