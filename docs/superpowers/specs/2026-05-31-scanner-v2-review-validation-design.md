# Scanner v2 Review and Validation Migration Design

## 背景

当前 `harness_builder_agent` 的扫描链路已经是 LLM-first：

```text
collect_evidence
  -> analyze_evidence_with_llm
  -> reconcile_scan
  -> ProjectInventory + CommandCatalog + ScanMetadata
```

大仓库 evidence depth v1 已完成，当前 evidence 已支持 bucket、priority、coverage、warnings、test/API/risk evidence，并把 coverage 写入 `scan-metadata.yaml` 和 LLM prompt。

Git 历史里曾存在旧 scanner v2，位于 `harness_builder/scanner/`，在 `50413fc chore: remove legacy scanner package` 中删除。相关 smoke test 保留在 `docs/research/scanner-v2-smoke-test.md`。

## 审查范围

审查的历史提交和文件：

- `67f6512 feat(scanner-v2): add deepseek_client.py`
- `4b8bf8f feat(scanner-v2): add file_tree_collector`
- `ff3d07f feat(scanner): add LLM scan engine with two-round self-check`
- `06ae874 feat(scanner): add evidence_extractor`
- `a7b51c6 refactor(scanner): core.py five-stage pipeline`
- `df61508 fix(scanner-v2): harden real LLM smoke handling`
- `9b12c51 docs(scanner-v2): finalize POC README and JS stack handling`
- `50413fc chore: remove legacy scanner package`

Key files reviewed from `50413fc^`:

- `harness_builder/scanner/core.py`
- `harness_builder/scanner/detectors/file_tree_collector.py`
- `harness_builder/scanner/detectors/llm_scanner.py`
- `harness_builder/scanner/detectors/evidence_extractor.py`
- `tests/scanner/test_core.py`
- `tests/scanner/test_evidence_extractor.py`
- `tests/scanner/test_llm_scanner.py`
- `docs/research/scanner-v2-smoke-test.md`

## 旧 scanner v2 能力判断

### 已被当前实现覆盖

- 轻量文件清单：当前 `EvidenceBundle.files` 已记录全量 evidence file list，并按 bucket/priority/coverage 选择 LLM 输入。
- 技术栈 evidence：当前 bucket evidence、key files、source samples、test/API/risk files 已覆盖主要事实输入。
- 命令证据调和：当前 `scan_reconciler._command_from_candidate` 已对缺证据 hard command 降级并写 warning。
- smoke test 中的真实仓库目标：当前 acceptance 仍以 RuoYi-Vue 和 eShopOnWeb 为重点。

### 值得迁移

1. **显式 LLM claim validation**

   旧 `_validate()` 会把 LLM 声称的 Java/Node/.NET 与 deterministic evidence 对比，产出 validation points。当前 `scan_reconciler` 已有 `_veto_impossible_stack()` 和 command warning，但 validation 不是一等产物。迁移价值明确：能把“LLM 推断 vs evidence 支持/冲突”写入 `ScanMetadata.warnings` 和 `ProjectInventory.stack_extensions`，便于 benchmark、人工确认和后续 scanner v2 迁移。

2. **嵌套 stackAnalysis / keyword false positive 的经验**

   旧 `evidence_extractor._flatten_text()` 和 `_keyword_matches()` 解决了真实 LLM 输出结构不稳定、`JavaScript` 被误判为 Java 的问题。当前新 schema 已把 LLM 输出规整为 `primary_stack`、`stacks` 和 `command_candidates`，不需要迁移旧自由形状解析，但“避免 substring false positive”的原则应进入 validation 设计。

3. **两轮 LLM self-check 的设计方向**

   旧 `llm_scanner` 的 round 2 self-check 可以提升覆盖意识，但旧实现中 round 2 失败会降级使用 round 1，且 caller 缺失会返回 `enabled=False`。这与当前 no silent fallback 规则冲突。第一轮不迁移两轮调用，只在目标架构里保留为未来候选：如果引入，必须有 Pydantic schema、显式配置和失败即失败或显式 degraded warning 的清晰语义。

4. **targeted evidence extraction 的设计方向**

   旧 `evidence_extractor` 会根据 LLM claim 选择 detector。这对 claim validation 有启发，但当前 evidence collector 已先收集事实，不应让 LLM 决定是否收集 evidence。第一轮不迁移 targeted detector；未来如做，应是“额外验证器”，不是替代基础 evidence collection。

### 不应迁移或需要重写

