# Guided Init 团队规则与 Workflow 返回修改提示实施计划

## 目标

补齐 final confirmation 中 `back -> rules` 和 `back -> workflow` 的纠错提示，让用户明确新输入替换旧输入，直接回车清空旧输入，并在清空后看到可见确认。

## 步骤

- [x] **Step 1: 写失败测试**
  - 修改 `tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_team_rules`：
    - 断言 `团队规则返回修改`、替换 / 清空说明和上一版摘要。
    - 保留最终资产只含新规则的断言。
  - 新增或扩展 rules 清空测试：
    - 初始输入团队规则，final confirmation `back -> rules` 后直接回车。
    - 断言 `团队规则已清空`。
    - 断言 `interaction-decisions.yaml` 没有 inline contexts，project-context / human-input-needed 不含旧规则。
  - 修改 `test_guided_init_final_summary_can_go_back_to_workflow_note`：
    - 断言 `Workflow 补充返回修改`、替换 / 清空说明和上一版摘要。
  - 新增或扩展 workflow 清空测试：
    - 初始输入 Workflow note，final confirmation `back -> workflow` 后直接回车。
    - 断言 `Workflow 补充已清空`。
    - 断言 `interaction-decisions.yaml` 没有 notes，project-context / human-input-needed / routing 不含旧 note。

- [x] **Step 2: 实现 CLI helper**
  - 修改 `src/harness_builder_agent/tools/interactive_init.py`：
    - `back -> rules` 前保存 `previous_inline_contexts`，输出返回修改 notice。
    - rules 新输入为空且上一版非空时输出清空确认。
    - `back -> workflow` 前保存 `previous_workflow_confirmation`，输出返回修改 notice。
    - workflow 新输入为空且上一版 note 非空时输出清空确认。
    - 新增四个 helper，并保持无旧输入时不增加噪音。

- [x] **Step 3: 同步工程文档与演进记录**
  - 修改 `docs/engineering/init-workflow.md`：
    - 在团队规则和 Workflow 返回修改规则中补充替换 / 清空可见语义。
  - 修改 `docs/evolution-log.md`：
    - 追加本轮记录。

- [x] **Step 4: 验证**
  - 运行目标 tests：
    - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_team_rules tests/integration/test_init_on_fixture_projects.py::test_guided_init_final_summary_can_go_back_to_workflow_note -q`
    - 加上新增清空测试目标。
  - 运行 full guided init integration：
    - `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py -q`
  - 运行 `git diff --check`。
  - commit 前运行 `scripts/test-fast.sh`。

- [x] **Step 5: 本地提交**
  - 暂存本轮文件。
  - 提交中文 commit：`提示团队规则与工作流返回修改边界`。
  - 本轮不 push。

## 边界

- 不修改 schema。
- 不修改 LLM、scanner、writer、benchmark。
- 不生成候选或应用 workflow policy。
- 不执行 Runtime、不创建 `.ai/task-runs`。
