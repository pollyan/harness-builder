# Guided 补充呈现边界抽取实施计划

## 目标

把首次 guided `init` 中用户补充相关的 CLI 呈现逻辑从 `interactive_init.py` 抽到独立模块，保持用户可见行为不变，并为后续打磨团队规则 / Workflow 补充体验提供可单测边界。

## 步骤

1. TDD：新增 `tests/unit/test_guided_supplement_presentation.py`
   - 先导入尚不存在的 `guided_supplement_presentation`，确认 RED。
   - 覆盖 scan supplement immediate summary、replacement summary、team rules back / clear、workflow note immediate / clear、final supplement impact summary。
2. 实现新模块 `src/harness_builder_agent/tools/guided_supplement_presentation.py`
   - 迁移纯呈现函数。
   - 复用 `GuidedScanOverrides`、`has_scan_overrides` 和 `WorkflowConfirmation`。
   - 不引入对 `interactive_init.py` 的反向依赖。
3. 更新 `interactive_init.py`
   - 导入新模块函数。
   - 删除内联呈现实现。
   - 保留同名下划线 facade，现有调用和隐藏测试继续可用。
4. 验证行为保持
   - 运行新 unit。
   - 运行相关 guided integration：
     - structured scan corrections。
     - scan back replaces corrections。
     - scan back clears corrections。
     - team rules back clears rules。
     - workflow back clears note。
5. 更新 `docs/evolution-log.md`
   - 记录本轮 Gap Analysis 摘要、工程信任故事、取舍、验证结果和 Gate。
6. 完成验证
   - `.venv/bin/python -m compileall src/harness_builder_agent/tools/interactive_init.py src/harness_builder_agent/tools/guided_supplement_presentation.py`
   - `git diff --check`
   - `scripts/test-fast.sh`
7. 本地 commit
   - commit message：`抽取 guided 补充呈现模块`
   - 本轮不 push；push 仍以完整工作包和 full regression 为边界。

## 非目标

- 不改变 guided init 用户文案。
- 不修改 input prompt 采集逻辑。
- 不修改 interaction decisions、writer、schema、benchmark、LLM 或 Runtime 边界。
- 不创建 `.ai/task-runs`。
