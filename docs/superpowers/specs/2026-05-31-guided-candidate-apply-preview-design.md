# Guided Candidate Apply Preview Design

## 用户故事

作为 Harness Maintainer，当我在已有 Harness 的 guided `init -> review-candidate` 中审查一个 Guide / Sensor 候选并可能选择 `applied` 时，我可以在输入决策前看到它会写入哪个正式资产、采用什么应用方式、是否已有重复 marker，以及将追加的内容 diff 摘要，从而避免盲目把 review-only 候选固化进正式 Harness。

## Current State Gap Analysis

- North Star 要求审查接管阶段区分 confirmed / candidate / review-only，说明证据、适用范围、风险和对正式 Harness 的影响。
- 当前 guided `review-candidate` 已能展示候选详情，并允许 Guide / Sensor 候选显式 `applied`。
- 当前详情只展示 id、kind、target、risk、evidence 和 acceptance checks；Maintainer 在输入 `applied` 前看不到实际应用方式、target 是否已存在、是否已有重复 marker、会追加什么标题或边界块。
- `review_candidate()` 底层已有 marker 和重复应用保护，但这个信息在用户做决策前不可见，仍然像“输入 id 后直接相信工具会处理好”。

## 目标

- guided `review-candidate` 在展示候选详情后、询问 decision 前，展示 apply preview。
- Guide / Sensor Markdown 候选 preview 展示：
  - `apply_preview=available`
  - target path
  - apply mode 为 append Markdown block
  - target exists
  - duplicate marker present / absent
  - applied block heading
  - unified append diff 中的关键新增行
  - review-only source report
- Workflow policy 候选 preview 展示：
  - `apply_preview=expert_command_required`
  - target path
  - reason: guided init does not apply workflow policy candidates
- 预览只读，不写文件、不刷新 Experience、不创建 governance。

## 非目标

- 不实现完整候选浏览器、分页、编号选择或搜索。
- 不实现 workflow policy guided apply。
- 不生成 diff artifact 文件。
- 不新增 schema；预览是人类 CLI 文案，不是机器消费契约。
- 不改变 `review_candidate()` 的实际应用逻辑和安全校验。

## 设计

在 `interactive_init.py` 中新增 `_asset_candidate_apply_preview(repo, candidate)`：

- 对 Guide / Sensor Markdown 候选：
  - 根据 `candidate.suggested_path` 解析目标路径，但只做读取检查。
  - 计算 target 是否存在。
  - 检查 `<!-- harness-builder:candidate-applied id=<candidate.id> -->` 是否已存在。
  - 展示即将追加的 block heading：`## Applied Candidate: <title>`。
  - 展示 `apply_mode=append_markdown_candidate_block`。
  - 展示只读 unified append diff 片段，包含 marker、heading 和 `draft_content` 的关键新增行。
- 对 workflow policy 候选：
  - 展示 guided boundary，不调用 patch preview，不触碰 `.ai/harness-config.yaml`。

该 preview 紧跟 `_asset_candidate_detail(candidate)` 输出，出现在 decision prompt 之前。这样 `accepted` / `deferred` / `rejected` 用户也能看到正式应用边界，而选择 `applied` 的用户能在决策前看到写入影响。

## 验收标准

- integration 覆盖 guided `init -> review-candidate -> applied` 的 Guide 候选，在输入 decision 前输出 apply preview，包括 target、mode、target_exists、duplicate marker、block heading、source report 和 unified append diff 关键新增行；成功后仍只修改目标 Guide，记录 governance，刷新 Experience index，不创建 `.ai/task-runs`。
- integration 覆盖已经包含 applied marker 的 Guide 候选，preview 显示 `duplicate_marker=present`，继续选择 `applied` 时底层显式失败，不写新的 governance。
- integration 覆盖 workflow policy 候选，preview 显示 `apply_preview=expert_command_required`，选择 `applied` 仍按现有边界显式失败。
- README / init workflow / todo / evolution log 同步说明 guided apply 前会展示 summary，但 workflow policy guided apply 仍不开放。

## Decisions / Responses

- 价值切分：本轮保护“将候选正式应用到 Harness 前的审查决策”，不是做内部 helper 或泛化 UI。
- 边界回应：不增加二次确认，因为当前 guided 流程已经要求用户显式输入 `applied`；本轮只补决策前 summary / diff 信息。
- 安全回应：重复 marker 只在 preview 中暴露，实际阻断仍由 `review_candidate()` 保持。
- 范围回应：workflow policy 仍走专家命令，因为它会结构化修改 `.ai/harness-config.yaml`，需要更完整 patch 审核。

## Assumptions / Risks

- 假设一段稳定 preview 足以降低误应用风险；完整 diff 和候选浏览器留给后续。
- 风险是 CLI 输出继续变长；preview 只在用户进入 `review-candidate` 并选定候选后展示。
- 风险是用户看到 duplicate marker 后仍输入 `applied`；底层会显式失败，保持 no silent fallback。
