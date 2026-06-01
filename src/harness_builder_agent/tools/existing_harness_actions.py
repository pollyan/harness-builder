from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExistingHarnessAction:
    number: str
    action: str
    description: str
    aliases: tuple[str, ...] = ()


EXISTING_HARNESS_ACTIONS: tuple[ExistingHarnessAction, ...] = (
    ExistingHarnessAction(
        number="1",
        action="exit",
        description="退出，不覆盖现有 Harness。",
        aliases=("quit", "q", "退出"),
    ),
    ExistingHarnessAction(
        number="2",
        action="assess",
        description="重新评估成熟度，只刷新 maturity 和 init summary 产物。",
        aliases=("reassess", "复评", "重新评估"),
    ),
    ExistingHarnessAction(
        number="3",
        action="improve",
        description="基于成熟度缺口生成 review-only 改进候选，不覆盖正式 Harness 资产。",
        aliases=("recommendations", "建议", "改进"),
    ),
    ExistingHarnessAction(
        number="4",
        action="benchmark",
        description="运行 Harness 质量门禁，刷新 benchmark / maturity / improvement 派生产物，不覆盖正式 Harness 资产。",
        aliases=("bench", "质量", "验收"),
    ),
    ExistingHarnessAction(
        number="5",
        action="recommend-workflow",
        description="输入任务说明，生成 review-only Workflow 推荐，不执行任务或修改正式 routing policy。",
        aliases=("recommend", "workflow", "工作流", "路由"),
    ),
    ExistingHarnessAction(
        number="6",
        action="review-candidate",
        description="记录候选 accepted / deferred / rejected；Guide/Sensor 可显式 applied，workflow_policy 仍需专家命令。",
        aliases=("candidate", "governance", "候选", "治理"),
    ),
    ExistingHarnessAction(
        number="7",
        action="review-human-input",
        description="处理 scan follow-up 人工复核 resolved / reopened，不修改正式 Harness 资产。",
        aliases=("human-input", "human", "input", "人工输入", "待确认", "复核"),
    ),
    ExistingHarnessAction(
        number="8",
        action="self-improve",
        description="生成 review-only 自改进审查包，不应用正式资产或执行 Runtime。",
        aliases=("self", "自改进", "智能改进"),
    ),
    ExistingHarnessAction(
        number="9",
        action="reinit",
        description="继续重新扫描并进入当前生成向导。",
        aliases=("重新生成", "regenerate"),
    ),
    ExistingHarnessAction(
        number="10",
        action="review-initial-candidate",
        description="记录初始 LLM Guide/Sensor 候选 accepted / rejected / kept，不写正式资产。",
        aliases=("initial-candidate", "initial", "初始候选", "初始候选治理"),
    ),
)


def existing_harness_action_menu_lines() -> list[str]:
    return [f"{item.number}. {item.action}：{item.description}" for item in EXISTING_HARNESS_ACTIONS]


def existing_harness_action_number(action: str) -> str | None:
    normalized = action.strip().lower()
    for item in EXISTING_HARNESS_ACTIONS:
        if item.action == normalized:
            return item.number
    return None


def is_existing_harness_action(action: str) -> bool:
    normalized = action.strip().lower()
    return any(item.action == normalized for item in EXISTING_HARNESS_ACTIONS)


def normalize_existing_harness_action(value: str) -> str:
    normalized = value.strip().lower()
    for item in EXISTING_HARNESS_ACTIONS:
        if normalized == item.number or normalized == item.action or normalized in item.aliases:
            return item.action
    return normalized
