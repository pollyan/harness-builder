# Evidence Depth For Large Repositories Design

## 背景

当前 `collect_evidence()` 已经能收集关键构建文件、配置文件、CI、文档和源码样本，但源码样本仍主要依赖排序后的前 N 个文件。面对大型企业仓库时，这会带来几个问题：

- 多模块仓库中，前 N 个源码文件可能集中在同一个模块。
- 测试目录、API 入口、配置热点和 CI 命令可能被普通源码样本挤掉。
- LLM 只能看到零散 evidence，缺少覆盖率、分层和遗漏风险说明。
- `scan-metadata.yaml` 不能清楚说明本次扫描覆盖了哪些层、跳过了哪些层、哪些需要人工确认。

这个设计目标是把 POC 的 evidence 收集从“简单采样”升级为“可审计、分层、有覆盖度意识”的扫描输入。

## 方案比较

### 方案 A：保持当前 collector，只提高 `max_source_samples`

优点：实现最小。

缺点：仍然按排序截取，不能保证模块、语言、测试、API、配置分布；大仓库 token 成本会增加，但质量不稳定。

结论：不采用。

### 方案 B：引入向量库或全量语义索引

优点：未来可支持更深的语义检索。

缺点：POC 范围过大，需要存储、索引、更新策略和额外依赖；也不符合当前“不建向量数据库”的 todo 非目标。

结论：不采用。

### 方案 C：分层轻量索引 + priority evidence + coverage report

优点：保留确定性 collector 的事实收集边界，不做最终业务判断；能显著改善大仓库 evidence 分布；易测试；能直接增强 LLM prompt 和 scan metadata。

缺点：仍不能保证 100% 不遗漏业务细节；不会自动进行多轮补扫。

结论：采用。

## 设计目标

第一版实现以下能力：

1. 对仓库做全量轻量索引，只读取需要摘要的高价值文件。
2. 对 evidence 标记 `priority`、`reason`、`bucket`。
3. 按构建、配置、CI、文档、测试、API 入口、源码、风险热点等层次采样。
4. 生成 `coverage` 信息，说明文件总量、采样数量、每个 bucket 的 total/selected/skipped。
5. 将 coverage 和 priority evidence 传给 LLM prompt。
6. 将 coverage、truncations、warnings 写进 `scan-metadata.yaml`。
7. 保持 LLM-first：collector 只收集事实和采样依据，不决定最终 primary stack。

## 数据结构

扩展 `EvidenceFile`：

```python
class EvidenceFile(BaseModel):
    path: str
    kind: str
    size_bytes: int | None = None
    summary: str | None = None
    truncated: bool = False
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    reason: str | None = None
    bucket: str | None = None
```

扩展 `EvidenceBundle`：

```python
class EvidenceBucketCoverage(BaseModel):
    bucket: str
    total_count: int
    selected_count: int
    skipped_count: int
    selected_paths: list[str] = []

class EvidenceCoverage(BaseModel):
    schema_version: str = "1.0"
    detected_file_count: int
    selected_evidence_count: int
    bucket_coverage: list[EvidenceBucketCoverage] = []
    warnings: list[dict[str, Any]] = []

class EvidenceBundle(BaseModel):
    ...
    priority_files: list[EvidenceFile] = []
    test_files: list[EvidenceFile] = []
    api_entrypoints: list[EvidenceFile] = []
    risk_files: list[EvidenceFile] = []
    coverage: EvidenceCoverage | None = None
```

兼容性：

- 新字段都有默认值，不破坏现有 schema 调用。
- 旧测试仍可只关注 `key_files`、`config_files`、`documents`、`source_samples`。
- `EvidenceBundle.model_dump_json()` 会自然包含新增字段，LLM prompt 无需额外序列化层。

## Collector 行为

collector 分三步：

1. 全量索引路径和基本元信息。
2. 将文件归入多个 bucket。
3. 按 bucket priority 和 per-bucket limit 选择需要摘要的 evidence。

第一版 bucket：

