# 大仓库 Evidence 扫描深度增强

## 状态

- 状态：implemented
- 优先级：high
- 发现日期：2026-05-30
- 相关命令：`harness-builder-agent init`
- 相关工程规则：`docs/engineering/init-workflow.md`、`docs/engineering/llm-contracts.md`、`docs/engineering/testing-strategy.md`

## 背景

当前 `init` 的第三步会调用 evidence collector，从目标仓库中收集文件、构建配置、CI、文档和源码样本，再交给 LLM 做结构化扫描。

当前实现适合 POC，但面对大型企业代码库时，存在一个核心风险：仓库文件很多、模块很多、目录结构不规范时，简单采样可能遗漏关键证据，导致 LLM 对技术栈、模块边界、测试命令、风险目录或架构信号判断不完整。

## 当前现状

当前 evidence collector 主要做：

- 遍历仓库文件。
- 忽略 `.git`、`.ai`、`.venv`、`node_modules`、`target`、`bin`、`obj`、`dist`、`build`、`__pycache__` 等目录。
- 收集 key files，例如 `pom.xml`、`package.json`、`.sln`、`.csproj`。
- 收集 config files，例如 `application.yml`、`appsettings.json`、`docker-compose.yml`。
- 收集 `.github/workflows` 下的 CI 文件。
- 收集 README 和 `docs` 文档。
- 收集前 N 个源码样本。
- 输出扩展名统计、文件数量和截断记录。

当前测试覆盖：

- 能捕获关键构建和配置文件。
- 会忽略生成目录和依赖目录。
- 大文件摘要会截断并记录。
- evidence collector 不做 `primary_stack` 决策。

## 问题

当前策略的问题不是“完全不能用”，而是对大仓库缺少深度保证：

- 源码样本按排序截取前 N 个，不能代表真实模块分布。
- 没有按模块、语言、目录、文件类型、风险信号分层采样。
- 没有明确识别测试入口、API 入口、配置热点、CI 命令、架构文档。
- 没有 token budget 和 evidence priority。
- 没有多轮扫描机制，LLM 第一轮发现证据不足时无法要求定向补扫。
- scan metadata 还不能充分表达扫描覆盖率和潜在遗漏风险。

## 理想状态

大仓库 evidence 收集应演进为：

```text
全量轻量索引
  -> 模块/语言/文件类型分层统计
  -> 关键证据优先级排序
  -> 分层采样
  -> LLM 第一轮扫描
  -> LLM 提出需要深挖的 evidence request
  -> 定向补充 evidence
  -> 最终 scan proposal + scan coverage report
```

理想能力：

- 全量索引文件路径和元信息，但不全量读取内容。
- 按语言、模块、目录类型、测试/源码/配置/CI/文档分层采样。
- 给 evidence 标记 priority 和 reason。
- 对大型文件和大型目录给出截断/跳过说明。
- 允许 LLM 返回 follow-up evidence requests。
- 输出 scan coverage 信息，说明扫描了多少、跳过了多少、哪些部分需要人工确认。

## 初步验收标准

未来实现该 todo 时，至少应满足：

- `EvidenceBundle` 或相关 schema 能表达分层 evidence、priority、coverage。
- 大仓库 fixture 能证明不再只取前 N 个源码文件。
- 测试覆盖多模块、多语言、测试目录不规范、配置分散等场景。
- LLM prompt 能看到 evidence coverage，而不是只有零散文件摘要。
- `scan-metadata.yaml` 能记录覆盖度、截断、跳过、follow-up 或人工确认风险。
- benchmark 或测试能检查关键 evidence 不会被普通源码样本挤掉。

## 非目标

第一版不要求：

- 全量语义索引整个仓库。
- 建立向量数据库。
- 保证 100% 不遗漏任何业务细节。
- 支持所有语言和框架。

重点是把当前 POC 的 evidence 收集，从“简单采样”升级为“可审计、可解释、分层、有覆盖度意识”的扫描层。

## 实现结果

- 已扩展 `EvidenceBundle`、`EvidenceFile` 和 `ScanMetadata`，支持 evidence priority、bucket、coverage、重点文件分组和覆盖度 warning。
- Evidence collector 已从“按排序取前 N 个源码样本”升级为“全量轻量索引 + 分桶采样 + 重点 evidence 优先”。
- 当前会识别并输出 `priority_files`、`test_files`、`api_entrypoints`、`risk_files`，并保留 build、config、CI、document、source bucket 的覆盖度统计。
- 大仓库或高数量 source bucket 被截断时，会在 coverage warnings 中记录 skipped 数量和相关 bucket，便于后续人工确认或调试。
- LLM scan prompt 已加入 coverage、priority evidence、test/API/risk evidence 的阅读规则，并使用 `exclude_none=True` 控制 prompt 体积。
- Scan reconciler 已将 coverage 写入 `scan-metadata.yaml` 和 `project-inventory.json` 的 `scan_metadata`，并把 coverage warning 转成可审计的 scan warning。
- 已补充 schema、evidence collector、LLM prompt、scan reconciler、init/e2e 相关测试。

## 已验证

- `.venv/bin/python -m pytest tests/unit/test_evidence_collector.py tests/unit/test_llm_scan_analyzer.py tests/unit/test_scan_reconciler.py tests/unit/test_schema_contracts.py -q`
- `.venv/bin/python -m pytest tests/integration/test_init_on_fixture_projects.py tests/e2e/test_fixture_end_to_end.py -q`
- `scripts/test-full.sh`
