from __future__ import annotations

from harness_builder_agent.tools.existing_harness_actions import (
    existing_harness_action_menu_lines,
    existing_harness_action_number,
    normalize_existing_harness_action,
)


def test_existing_harness_action_contract_renders_stable_numbered_menu():
    lines = existing_harness_action_menu_lines()

    assert lines == [
        "1. exit：退出，不覆盖现有 Harness。",
        "2. assess：重新评估成熟度，只刷新 maturity 和 init summary 产物。",
        "3. improve：基于成熟度缺口生成 review-only 改进候选，不覆盖正式 Harness 资产。",
        "4. benchmark：运行 Harness 质量门禁，刷新 benchmark / maturity / improvement 派生产物，不覆盖正式 Harness 资产。",
        "5. recommend-workflow：输入任务说明，生成 review-only Workflow 推荐，不执行任务或修改正式 routing policy。",
        "6. review-candidate：记录候选 accepted / deferred / rejected；Guide/Sensor 可显式 applied，workflow_policy 仍需专家命令。",
        "7. review-human-input：处理 scan follow-up 人工复核 resolved / reopened，不修改正式 Harness 资产。",
        "8. self-improve：生成 review-only 自改进审查包，不应用正式资产或执行 Runtime。",
        "9. reinit：继续重新扫描并进入当前生成向导。",
    ]


def test_existing_harness_action_contract_maps_numbers_and_unknown_actions():
    assert existing_harness_action_number("exit") == "1"
    assert existing_harness_action_number("benchmark") == "4"
    assert existing_harness_action_number("recommend-workflow") == "5"
    assert existing_harness_action_number("review-human-input") == "7"
    assert existing_harness_action_number("custom-action") is None


def test_existing_harness_action_contract_normalizes_numbers_and_aliases():
    assert normalize_existing_harness_action("1") == "exit"
    assert normalize_existing_harness_action("4") == "benchmark"
    assert normalize_existing_harness_action("7") == "review-human-input"
    assert normalize_existing_harness_action("quit") == "exit"
    assert normalize_existing_harness_action("质量") == "benchmark"
    assert normalize_existing_harness_action("治理") == "review-candidate"
    assert normalize_existing_harness_action("human-input") == "review-human-input"
    assert normalize_existing_harness_action("人工输入") == "review-human-input"
    assert normalize_existing_harness_action("待确认") == "review-human-input"
    assert normalize_existing_harness_action("重新生成") == "reinit"
    assert normalize_existing_harness_action("unknown") == "unknown"
