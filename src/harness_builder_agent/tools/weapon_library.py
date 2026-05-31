from __future__ import annotations

from harness_builder_agent.schemas.command_catalog import CommandCatalog
from harness_builder_agent.schemas.project_inventory import ProjectInventory
from harness_builder_agent.schemas.weapon_library import WeaponLibraryEntry, WeaponLibrarySelection


WEAPON_LIBRARY: tuple[WeaponLibraryEntry, ...] = (
    WeaponLibraryEntry(
        id="common.guide.project-facts",
        stack="common",
        kind="guide",
        title="项目事实优先",
        guidance="所有规则必须先绑定扫描出的模块、配置、CI 和文档证据，缺少证据时保持 candidate 状态。",
        recommended_action="在 Guide 中保留来源证据和人工确认点，避免把推断直接升级为团队规范。",
        evidence_hints=["project-inventory.json", "scan-report.md"],
        tags=["evidence", "governance"],
    ),
    WeaponLibraryEntry(
        id="common.guide.change-risk",
        stack="common",
        kind="guide",
        title="变更风险分级",
        guidance="接口、权限、配置、数据访问和构建脚本变更默认高于普通文案或样式变更。",
        recommended_action="为高风险目录补充更严格的 Guide，并要求任务执行前说明影响面。",
        evidence_hints=["modules", "configs", "ci_files"],
        tags=["risk", "review"],
    ),
    WeaponLibraryEntry(
        id="common.sensor.hard-gate-policy",
        stack="common",
        kind="sensor",
        title="Hard gate 策略",
        guidance="稳定、快速、可重复的构建或测试命令应作为 hard gate；失败时任务不能声明完成。",
        recommended_action="将已发现且置信度较高的 build/test 命令纳入验证清单。",
        gate="hard",
        evidence_hints=["command-catalog.yaml"],
        tags=["verification", "hard-gate"],
    ),
    WeaponLibraryEntry(
        id="common.sensor.missing-capability",
        stack="common",
        kind="sensor",
        title="缺失能力显式记录",
        guidance="缺少 lint、typecheck 或安全检查时，不编造通过结果，必须记录为待补齐 Sensor。",
        recommended_action="在 Sensors 中列出缺口，并要求维护者确认是否升级为团队标准。",
        gate="soft",
        evidence_hints=["command-catalog.yaml"],
        tags=["gap", "sensor"],
    ),
    WeaponLibraryEntry(
        id="java-spring.guide.maven-boundary",
        stack="java-spring",
        kind="guide",
        title="Maven 模块边界",
        guidance="确认 Maven 多模块之间的依赖边界，Controller 只处理接口入口和参数映射，业务逻辑下沉到 Service。",
        recommended_action="跨层调用、公共依赖和模块耦合变更需要在 Guide 中明确影响范围。",
        evidence_hints=["pom.xml", "src/main/java"],
        tags=["maven", "architecture"],
    ),
    WeaponLibraryEntry(
        id="java-spring.guide.auth-sql-config-risk",
        stack="java-spring",
        kind="guide",
        title="登录权限 SQL 配置风险",
        guidance="登录、权限、SQL、Mapper、Repository 和配置变更默认需要更严格 Sensor。",
        recommended_action="为认证授权、数据访问和配置目录补充风险说明与人工确认点。",
        evidence_hints=["controller", "mapper", "application.yml"],
        tags=["auth", "sql", "config"],
    ),
    WeaponLibraryEntry(
        id="java-spring.sensor.maven-test",
        stack="java-spring",
        kind="sensor",
        title="Maven 验证命令",
        guidance="Java Spring 项目优先识别并运行 Maven test/package 类命令，作为后端 hard gate 候选。",
        recommended_action="发现 `mvn test`、`mvn package` 或 wrapper 命令时纳入验证清单；缺失时记录人工补齐。",
        gate="hard",
        evidence_hints=["pom.xml", "mvnw"],
        tags=["maven", "test"],
    ),
    WeaponLibraryEntry(
        id="java-spring.sensor.auth-sql-config-risk",
        stack="java-spring",
        kind="sensor",
        title="认证数据配置风险验证",
        guidance="登录、权限、SQL 和配置变更至少需要测试命令、集成验证或人工确认之一。",
        recommended_action="当任务命中这些风险区域时，在 Sensor report 中记录验证结果或跳过原因。",
        gate="soft",
        evidence_hints=["security", "mapper", "application.yml"],
        tags=["auth", "sql", "config"],
    ),
    WeaponLibraryEntry(
        id="dotnet-aspnet.guide.solution-boundary",
        stack="dotnet-aspnet",
        kind="guide",
        title="Solution 和项目边界",
        guidance="确认 solution / project 边界与 Clean Architecture 分层一致，ApplicationCore 保持领域规则中心位置。",
        recommended_action="PublicApi、Web、Infrastructure、测试项目之间的协作关系需要在 Guide 中说明。",
        evidence_hints=["*.sln", "*.csproj"],
        tags=["solution", "clean-architecture"],
    ),
    WeaponLibraryEntry(
        id="dotnet-aspnet.guide.publicapi-config-risk",
        stack="dotnet-aspnet",
        kind="guide",
        title="PublicApi 与配置风险",
        guidance="PublicApi / Web 文案、appsettings 和 Infrastructure 变更需要关注外部依赖与运行环境。",
        recommended_action="为 API、配置和基础设施变更记录测试依赖、环境变量和人工确认点。",
        evidence_hints=["PublicApi", "appsettings.json", "Infrastructure"],
        tags=["publicapi", "config", "infrastructure"],
    ),
    WeaponLibraryEntry(
        id="dotnet-aspnet.sensor.dotnet-test",
        stack="dotnet-aspnet",
        kind="sensor",
        title="dotnet test 验证命令",
        guidance=".NET ASP.NET 项目优先识别 `dotnet test`，作为 solution 级 hard gate 候选。",
        recommended_action="发现测试项目或 solution 时纳入 `dotnet test`；缺失时记录为待补齐 Sensor。",
        gate="hard",
        evidence_hints=["*.sln", "*Tests.csproj"],
        tags=["dotnet", "test"],
    ),
    WeaponLibraryEntry(
        id="dotnet-aspnet.sensor.publicapi-appsettings-risk",
        stack="dotnet-aspnet",
        kind="sensor",
        title="PublicApi 和 appsettings 风险验证",
        guidance="PublicApi、Web、Infrastructure 和 appsettings 变更至少需要测试命令或人工确认。",
        recommended_action="当任务命中 API、配置或基础设施目录时，记录 dotnet test 结果或明确 skipped 原因。",
        gate="soft",
        evidence_hints=["PublicApi", "Web", "Infrastructure", "appsettings.json"],
        tags=["publicapi", "config", "infrastructure"],
    ),
    WeaponLibraryEntry(
        id="python-flask.guide.api-boundary",
        stack="python-flask",
        kind="guide",
        title="Flask API 边界",
        guidance="确认 Flask 路由、Service、配置和数据访问边界，避免把接口入口、业务逻辑和运行配置混在同一变更里。",
        recommended_action="为 Flask 后端入口、配置文件和关键业务模块补充 Guide，并记录模块职责。",
        evidence_hints=["pyproject.toml", "requirements.txt", "app.py"],
        tags=["python", "flask", "architecture"],
    ),
    WeaponLibraryEntry(
        id="python-flask.sensor.pytest",
        stack="python-flask",
        kind="sensor",
        title="pytest 验证命令",
        guidance="Python Flask 项目优先识别 `pytest` 或等价测试入口，作为后端 hard gate 候选。",
        recommended_action="发现 pytest 入口时纳入验证清单；缺失时记录为待补齐 Sensor。",
        gate="hard",
        evidence_hints=["pyproject.toml", "requirements.txt", "tests"],
        tags=["python", "flask", "test"],
    ),
    WeaponLibraryEntry(
        id="node.guide.frontend-boundary",
        stack="node",
        kind="guide",
        title="前端模块边界",
        guidance="确认 React / TypeScript 前端入口、组件边界、构建配置和后端 API 协作方式。",
        recommended_action="为前端目录、构建脚本、状态管理和 API 调用边界补充 Guide。",
        evidence_hints=["package.json", "src", "vite.config.ts"],
        tags=["frontend", "react", "typescript"],
    ),
    WeaponLibraryEntry(
        id="node.sensor.npm-test",
        stack="node",
        kind="sensor",
        title="npm 验证命令",
        guidance="Node / 前端项目优先识别 `npm test`、`npm run lint`、`npm run build` 等验证入口。",
        recommended_action="发现 npm 验证命令时纳入 Sensor；缺失时记录为前端验证缺口。",
        gate="hard",
        evidence_hints=["package.json"],
        tags=["frontend", "node", "test"],
    ),
)