- `build`：`pom.xml`、`.sln`、`.csproj`、`package.json`、`global.json`。
- `config`：`application*.yml`、`appsettings*.json`、`docker-compose*`、`*.config`、包含 `config` 的 yaml/json。
- `ci`：`.github/workflows/**`。
- `document`：`README*`、`docs/**`。
- `test`：路径或文件名包含 `test`、`tests`、`spec`，以及 Java/.NET 常见测试目录。
- `api_entrypoint`：Controller、Endpoint、Program.cs、Application.java、Router、Route 等入口信号。
- `risk`：配置、认证、SQL、security、auth、database、migration 相关路径。
- `source:<ext>`：普通源码按语言扩展名分层，例如 `source:.java`、`source:.cs`。

priority 规则：

- `critical`：构建文件、CI、API 入口、测试命令来源文件、核心配置。
- `high`：风险热点、架构文档、测试入口。
- `medium`：普通文档、普通源码样本。
- `low`：只用于路径统计、不读取摘要的低价值文件。

采样规则：

- build/config/ci/API/risk 文件优先，不被普通 source samples 挤掉。
- 普通源码按扩展名和顶层目录分层采样。
- 单 bucket 设置上限，避免大仓库单一目录占满 token。
- 所有 skipped 都进入 coverage 统计，而不是静默丢失。

## LLM Prompt 变化

`build_scan_messages()` 继续要求 LLM 输出严格 JSON proposal，不让 LLM 写文件。

新增 prompt 要求：

- 阅读 `coverage`，在证据不足时降低 confidence 或设置 `needs_human_confirmation=true`。
- 优先引用 `priority_files`、`test_files`、`api_entrypoints`、`risk_files`。
- 不要因为没有标准 `tests/` 目录就断定没有测试。
- 当 coverage warnings 显示某些 bucket skipped 较多时，在 `reasoning_summary` 中说明不确定性。

这仍属于机器消费输出，LLM proposal schema 不新增自由文本字段。

## Scan Metadata 变化

`reconcile_scan()` 将 Evidence coverage 写入 `ScanMetadata`：

- `coverage`：coverage 的 machine-readable dump。
- `warnings`：当关键 bucket 没有 evidence、source sampling 被截断、测试文件未发现时记录 warning。
- `truncated_files`：继续保留，并可来自所有被摘要的 evidence。

生成的 `scan-metadata.yaml` 应能回答：

- 本次扫描发现多少文件。
- 实际给 LLM 摘要了多少 evidence。
- 每类 bucket 命中了多少、选择了多少、跳过了多少。
- 哪些遗漏风险需要人工确认。

## 测试策略

新增或增强测试：

- 多模块 fixture：普通源码很多时，`pom.xml`、`*.csproj`、测试文件、API 入口不会被挤掉。
- 多语言 fixture：Java 和 .NET 文件都能按语言 bucket 采样。
- 非标准测试目录：例如 `quality/checks/UserFlowSpec.cs` 仍进入 test bucket。
- 风险热点：`security/AuthConfig.java`、`migrations/*.sql`、`appsettings.Production.json` 进入 risk/config。
- coverage schema：bucket 的 total/selected/skipped 正确。
- prompt：包含 coverage、priority_files、test_files、api_entrypoints。
- metadata：`scan-metadata.yaml` 中包含 coverage 和 warnings。

Acceptance 仍使用真实 DeepSeek，但不新增默认 CI 真实 LLM 测试。

## 非目标

第一版不做：

- 向量库。
- 全量文件内容读取。
- 多轮 LLM follow-up request 执行。
- 完整语义级模块边界推断。
- 100% 不遗漏任何业务细节的保证。

## 验收标准

- `EvidenceBundle` 能表达 priority、bucket、coverage。
- 大仓库 fixture 能证明采样不是简单排序前 N 个。
- LLM prompt 能看到 coverage 和分层 evidence。
- `scan-metadata.yaml` 能记录覆盖度、截断、跳过和风险 warning。
- benchmark 或单测能证明关键 evidence 不会被普通源码样本挤掉。
- `scripts/test-fast.sh` 和真实 acceptance 通过。
