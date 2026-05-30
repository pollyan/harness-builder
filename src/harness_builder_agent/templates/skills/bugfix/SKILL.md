---
name: bugfix
description: 用于明确缺陷、错误提示、失败行为或回归问题的项目级 AI Coding 工作流。
---

# 缺陷修复工作流

## 使用条件

当任务描述包含修复、错误、bug、失败、异常或回归线索时使用本 Skill。

## 必读资产

- `.ai/guides/project-context.md`
- `.ai/guides/architecture.md`
- `.ai/guides/coding-rules.md`
- `.ai/guides/task-templates/bugfix.md`
- `.ai/sensors/verification.md`

## 执行步骤

1. 复述错误现象、期望行为和已知约束。
2. 根据 Harness Map 定位最小相关模块和风险点。
3. 优先寻找已有测试、接口、配置或日志线索。
4. 制定最小修复策略；当前 POC 可只生成受控交接资产，不强制修改业务代码。
5. 执行 targeted hard gate Sensor。
6. Sensor 失败时记录命令、状态、摘要、影响和人工下一步。
7. 输出 Decision Log、Sensor Report、Handoff Summary 和 Experience Candidate。

## 交付要求

- 修复判断必须引用项目事实或 Sensor 结果。
- 不把单次经验直接写入正式 Guides / Sensors。
- 高风险或低置信度情况必须进入人工确认。
