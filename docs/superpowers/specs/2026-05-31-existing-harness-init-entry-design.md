# Existing Harness Init Entry Design

## North Star Capability

本轮继续推进“成熟度驱动的 init 主向导”。目标是让默认 guided `init` 在发现目标仓库已有 `.ai` Harness 时，先进入状态感知维护入口，而不是直接开始扫描和覆盖资产。

## Current State Gap Analysis

| 维度 | 目标态 | 当前已有 | 缺口 | 本轮判断 |
| --- | --- | --- | --- | --- |
| 用户工作流 | 再次执行 `init` 先展示已有 Harness 状态和可选动作 | 首次 init 已有成熟度摘要 | guided init 仍直接进入生成流程 | 本轮优先 |
| 正式资产保护 | 默认不覆盖客户已编辑 Harness | candidate governance 已强调正式资产边界 | 再次 init 可能重写 `.ai` 正式文件 | 本轮先支持退出不覆盖 |
| 自动化兼容 | 脚本仍可显式使用 `--non-interactive` | `--non-interactive` 已用于测试/CI | 不应在本轮改变自动化重新生成语义 | 保持不变 |
| 状态摘要 | 用户看到成熟度、benchmark、pending items | `.ai/init-summary.md`、maturity score、experience index 已有 | guided init 未消费这些状态 | 本轮读取并展示 |
| 动作菜单 | 支持复评、重扫、benchmark、处理候选等 | 底层命令存在 | 全动作菜单会扩大范围 | 本轮只实现 `exit` / `reinit` |

## Decisions

- 只改变默认 guided mode。`--non-interactive` 继续按当前自动化语义生成或重写初始资产。
- 如果存在 `.ai/project-inventory.json` 和 `.ai/harness-config.yaml`，guided `init` 先展示已有 Harness 状态。
- 第一版动作只支持：
  - `exit`：退出，不扫描、不调用 writer、不覆盖正式资产。
  - `reinit`：显式继续现有生成流程，仍会进入当前 guided 确认。
- 选择 `exit` 时允许写入本次 `.ai/runs/<run_id>` trace，因为这是 Harness Builder 自身可观测性，不属于正式 Harness 内容覆盖。
- 状态读取使用现有 schema；状态文件损坏时显式失败，不伪造健康摘要。

## Acceptance Criteria

- Integration：先运行 `init --non-interactive` 生成 Harness，再运行默认 guided `init`，输入 `exit` 后输出包含“已存在 Harness”、当前成熟度和可选动作。
- Integration：上述 `exit` 路径不调用 `scan_repository`，不改写 `.ai/project-inventory.json`、`.ai/harness-config.yaml`、`.ai/init-summary.md`。
- Trace：`exit` 路径生成 trace，status 为 `completed`，summary 标记 `existing_harness_action: exit`。
- Existing tests：首次 guided happy path 仍能继续生成。
- Docs：todo 标记已有 Harness read-only entry slice 已完成，init workflow 记录该默认 guided 行为。

## Risks

- 只支持 `exit` / `reinit` 还不是完整维护菜单。本轮先建立保护边界和状态入口，后续再把 assess / improve / benchmark / candidate governance 动作接入。
- `--non-interactive` 仍可重写资产。保留自动化兼容，后续如需保护应另行设计 `--force` 或维护模式参数。
