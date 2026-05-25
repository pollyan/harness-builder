# Scanner Skill 重构计划：从"LLM 兜底"到"脚本收集 + LLM 理解"流水线

> 日期：2026-05-25
> 状态：待确认
> 前置：Scanner 第一阶段已完成（113 tests passing）

---

## 1. 为什么要重构

当前架构的问题：

1. **确定性脚本同时做收集和推断**。比如 `_build_command_catalog()` 硬编码了"看到 pom.xml 就猜 mvn clean package"——这是推断，不是事实收集。
2. **LLM 定位为"可选兜底"**。但真正需要推理的工作（技术栈判断、模块职责、命令候选）恰恰是 LLM 最擅长的。
3. **两层输出混在一起**。确定性事实和推断结论没有明确分开，后续 Skill 无法区分"哪些是硬事实、哪些是推测"。

重构目标：

```
脚本负责收集原始证据（文件列表、XML/JSON 内容解析、文件统计）
    ↓
确定性规则做高置信度快速推断（有 pom.xml → 构建文件存在）
    ↓
LLM 基于全部证据做深度理解（技术栈、模块职责、命令候选、异常检测）
    ↓
合并输出，明确标注来源和置信度
```

## 2. 重构后的数据流

```
repo_root
  │
  ├── detectors/filesystem.py ─────→ 文件列表、目录结构、扩展名统计
  ├── detectors/java_maven.py ─────→ pom.xml 列表、module 列表、Spring 配置列表、SQL 列表
  ├── detectors/node_frontend.py ──→ package.json 列表、scripts 内容、依赖列表、vue 文件数
  ├── detectors/dotnet.py ─────────→ sln 列表、csproj 列表、ProjectReference、测试项目
  ├── detectors/ci_docker.py ──────→ CI workflow 列表、Dockerfile 列表、compose 列表
  ├── detectors/shallow_code.py ───→ Controller/Service/Entity/Test 文件列表
  ├── detectors/generic_fallback.py → README、scripts 目录、config 目录
  │
  ▼
  evidence.json（原始证据，全部来自确定性脚本）
  │
  ▼
  LLM 分析（基于 evidence.json）
  │
  ├── 技术栈判断（主/辅、置信度、证据链）
  ├── 模块职责推测（每个模块做什么、置信度）
  ├── 命令候选生成（build/test/run/frontend/docker、参考 CI 和 scripts）
  ├── 架构模式识别（分层/Clean/微服务等）
  ├── 异常信号检测（多构建系统、缺失文档、结构异常）
  └── 校准建议（需要人工确认的点）
  │
  ▼
  合并输出：
  ├── project-inventory.json（确定性事实 + LLM 推断，来源标注）
  ├── command-catalog.yaml（命令候选，标注来自规则还是 LLM）
  └── scanner-report.md（人类可读报告）
```

## 3. 变更范围

### 3.1 需要改的文件

| 文件 | 改什么 | 为什么 |
|------|--------|--------|
| `core.py` | 重构 `scan_repository()`：先收集证据，再调用 LLM 分析，最后合并。`_build_command_catalog()` 删除，命令生成移到 LLM。 | 核心流水线重构 |
| `llm_hints.py` | 重命名为 `llm_analyzer.py`。从"生成 hints"升级为"完整分析"。prompt 大幅增强，增加命令候选和架构模式输出。 | LLM 从配角变主角 |
| `cli.py` | `--llm` 从可选标志改为默认行为。新增 `--no-llm` 用于离线/无 key 场景。 | LLM 分析层默认必须 |
| `report.py` | 报告内容增强：展示 LLM 分析结果，标注确定性事实 vs 推断。 | 报告需要区分事实和推断 |

### 3.2 需要新建的文件

| 文件 | 做什么 |
|------|--------|
| `detectors/llm_analyzer.py` | LLM 分析引擎（从 llm_hints.py 演化，职责扩展） |
| `detectors/evidence_builder.py` | 把各 detector 结果组装成标准化 evidence 结构，供 LLM 消费 |

### 3.3 需要删除的文件

