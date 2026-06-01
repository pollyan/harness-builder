from __future__ import annotations

from collections.abc import Callable

import typer


Prompt = Callable[..., str]


def collect_team_rules(*, prompt: Prompt = typer.prompt) -> list[str]:
    typer.echo("\n团队规则")
    typer.echo("除了仓库本身能扫描出来的信息，你们团队是否还有需要 AI 遵守的规则？")
    typer.echo("建议优先补充这些隐性约束：")
    typer.echo("- 架构边界 / 模块分层：例如 Controller 只能调用 Service，跨模块改动需要先说明影响。")
    typer.echo("- 测试策略 / 必跑验证：例如修改接口必须跑集成测试，前端改动必须跑 lint。")
    typer.echo("- 安全合规 / 数据权限：例如支付、鉴权、隐私数据相关改动必须人工复核。")
    typer.echo("- 发布回滚 / 环境限制：例如配置变更必须说明回滚方式，不直接修改生产配置。")
    typer.echo("- 禁止修改 / 只读区域：例如生成代码、迁移脚本或供应商目录默认只读。")
    typer.echo("这些内容会进入 Guides 与 human-input-needed，但不会被当作扫描事实或正式 routing policy。")
    typer.echo("也可以直接用一段自然语言合并多条规则。")
    answer = prompt("可以输入一段规则说明；暂时没有则直接回车", default="", show_default=False).strip()
    return [answer] if answer else []
