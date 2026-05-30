# Harness Weapon Library 实施计划

> **For agentic workers:** 按 TDD 执行。先写失败测试，再实现最小代码，通过后再重构。每个阶段保持小步提交。

## 目标

把技术栈专属 Guides / Sensors 从临时生成逻辑升级为可审计的内置武器库。生成结果必须稳定、可解释，并能通过 benchmark 验收。

## 范围

- 新增结构化武器库，覆盖 `common`、`java-spring`、`dotnet-aspnet`。
- 生成 `.ai/weapon-library-selection.yaml`。
- Guides / Sensors 显式引用被选中的 weapon id。
- Benchmark 校验选择文件、schema 和内容引用。
- 保持现有 CLI、Workflow Skill、成熟度和 improve 产物兼容。

## 实施步骤

1. RED：补集成测试
   - 在 fixture 初始化测试中断言 `weapon-library-selection.yaml` 存在。
   - 断言 Java Spring 输出包含 `java-spring.*` weapon id。
   - 断言 .NET 输出包含 `dotnet-aspnet.*` weapon id。
   - 断言 Guides / Sensors 均有“武器库匹配结果”章节。

2. RED：补 benchmark 测试
   - 断言 benchmark report 包含 `exists:weapon-library-selection.yaml`。
   - 断言 benchmark report 包含 `schema:weapon-library-selection`。
   - 断言 benchmark report 包含 `content:weapon-library-selection`。

3. GREEN：实现武器库模型和选择逻辑
   - 新增 `WeaponLibrarySelection` schema。
   - 新增内置 weapon entries 和 `select_weapon_library()`。
   - 保证选择逻辑只依赖扫描结果和内置数据，结果可重复。

4. GREEN：接入生成流程
   - `write_initial_assets()` 写出选择文件。
   - Guides / Sensors 从选择结果组装规则、建议和验证活动。
   - 成熟度证据记录武器库命中情况。

5. GREEN：接入 benchmark
   - REQUIRED_FILES 增加选择文件。
   - schema checks 增加 `WeaponLibrarySelection`。
   - content checks 校验 Guide / Sensor 引用所选 weapon id。

6. 验证
   - 运行新增测试，确认先失败后通过。
   - 运行全量 pytest。
   - 运行真实 fixture / benchmark 流程，确认产物完整。

7. 收尾
   - 小步提交文档和实现。
   - 推送 `main`。
