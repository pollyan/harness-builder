# Init Completion User Supplements 实施计划

目标：让首次 `init` 写入完成后的 CLI 主交付摘要直接展示本次吸收的 scan / team / workflow 用户补充，补齐终端侧闭环。

## Steps

1. 红测：unit
   - 修改 `tests/unit/test_init_summary.py`。
   - 在 completion message fixture 中写入 `.ai/interaction-decisions.yaml`，断言输出 `本次吸收的用户补充`、scan/team/workflow 摘要、source 和事实边界。
   - 增加无用户补充和缺失 `interaction-decisions.yaml` 的断言。
   - 先运行目标 unit，确认当前 completion message 缺少 section。

2. 实现
   - 修改 `src/harness_builder_agent/tools/init_summary.py`。
   - 新增 `_completion_user_supplement_lines(ai)`，使用 `InteractionDecisions` schema 读取 `.ai/interaction-decisions.yaml`。
   - `render_init_completion_message()` 在 `主要证据 / 缺口` 后输出该 section。
   - 保持 no silent fallback：文件缺失显示 missing，schema 错误继续显式抛出。

3. 集成验证
   - 修改或补充 `tests/integration/test_init_on_fixture_projects.py` 的 guided init 补充场景，断言 completion message 包含本次补充。
   - 运行目标 integration 和完整 guided init integration。

4. 文档记录
   - 更新 `README.md` 与 `docs/engineering/init-workflow.md`，说明 completion message 会展示本次吸收的用户补充。
   - 更新 `docs/evolution-log.md`。

5. 最终验证与提交
   - `git diff --check`
   - `scripts/test-fast.sh`
   - 中文 commit message。
