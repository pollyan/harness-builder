from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RiskSignal:
    path: str
    reason: str
    is_high_impact: bool
    category: str
    confirmation_reason: str


KEYWORD_CATEGORIES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "credential",
        (
            "api key",
            "apikey",
            "secret",
            "token",
            "password",
            "credential",
            "private key",
            "access key",
            "密钥",
            "凭证",
            "令牌",
            "密码",
        ),
        "疑似凭证、密钥或访问令牌，需人工确认是否进入安全风险边界。",
    ),
    (
        "security",
        ("security", "auth", "permission", "login", "安全", "权限", "认证", "鉴权", "登录"),
        "疑似安全、认证或权限风险，需人工确认影响面和升级策略。",
    ),
    (
        "payment",
        ("payment", "money", "billing", "invoice", "支付", "金额", "计费", "账单"),
        "疑似支付、金额或计费风险，需人工确认验证策略和人工升级条件。",
    ),
    (
        "data_migration",
        ("data migration", "migration", "database migration", "数据迁移", "迁移脚本", "数据库迁移"),
        "疑似数据迁移风险，需人工确认回滚、验证和发布边界。",
    ),
    (
        "data_privacy",
        ("pii", "privacy", "personal data", "隐私", "个人信息", "敏感数据"),
        "疑似隐私或敏感数据风险，需人工确认合规和审计要求。",
    ),
)


def classify_risk_area(risk: dict[str, Any]) -> RiskSignal:
    path = str(risk.get("path") or risk.get("name") or "未标注路径")
    reason = str(risk.get("reason") or risk.get("summary") or "当前扫描提示需要人工确认。")
    haystack = f"{path} {reason}".lower()
    for category, keywords, confirmation_reason in KEYWORD_CATEGORIES:
        if any(keyword.lower() in haystack for keyword in keywords):
            return RiskSignal(
                path=path,
                reason=reason,
                is_high_impact=True,
                category=category,
                confirmation_reason=confirmation_reason,
            )
    return RiskSignal(
        path=path,
        reason=reason,
        is_high_impact=False,
        category="general",
        confirmation_reason="普通风险线索，仍需维护者确认影响面。",
    )


def high_impact_risk_areas(risks: list[dict[str, Any]]) -> list[RiskSignal]:
    return [signal for signal in (classify_risk_area(risk) for risk in risks) if signal.is_high_impact]


def risk_slug(path: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", path.strip().lower()).strip("-")
    return slug or "unknown"
