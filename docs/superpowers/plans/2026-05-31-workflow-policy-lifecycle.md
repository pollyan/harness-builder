# Workflow 推荐到 Routing Policy 生命周期实施计划

> **执行要求：** 使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 按任务执行。步骤使用复选框记录状态。

**目标：** 证明并收紧 `recommend-workflow -> improve -> review-maturity -> generate-asset-candidates -> review-candidate applied -> benchmark` 的 routing policy 生命周期。

**架构：** 不新增命令。补一条集成验收串起既有专家命令链路；在 asset candidate parser 和 candidate governance 中收紧 workflow policy apply 边界；让 `generate-asset-candidates` 写完 candidates 后刷新 maturity 派生证据并记录 trace。

**技术栈：** Python、Typer CLI、Pydantic、PyYAML、pytest。

---

### 任务 1：写 RED 集成测试

**文件：**
- 修改：`tests/integration/test_assess_improve_commands.py`

- [x] **步骤 1：添加 workflow policy lifecycle 测试**

新增 `test_workflow_recommendation_can_be_governed_into_routing_policy_lifecycle`：

```python
def test_workflow_recommendation_can_be_governed_into_routing_policy_lifecycle(tmp_path: Path, monkeypatch):
    repo = _prepared_harness_repo(tmp_path, "mini-spring-boot", "java-spring", monkeypatch)
    runner = CliRunner()

    def fake_recommendation(task_id, task_brief, config, evidence_pack, caller=None, llm_config=None):
        return WorkflowRecommendationReport(
            task_id=task_id,
            task_brief=task_brief,
            recommended_workflow="standard",
            matched_rule_ids=["standard-escalation"],
            risk_level="high",
            confidence="high",
            rationale="Domain policy changes should use the standard workflow.",
            required_guides=[".ai/guides/project-context.md", ".ai/guides/architecture.md"],
            required_sensors=[".ai/sensors/verification.md"],
            human_confirmation_required=True,
            evidence_sources=[".ai/harness-config.yaml", ".ai/maturity-evidence.yaml"],
        )

    monkeypatch.setattr("harness_builder_agent.tools.recommend_workflow.recommend_workflow_with_llm", fake_recommendation)

    recommend = runner.invoke(app, ["recommend-workflow", "--repo", str(repo), "--task", "Change settlement approval policy.", "--task-id", "policy-1"])
    assert recommend.exit_code == 0, recommend.output
    before_config = HarnessConfig.model_validate(yaml.safe_load((repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8")))
    before_ids = [rule.id for rule in before_config.workflow_routing.rules]
    assert not (repo / ".ai" / "task-runs").exists()

    improve = runner.invoke(app, ["improve", "--repo", str(repo)])
    assert improve.exit_code == 0, improve.output
    improvements = yaml.safe_load((repo / ".ai" / "improvement-candidates.yaml").read_text(encoding="utf-8"))
    assert any(item["id"] == "experience-workflow-recommendation-review" for item in improvements["candidates"])

    def fake_review(score, evidence_pack, candidates, experience_summary=None):
        assert any(candidate.id == "experience-workflow-recommendation-review" for candidate in candidates.candidates)
        return MaturityReviewReport(
            summary="Workflow recommendation should become a reviewed routing policy candidate.",
            candidate_reviews=[
                {
                    "candidate_id": "experience-workflow-recommendation-review",
                    "decision": "support",
                    "rationale": "The recommendation is grounded in routing evidence.",
                    "risks": ["Routing policy changes require maintainer review."],
                    "suggested_acceptance_checks": ["Benchmark content:workflow-routing-policy passes."],
                    "evidence_sources": [".ai/review/workflow-routing-recommendation.yaml"],
                }
            ],
            missing_candidates=[],
            global_risks=[],
        )

    monkeypatch.setattr("harness_builder_agent.tools.review_maturity.review_maturity_with_llm", fake_review)
    review = runner.invoke(app, ["review-maturity", "--repo", str(repo)])
    assert review.exit_code == 0, review.output

    def fake_assets(score, evidence_pack, improvement_candidates, maturity_review, experience_summary=None):
        return AssetCandidateReport(
            candidates=[
                {
                    "id": "workflow-standard-domain-policy",
                    "kind": "workflow_policy",
                    "source_candidate_id": "experience-workflow-recommendation-review",
                    "source_review_decision": "support",
                    "suggested_path": ".ai/harness-config.yaml",
                    "title": "Escalate domain policy changes",
                    "rationale": "The reviewed recommendation supports a routing update.",
                    "draft_content": "Review-only routing policy update.",
                    "workflow_policy_patch": {
                        "schema_version": "1.0",
                        "operation": "upsert_routing_rule",
                        "target": "workflow_routing.rules",
                        "rule": {
                            "id": "standard-escalation",
                            "selected_workflow": "standard",
                            "rationale": "Escalate high-risk, cross-module, security, low-coverage, and domain policy changes.",
                            "task_type_hints": ["feature", "policy"],
                            "triggers": [
                                "unclear_impact_scope",
                                "high_risk_module",
                                "cross_module_design",
                                "security_or_permission",
                                "insufficient_sensor_coverage",
                                "domain_policy_change",
                            ],
                            "required_guides": [".ai/guides/project-context.md", ".ai/guides/architecture.md"],
                            "required_sensors": [".ai/sensors/verification.md"],
                            "human_confirmation_required": True,
                        },
                    },
                    "evidence_sources": [".ai/review/workflow-routing-recommendation.yaml"],
                    "acceptance_checks": ["Benchmark content:workflow-routing-policy passes."],
                    "risk_level": "high",
                    "review_status": "pending_harness_maintainer_review",
                }
            ]
        )

    monkeypatch.setattr("harness_builder_agent.tools.generate_asset_candidates.generate_asset_candidates_with_llm", fake_assets)
    assets = runner.invoke(app, ["generate-asset-candidates", "--repo", str(repo)])
    assert assets.exit_code == 0, assets.output
    evidence_after_assets = yaml.safe_load((repo / ".ai" / "maturity-evidence.yaml").read_text(encoding="utf-8"))
    assert evidence_after_assets["experience"]["asset_candidate_count"] == 1

    after_candidate_config = HarnessConfig.model_validate(yaml.safe_load((repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8")))
    assert after_candidate_config.model_dump(mode="json") == before_config.model_dump(mode="json")

    apply = runner.invoke(
        app,
        [
            "review-candidate",
            "--repo",
            str(repo),
            "--candidate-id",
            "workflow-standard-domain-policy",
            "--decision",
            "applied",
            "--rationale",
            "Maintainer accepted the workflow policy patch.",
        ],
    )
    assert apply.exit_code == 0, apply.output
    config = HarnessConfig.model_validate(yaml.safe_load((repo / ".ai" / "harness-config.yaml").read_text(encoding="utf-8")))
    assert [rule.id for rule in config.workflow_routing.rules] == before_ids
    standard = next(rule for rule in config.workflow_routing.rules if rule.id == "standard-escalation")
    assert "domain_policy_change" in standard.triggers
    governance = CandidateGovernanceLog.model_validate(yaml.safe_load((repo / ".ai" / "review" / "candidate-governance.yaml").read_text(encoding="utf-8")))
    assert governance.decisions[0].applied_paths == [".ai/harness-config.yaml"]

    monkeypatch.setattr("harness_builder_agent.tools.benchmark.scan_repository", lambda repo_path: _fake_scan(repo_path, "java-spring"))
    benchmark = runner.invoke(app, ["benchmark", "--repo", str(repo), "--profile", "java-spring"])
    assert benchmark.exit_code == 0, benchmark.output
    report = yaml.safe_load((repo / ".ai" / "benchmark-report.yaml").read_text(encoding="utf-8"))
    check_ids = {check["id"]: check for check in report["checks"]}
    assert check_ids["content:workflow-routing-policy"]["passed"] is True
    assert check_ids["content:candidate-governance"]["passed"] is True
    assert check_ids["content:workflow-recommendation-review"]["passed"] is True
```