def select_weapon_library(inventory: ProjectInventory, commands: CommandCatalog) -> WeaponLibrarySelection:
    selected_stacks = _selected_stack_keys(inventory)

    entries = [entry for entry in WEAPON_LIBRARY if entry.stack in selected_stacks]
    guide_weapons = [entry for entry in entries if entry.kind == "guide"]
    sensor_weapons = [entry for entry in entries if entry.kind == "sensor"]

    if commands.commands:
        sensor_weapons = _promote_matching_hard_gates(sensor_weapons, commands)

    return WeaponLibrarySelection(
        primary_stack=inventory.primary_stack,
        selected_stacks=selected_stacks,
        guide_weapon_ids=[entry.id for entry in guide_weapons],
        sensor_weapon_ids=[entry.id for entry in sensor_weapons],
        guide_weapons=guide_weapons,
        sensor_weapons=sensor_weapons,
    )


def _selected_stack_keys(inventory: ProjectInventory) -> list[str]:
    selected = ["common"]
    if inventory.primary_stack == "unknown":
        return selected
    stack_values = [inventory.primary_stack, *inventory.stacks]
    aliases = {
        "java": "java-spring",
        "spring": "java-spring",
        "spring-boot": "java-spring",
        "maven": "java-spring",
        "dotnet": "dotnet-aspnet",
        ".net": "dotnet-aspnet",
        "aspnet": "dotnet-aspnet",
        "aspnet-core": "dotnet-aspnet",
        "node": "node",
        "npm": "node",
        "javascript": "node",
        "typescript": "node",
        "react": "node",
        "vue": "node",
        "vite": "node",
        "python": "python-flask",
        "flask": "python-flask",
        "python-flask": "python-flask",
    }
    for raw_stack in stack_values:
        stack = aliases.get(raw_stack.strip().lower(), raw_stack.strip().lower())
        if stack in {"java-spring", "dotnet-aspnet", "node", "python-flask"} and stack not in selected:
            selected.append(stack)
    return selected