| 文件 | 原因 |
|------|------|
| `detectors/llm_hints.py` | 被 `llm_analyzer.py` 替代（迁移后删除） |

### 3.4 不动的文件

| 文件 | 原因 |
|------|------|
| `detectors/filesystem.py` | 事实收集层，不需要改 |
| `detectors/java_maven.py` | 事实收集层，不需要改 |
| `detectors/node_frontend.py` | 事实收集层，不需要改 |
| `detectors/dotnet.py` | 事实收集层，不需要改 |
| `detectors/ci_docker.py` | 事实收集层，不需要改 |
| `detectors/shallow_code.py` | 事实收集层，不需要改 |
| `detectors/generic_fallback.py` | 事实收集层，不需要改 |
| `models.py` | ScanContext 不变 |

## 4. 新增的输出结构

### 4.1 evidence（LLM 的输入）

```json
{
  "repo": {
    "name": "RuoYi-Vue",
    "path": "/path/to/RuoYi-Vue"
  },
  "filesystem": {
    "topLevelDirectories": ["sql", "ruoyi-ui", ...],
    "keyFiles": ["pom.xml", "ruoyi-ui/package.json", ...],
    "fileCounts": {"total": 320, "byExtension": {".java": 85, ".vue": 106, ...}}
  },
  "java": {
    "detected": true,
    "buildFiles": ["pom.xml", "ruoyi-admin/pom.xml", ...],
    "mavenModules": [...],
    "springConfigFiles": [...],
    "sqlAssets": [...]
  },
  "node": {...},
  "dotnet": {...},
  "ci": {...},
  "codeStructure": {...},
  "genericFallback": {...}
}
```

这是各 detector 的原始输出汇总，不加任何推断。

### 4.2 LLM 分析结果（新增字段）

```json
{
  "stackAnalysis": {
    "primary": {
      "name": "Java / Spring Boot / Maven",
      "confidence": "high",
      "evidence": ["7 pom.xml files found", "Spring Boot application.yml detected", "6 Maven modules"]
    },
    "secondary": [
      {"name": "Vue.js", "confidence": "high", "evidence": ["106 .vue files", "package.json with vue dependency"]}
    ]
  },
  "moduleAnalysis": [
    {
      "module": "ruoyi-admin",
      "guessedRole": "Web 入口模块，包含 Spring Boot Application 启动类",
      "confidence": "medium",
      "evidence": ["有独立 pom.xml", "模块名含 admin"]
    }
  ],
  "commandCandidates": [
    {
      "category": "build",
      "command": "mvn clean package -DskipTests",
      "workingDirectory": ".",
      "confidence": "high",
      "source": "rule",
      "evidence": ["pom.xml detected at root"]
    },
    {
      "category": "frontend",
      "command": "npm run build:prod",
      "workingDirectory": "ruoyi-ui",
      "confidence": "high",
      "source": "llm",
      "evidence": ["ruoyi-ui/package.json has build:prod script"]
    }
  ],
  "architecturePattern": {
    "pattern": "Multi-module monolith with separate frontend",
    "confidence": "medium",
    "evidence": ["6 Maven modules", "Separate npm project in ruoyi-ui/"]
  },
  "anomalies": [
    {
      "message": "No CI/CD configuration found",
      "confidence": "medium",
      "evidence": ["No .github/workflows/, no Jenkinsfile, no .gitlab-ci.yml"]
    }
  ],
  "calibrationPoints": [
    {
      "message": "确认 Maven profile 配置（开发/生产环境差异）",
      "confidence": "low",
      "evidence": ["Spring Boot project typically uses profiles"]
    }
  ]
}
```

### 4.3 project-inventory.json（合并后）

在现有基础上增加：
- `evidence` 字段：原始证据汇总
- `llmAnalysis` 字段：LLM 分析结果
- 命令候选从 `command-catalog.yaml` 合并进来，每条标注 `source: "rule"` 或 `source: "llm"`

## 5. 命令候选的生成逻辑变更

**现状：** 硬编码在 `_build_command_catalog()`，看到 pom.xml 就生成 `mvn clean package`。

