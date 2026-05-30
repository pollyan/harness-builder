# Harness Builder 工程规则索引

本目录存放 Harness Builder 自身开发时使用的工程规则。它们不是用户使用手册，也不是阶段性方案文档，而是给维护者和 Codex 使用的项目级约束。

根目录 `AGENTS.md` 是自动加载入口；本目录文档按需加载。不要在一次任务中默认读取所有文档，除非任务同时跨越多个边界。

## 文档地图

| 文档 | 适用场景 |
| --- | --- |
| `architecture.md` | 修改模块边界、目录结构、职责划分、核心设计时阅读 |
| `init-workflow.md` | 修改 `init` 命令、扫描到生成的主流程、生成资产契约时阅读 |
| `llm-contracts.md` | 修改 DeepSeek、LLM prompt、结构化输出、scan reconcile 时阅读 |
| `testing-strategy.md` | 修改测试、fixture、e2e、acceptance、CI、断言策略时阅读 |
| `sensor-and-gate-rules.md` | 修改 sensors、hard gate、benchmark、验证报告时阅读 |

## 组织原则

1. `AGENTS.md` 放入口索引和硬规则，本目录放详细解释。
2. 文档以中文为主，命令、路径、schema 字段、技术名词保持英文原样。
3. 规则必须可执行，避免“提高质量”“保持健壮”这类空泛表述。
4. 同一条规则只保留一个权威来源，其他文档只引用或摘要，避免漂移。
5. 每份文档都应该说明适用范围、必须遵守的规则、推荐验证方式。
6. 当前工作流过程由 Codex/Superpowers 管理，本目录不重复定义通用开发工作流。

## 当前重点

当前仓库已经具备 Python CLI、LLM-first scan、资产生成、benchmark 和测试分层。后续工程治理的重点是：

- 保持 `init` 主链路可审计、可测试、可失败。
- 确保 LLM 输出进入严格 schema，而不是直接驱动不受控写入。
- 确保生成文件测试具备足够深度，不只检查文件存在。
- 确保 Sensor 和 benchmark 能暴露真实质量问题，而不是把失败包装成成功。

