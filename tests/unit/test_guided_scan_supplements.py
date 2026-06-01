from harness_builder_agent.tools.guided_scan_supplements import parse_guided_scan_supplement


def test_parse_guided_scan_supplement_accepts_structured_fragments():
    overrides = parse_guided_scan_supplement(
        "stack=node; module=apps/web|frontend|Web UI; "
        "command=unit-test|npm test|test|hard|package.json|high; risk=apps/payments|支付风险高",
        current_stack="java-spring",
    )

    assert overrides.primary_stack == "node"
    assert overrides.modules == [{"path": "apps/web", "kind": "frontend", "name": "Web UI"}]
    assert len(overrides.commands) == 1
    assert overrides.commands[0].id == "unit-test"
    assert overrides.commands[0].command == "npm test"
    assert overrides.commands[0].type == "test"
    assert overrides.commands[0].gate == "hard"
    assert overrides.commands[0].source == "package.json"
    assert overrides.commands[0].confidence == "high"
    assert overrides.risk_areas == [{"path": "apps/payments", "reason": "支付风险高"}]
    assert "用户将主要技术栈修正为：node" in overrides.notes
    assert "用户补充验证命令：npm test，gate=hard" in overrides.notes


def test_parse_guided_scan_supplement_reports_invalid_structured_command_as_note():
    overrides = parse_guided_scan_supplement(
        "command=unit-test|npm test|test|hard",
        current_stack="java-spring",
    )

    assert overrides.commands == []
    assert overrides.notes == [
        "结构化 command 片段未解析：command=unit-test|npm test|test|hard；"
        "未进入 command catalog，只作为自然语言补充保留。"
        "可用格式：command=ID|命令|类型(build/test/lint/typecheck/other)|gate(hard/soft)|来源|置信度(low/medium/high)。"
    ]


def test_parse_guided_scan_supplement_reports_invalid_module_and_risk_without_structured_effect():
    overrides = parse_guided_scan_supplement(
        "module=apps/api|backend; risk=apps/payments",
        current_stack="java-spring",
    )

    assert overrides.modules == []
    assert overrides.risk_areas == []
    assert overrides.notes == [
        "结构化 module 片段未解析：module=apps/api|backend；未进入 project inventory，只作为自然语言补充保留。"
        "可用格式：module=路径|类型|名称。",
        "结构化 risk 片段未解析：risk=apps/payments；未进入 risk hints，只作为自然语言补充保留。"
        "可用格式：risk=路径|原因。",
    ]


def test_parse_guided_scan_supplement_reports_invalid_stack_with_allowed_values():
    overrides = parse_guided_scan_supplement(
        "stack=rails",
        current_stack="java-spring",
        stack_resolver=lambda _value: "rails",
    )

    assert overrides.primary_stack is None
    assert overrides.notes == [
        "结构化 stack 片段未解析：stack=rails；未进入 primary stack override，只作为自然语言补充保留。"
        "可用格式：stack=java-spring|dotnet-aspnet|node|python-flask|unknown。"
    ]


def test_parse_guided_scan_supplement_keeps_plain_language_without_structured_error():
    overrides = parse_guided_scan_supplement(
        "后端真实主模块在 services/order，支付模块风险最高",
        current_stack="java-spring",
    )

    assert overrides.modules == []
    assert overrides.commands == []
    assert overrides.risk_areas == []
    assert overrides.notes == ["后端真实主模块在 services/order，支付模块风险最高"]