- [x] **步骤 2：添加 workflow policy defer 不可 applied 测试**

复用已有 `_workflow_policy_candidate()` 或局部 YAML，构造 `source_review_decision: defer`，调用 `review-candidate --decision applied`，期望失败并且 `.ai/harness-config.yaml` 不变。

- [x] **步骤 3：添加 asset candidate parser 负向测试**

在 `tests/unit/test_llm_asset_candidate_generator.py` 中新增：

- `test_parse_asset_candidate_response_rejects_path_traversal_suggested_path`
- `test_parse_asset_candidate_response_rejects_workflow_policy_non_config_target`

- [x] **步骤 4：运行 RED**

运行：`.venv/bin/python -m pytest tests/integration/test_assess_improve_commands.py::test_workflow_recommendation_can_be_governed_into_routing_policy_lifecycle tests/unit/test_llm_asset_candidate_generator.py -q`

预期：lifecycle 测试失败于 maturity evidence 未刷新或 trace 缺失；负向 parser / defer apply 测试失败。

### 任务 2：实现 lifecycle 补强

**文件：**
- 修改：`src/harness_builder_agent/tools/generate_asset_candidates.py`
- 修改：`src/harness_builder_agent/cli.py`
- 修改：`src/harness_builder_agent/tools/llm_asset_candidate_generator.py`
- 修改：`src/harness_builder_agent/tools/candidate_governance.py`

