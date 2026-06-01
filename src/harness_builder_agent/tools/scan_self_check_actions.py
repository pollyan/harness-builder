from __future__ import annotations


def scan_self_check_action_hint(action_type: str) -> str:
    hints = {
        "provide_stack": "补充 `stack=<value>`，说明真实主技术栈或子模块边界。",
        "provide_module": "补充 `module=路径|类型|名称`，说明关键目录、模块职责或入口文件。",
        "provide_command": "补充 `command=ID|命令|类型|gate|来源|置信度`，说明真实验证入口。",
        "provide_risk": "补充 `risk=路径|原因`，说明高风险目录、权限、支付、数据或发布边界。",
        "review_current_evidence": "复核当前 evidence 是否足以关闭追问，必要时用 `review-human-input` 标记。",
        "run_targeted_scan": "后续运行 targeted scan 或人工补充关键 evidence；当前 Builder 不自动重扫。",
        "maintainer_review": "由 Harness Maintainer 人工复核该追问，必要时补充上下文或保持待确认。",
    }
    return hints.get(action_type, hints["maintainer_review"])
