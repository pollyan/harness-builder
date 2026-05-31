from __future__ import annotations

from harness_builder_agent.tools.risk_signals import classify_risk_area, high_impact_risk_areas, risk_slug


def test_classify_secret_like_risk_as_high_impact():
    signal = classify_risk_area({"path": "docs/a.json", "reason": "Possible plaintext API key is present."})

    assert signal.is_high_impact is True
    assert signal.category == "credential"
    assert "疑似凭证" in signal.confirmation_reason


def test_classify_chinese_business_risks_as_high_impact():
    permission = classify_risk_area({"path": "src/auth", "reason": "权限校验和登录安全逻辑"})
    payment = classify_risk_area({"path": "billing/pay", "reason": "支付金额计算"})
    migration = classify_risk_area({"path": "db/migrations", "reason": "数据迁移脚本"})

    assert permission.is_high_impact is True
    assert permission.category == "security"
    assert payment.is_high_impact is True
    assert payment.category == "payment"
    assert migration.is_high_impact is True
    assert migration.category == "data_migration"


def test_classify_plain_configuration_risk_as_normal():
    signal = classify_risk_area({"path": "application.yml", "reason": "configuration risk"})

    assert signal.is_high_impact is False
    assert signal.category == "general"


def test_high_impact_risk_areas_filters_and_slugs_paths():
    risks = [
        {"path": "docs/a.json", "reason": "API key"},
        {"path": "application.yml", "reason": "configuration risk"},
    ]

    high_risks = high_impact_risk_areas(risks)

    assert len(high_risks) == 1
    assert high_risks[0].path == "docs/a.json"
    assert risk_slug("docs/a.json") == "docs-a-json"