- [x] **步骤 1：asset candidates 后刷新 maturity evidence**

在 `generate_asset_candidates(repo)` 写完 candidates 和 experience index 后调用 `assess_maturity(root)`，确保 asset candidate count 进入 maturity evidence。

- [x] **步骤 2：CLI trace 增加派生证据**

在 `generate_asset_candidates_command` 中记录：

```python
trace.artifact(output_dir / "experience" / "experience-index.yaml", "experience_index")
trace.artifact(output_dir / "maturity-score.yaml", "maturity_score")
trace.artifact(output_dir / "maturity-evidence.yaml", "maturity_evidence")
```

- [x] **步骤 3：收紧 asset candidate suggested_path 校验**

新增 helper：

```python
def _is_safe_ai_path(path: str) -> bool:
    parts = path.split("/")
    return len(parts) > 1 and parts[0] == ".ai" and all(part not in {"", ".", ".."} for part in parts[1:])
```

parser 中用它替代 `startswith(".ai/")`，并要求 workflow_policy 的 `suggested_path == ".ai/harness-config.yaml"`。

- [x] **步骤 4：收紧 workflow policy apply**

在 `review_candidate()` 中，当 `decision == "applied"` 且 `candidate.kind == "workflow_policy"` 时：

- 若 `source_review_decision not in {"support", "revise"}`，抛 `ValueError("workflow_policy candidates require support or revise review decision before applied")`。
- `_apply_workflow_policy_candidate()` 替换已有 rule 时保持原位置；新增 rule 才 append。

- [x] **步骤 5：运行 GREEN**

运行：`.venv/bin/python -m pytest tests/unit/test_llm_asset_candidate_generator.py tests/unit/test_candidate_governance.py tests/integration/test_assess_improve_commands.py -q`

预期：通过。

### 任务 3：文档与演进记录

**文件：**
- 修改：`README.md`
- 修改：`docs/engineering/init-workflow.md`
- 修改：`docs/engineering/sensor-and-gate-rules.md`
- 修改：`docs/evolution-log.md`

- [x] **步骤 1：README 补 lifecycle 说明**

说明 recommendation / improve / review / generate 都保持 review-only，只有 `review-candidate --decision applied` 会按结构化 patch 修改 routing policy。

- [x] **步骤 2：engineering docs 补边界**

在 init workflow 和 sensor/gate rules 中说明 workflow policy candidate applied 的约束：support/revise、精确 target、结构化 patch、benchmark 一致性。

- [x] **步骤 3：evolution-log 新增本轮记录**

记录 gap、用户故事、决策、失败模式、sub agent 使用、验收和下一轮候选 gap。

### 任务 4：验证、提交、推送

- [x] **步骤 1：目标回归**

运行：`.venv/bin/python -m pytest tests/unit/test_llm_asset_candidate_generator.py tests/unit/test_candidate_governance.py tests/integration/test_assess_improve_commands.py tests/integration/test_benchmark_command.py -q`

预期：通过。

- [x] **步骤 2：快速回归**

运行：`scripts/test-fast.sh`

预期：通过。

- [x] **步骤 3：提交**

```bash
git add .
git commit -m "打通 Workflow 推荐到策略治理闭环"
```

- [x] **步骤 4：push 前全量回归**

运行：`scripts/test-full.sh`

预期：通过。

- [ ] **步骤 5：推送**

运行：`git push --no-verify origin main`

预期：手动 full regression 通过后推送成功。