def _promote_matching_hard_gates(
    sensor_weapons: list[WeaponLibraryEntry], commands: CommandCatalog
) -> list[WeaponLibraryEntry]:
    command_text = " ".join(command.command for command in commands.commands).lower()
    promoted: list[WeaponLibraryEntry] = []
    for weapon in sensor_weapons:
        if weapon.id == "java-spring.sensor.maven-test" and "mvn" in command_text:
            promoted.append(weapon.model_copy(update={"recommended_action": "已发现 Maven 命令，建议作为 Java 后端 hard gate 候选。"}))
        elif weapon.id == "dotnet-aspnet.sensor.dotnet-test" and "dotnet test" in command_text:
            promoted.append(weapon.model_copy(update={"recommended_action": "已发现 dotnet test，建议作为 .NET solution hard gate 候选。"}))
        elif weapon.id == "python-flask.sensor.pytest" and "pytest" in command_text:
            promoted.append(weapon.model_copy(update={"recommended_action": "已发现 pytest，建议作为 Python Flask 后端 hard gate 候选。"}))
        elif weapon.id == "node.sensor.npm-test" and "npm" in command_text:
            promoted.append(weapon.model_copy(update={"recommended_action": "已发现 npm 验证命令，建议作为前端 hard gate 候选。"}))
        else:
            promoted.append(weapon)
    return promoted
