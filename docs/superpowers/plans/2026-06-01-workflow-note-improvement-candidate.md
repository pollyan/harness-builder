# Workflow 补充改进候选实施计划

## 修改范围

本轮只把 guided `init` 中已经持久化的 Workflow 补充接入 existing Harness `improve` 的 review-only 改进候选流。修改范围：

- `src/harness_builder_agent/tools/generate_improvements.py`
- `src/harness_builder_agent/tools/maturity_evidence.py`
- `tests/unit/test_generate_improvements.py`
- `tests/integration/test_init_on_fixture_projects.py`
- `docs/engineering/init-workflow.md`
- `docs/evolution-log.md`

不修改：

- `WorkflowPolicyPatch` / `AssetCandidateDraft`
- `review-candidate applied` 行为
- 正式 `.ai/harness-config.yaml` routing policy
- Runtime / `.ai/task-runs`

## TDD 步骤

1. 在 `tests/unit/test_generate_improvements.py` 新增失败测试：
   - pending review + review-only workflow note 生成 `interaction-workflow-note-review`。
   - 无 note / not_required / 非 review-only effect 不生成候选。
2. 在 guided init integration 新增失败测试：
   - 首次 guided init 输入 Workflow note 并确认写入。
   - 再次 guided init 选择 `improve`，不重新扫描。
   - `.ai/improvement-candidates.yaml` 包含 Workflow note candidate。
   - `harness-config.yaml` routing policy 不包含 Workflow note 文本。
3. 实现：
   - `generate_improvements()` 读取可选 `interaction-decisions.yaml`。
   - `_candidates()` 接收可选 `InteractionDecisions`。
   - 新增 `_workflow_note_review_candidate()` 和 guard helper。
   - `maturity_evidence.MATURITY_INPUTS` 增加 `.ai/interaction-decisions.yaml`、`.ai/human-input-needed.md`。
4. 更新工程规则：
   - `docs/engineering/init-workflow.md` 说明 `improve` 可把 review-only Workflow note 转为 `workflow_policy_update` 候选，但不生成 patch、不修改正式 routing policy。
5. 验证：
   - 目标 unit test。
   - 目标 integration test。
   - 相关 improve / guided init 测试切片。
   - `git diff --check`。
   - `scripts/test-fast.sh`。
6. 提交：
   - 中文 commit message。
   - 不 push，除非后续工作包达到独立 push 边界并通过 `scripts/test-full.sh`。

## 验收命令

```bash
.venv/bin/python -m pytest tests/unit/test_generate_improvements.py -q
.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py::<目标测试名> -q
.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_improve_generates_reviewable_improvement_candidates tests/integration/test_init_on_fixture_projects.py::<目标测试名> -q
git diff --check
scripts/test-fast.sh
```