- `--no-llm` 成功扫描模式：违反当前 LLM-first 和 no silent fallback 规则。
- LLM caller 缺失时返回 `{"enabled": False}` 并继续成功：违反 DeepSeek 不可用必须显式失败的规则。
- JSON parse/schema 失败后返回 disabled analysis：违反机器消费 LLM 输出必须 schema 校验的规则。
- detector `_safe_detect()` 捕获异常后继续成功：可能隐藏 evidence 质量问题；如需要保留，必须转为显式 warning 或 validation finding。
- 旧 command catalog 分组形状 `build/test/run/frontend/docker`：当前 `CommandCatalog(commands: list[CommandDefinition])` 更稳定，不迁移旧形状。
- 旧 `harness_builder/scanner/` 包结构：已删除且与当前 `harness_builder_agent` 架构不一致，不恢复。

## 迁移目标

第一轮迁移只实现一件事：把旧 scanner v2 的 claim validation 思路融入当前 `scan_reconciler`。

新增行为：

- `reconcile_scan()` 根据 `LLMScanProposal.primary_stack`、`LLMScanProposal.stacks` 和 `EvidenceBundle` 生成 validation warnings。
- 对 supported stack 进行 evidence validation：
  - `java-spring` 需要 `.java`、`pom.xml`、`build.gradle` 或 Spring 相关 evidence。
  - `dotnet-aspnet` 需要 `.sln`、`.csproj` 或 `.cs` evidence。
  - `node` 相关 stack 需要 `package.json`、`.js`、`.ts`、`.tsx` 或 `.vue` evidence。
- 明显不可能的 primary stack 继续抛 `ScanConflictError`，保持显式失败。
- 非 primary 或补充 stack 缺少 evidence 时，不直接失败；写入 `ScanWarning(code="llm_stack_claim_without_evidence", severity="warning")`，并设置 `needs_human_confirmation` 相关上下文。
- validation summary 写入 `ProjectInventory.stack_extensions["scan_validation"]`，包含 checked claims、unsupported claims 和 supported claims。
- `ScanMetadata.warnings` 包含 validation warning，benchmark 可通过现有 scan metadata/schema 检查读取。

## 非目标

- 不恢复旧 scanner package。
- 不引入两轮 LLM self-check。
- 不引入 targeted detector。
- 不扩展所有语言。
- 不改变当前 `LLMScanProposal` JSON schema。
- 不改变 command catalog 数据形状。

## 目标架构

```text
collect_evidence(root)
  -> EvidenceBundle(files, buckets, coverage, priority evidence)
  -> analyze_evidence_with_llm(evidence)
  -> LLMScanProposal(primary_stack, stacks, modules, commands, risks)
  -> reconcile_scan(evidence, proposal)
       - primary stack veto for impossible claims
       - command evidence downgrade
       - scanner-v2-inspired claim validation warnings
       - scan_validation extension
  -> ProjectInventory + CommandCatalog + ScanMetadata
```

## 数据契约

不新增 Pydantic schema 文件。复用现有：

- `ScanWarning`
- `ScanMetadata.warnings`
- `ProjectInventory.stack_extensions`

`scan_validation` 结构为普通 JSON-compatible dict，作为 `stack_extensions` 的审计上下文：

```json
{
  "checked_claims": ["java-spring", "node"],
  "supported_claims": ["java-spring"],
  "unsupported_claims": [
    {
      "stack": "node",
      "reason": "LLM claimed node but no package.json or JS/TS/Vue evidence was found"
    }
  ]
}
```

## 错误处理

- Primary stack impossible：继续抛 `ScanConflictError`。
- Secondary stack unsupported：写 warning，不伪装成 supported。
- Unknown stack：不强行验证，保留人工确认语义。
- Evidence coverage warning 与 claim validation warning 同时保留，不互相覆盖。

## 测试策略

遵循 TDD：

1. 单测 `scan_reconciler`：secondary `node` claim 无 evidence 时写 `llm_stack_claim_without_evidence` warning。
2. 单测 `scan_reconciler`：primary `java-spring` 无 evidence 仍抛 `ScanConflictError`。
3. 单测 `scan_reconciler`：`JavaScript` / `.js` evidence 不误判为 Java support。
4. 单测 `scan_reconciler`：`scan_validation` 写入 `ProjectInventory.stack_extensions` 和 `ScanMetadata`。
5. Integration：Java Spring fixture 和 .NET fixture 的 `init --non-interactive` 结果不退化，`scan-metadata.yaml` 可解析且不出现错误 validation warning。
6. 默认快速回归通过。

## 验收标准

- 审查结论包含旧 scanner v2 关键文件和提交清单。
- 审查结论明确可迁移能力和不迁移能力。
- 当前扫描链路目标架构清楚。
- 第一轮迁移实现 scanner-v2-inspired claim validation。
- 不破坏 evidence depth v1 的 coverage、priority、bucket 和 scan metadata 行为。
- 新增 validation 行为有单测。
- Java Spring 和 .NET fixture 扫描结果不退化。
- 默认快速回归通过。