**重构后：**

1. 确定性规则仍然生成高置信度候选（`source: "rule"`），例如看到 pom.xml → `mvn clean package`
2. LLM 基于完整证据生成更全面的候选（`source: "llm"`），例如：
   - 从 CI workflow 文件内容提取实际用的构建命令
   - 从 package.json scripts 提取所有可用命令
   - 推断非标准构建方式（如 Makefile、自定义脚本）
3. 合并时去重，rule 和 llm 矛盾的标记为校准点

## 6. 向后兼容

- `--no-llm` 模式下行为与当前完全一致（只用确定性规则生成命令）
- `project-inventory.json` 保留所有现有字段，只新增不删除
- `command-catalog.yaml` 格式不变，只新增 `source` 字段
- 所有现有 113 个测试必须继续通过

## 7. 测试策略

| 类型 | 数量 | 说明 |
|------|------|------|
| 不动的测试 | ~85 | 7 个 detector + models + report 的测试完全不动 |
| 修改的测试 | ~15 | core.py 和 cli.py 的测试适配新接口 |
| 新增的测试 | ~25 | evidence_builder、llm_analyzer、合并逻辑 |
| **预期总计** | **~125** | |

### 新增测试重点

1. **evidence_builder**：各 detector 输出正确汇总、空仓库兜底
2. **llm_analyzer**：prompt 构建、响应解析、四种分析结果格式化、异常降级
3. **合并逻辑**：rule 和 llm 命令候选去重、矛盾标记为校准点
4. **端到端**：`--no-llm` 模式输出与重构前一致

## 8. 实施步骤

### Step 1：新建 evidence_builder.py

把 `core.py` 里收集证据的逻辑抽成独立模块，产出标准化 evidence dict。

**验证点：** evidence_builder 输出的 evidence 结构正确、包含所有 detector 结果。

### Step 2：新建 llm_analyzer.py

从 llm_hints.py 演化，职责从"生成 hints"扩展为"完整分析"：
- 接收 evidence dict
- 构建 prompt（包含完整证据）
- 解析 LLM 响应为结构化分析结果
- 异常降级：LLM 失败时返回基于规则的分析结果

**验证点：** mock caller 测试 prompt 构建、响应解析、降级逻辑。

### Step 3：重构 core.py

- `scan_repository()` 改为三阶段流水线：收集证据 → LLM 分析 → 合并输出
- 删除 `_build_command_catalog()`，命令生成拆分到规则快速通道 + LLM 分析
- `ScanResult` 结构适配

**验证点：** 现有测试全部通过（`--no-llm` 模式行为不变）。

### Step 4：重构 cli.py

- `--llm` 改为默认行为
- 新增 `--no-llm` 离线模式
- 输出文件内容适配新结构

**验证点：** CLI 测试全部通过，真实仓库冒烟。

### Step 5：增强 report.py

报告内容区分确定性事实和 LLM 推断。

**验证点：** 报告测试通过。

### Step 6：清理

- 删除旧 `llm_hints.py`
- 更新现有测试适配新接口
- 补充新测试到 ~125 个
- 全量通过后提交

### Step 7：真实仓库冒烟

用 RuoYi-Vue 和 eShopOnWeb 做端到端验证（需要 LLM API key）。

## 9. 风险

| 风险 | 缓解 |
|------|------|
| LLM 响应格式不稳定 | prompt 明确要求 JSON 格式 + 解析层容错 |
| LLM 调用失败 | 降级到纯规则模式，不影响基本扫描 |
| 测试回归 | 每步都跑全量测试，确保 113 个现有测试不 break |
| LLM API key 不可用 | `--no-llm` 模式保证离线可用 |

## 10. 完成标准

1. 所有 ~125 个测试通过
2. `--no-llm` 模式输出与重构前完全一致
3. `--llm` 模式（默认）输出包含 evidence + llmAnalysis + 标注来源的命令候选
4. RuoYi-Vue 和 eShopOnWeb 冒烟通过
5. project-inventory.json 结构向后兼容（只新增不删除）
