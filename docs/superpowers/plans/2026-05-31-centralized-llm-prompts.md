# Centralized LLM Prompts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move all machine-consumed LLM prompt contracts into `src/harness_builder_agent/prompts/` with shared loading and regression tests.

**Architecture:** Add a small prompt asset loader used by all LLM tool modules. Prompt Markdown files provide `## System Message` and `## User Message`; Python modules append structured JSON payloads and keep schema validation unchanged.

**Tech Stack:** Python, importlib.resources, pytest, Markdown prompt assets.

---

### Task 1: Prompt Asset Contract Tests

**Files:**
- Create: `tests/unit/test_prompt_assets.py`

- [ ] **Step 1: Write failing tests**

Add tests that assert known prompt assets are loadable and that `tools/llm_*.py` modules do not contain inline long prompt contracts such as `Return one JSON object only`.

- [ ] **Step 2: Run RED**

Run:

```bash
/Users/anhui/Documents/myProgram/harness-builder/.venv/bin/python -m pytest tests/unit/test_prompt_assets.py -q
```

Expected: fail because most prompt assets do not exist yet and inline contracts still exist.

### Task 2: Shared Prompt Loader

**Files:**
- Create: `src/harness_builder_agent/prompts/loader.py`
- Modify: `src/harness_builder_agent/tools/llm_scan_analyzer.py`

- [ ] **Step 1: Implement loader**

Create `load_prompt_sections(filename: str) -> tuple[str, str]` that reads `prompts/<filename>` from package resources and requires `## System Message` plus `## User Message`.

- [ ] **Step 2: Migrate scan analyzer to loader**

Replace its private loader with the shared helper while keeping behavior unchanged.

### Task 3: Move Inline Prompts

**Files:**
- Create: `src/harness_builder_agent/prompts/llm_maturity_review_v2.md`
- Create: `src/harness_builder_agent/prompts/llm_asset_candidate_v2.md`
- Create: `src/harness_builder_agent/prompts/llm_experience_summary_v1.md`
- Create: `src/harness_builder_agent/prompts/llm_workflow_router_v1.md`
- Modify: corresponding `src/harness_builder_agent/tools/llm_*.py`

- [ ] **Step 1: Move text with minimal wording changes**

Keep prompt text semantically equivalent to the current working code.

- [ ] **Step 2: Keep JSON payload assembly in Python**

Each builder appends `...\n\n<Input label>:\n{json.dumps(payload, ensure_ascii=False)}`.

### Task 4: Docs And Verification

**Files:**
- Modify: `docs/engineering/llm-contracts.md`
- Modify: `docs/evolution-log.md`

- [ ] **Step 1: Make prompt centralization a current rule**

Replace future wording with the rule that all machine-consumed LLM prompts live under `src/harness_builder_agent/prompts/`.

- [ ] **Step 2: Run focused and fast verification**

Run:

```bash
/Users/anhui/Documents/myProgram/harness-builder/.venv/bin/python -m pytest tests/unit/test_prompt_assets.py tests/unit/test_llm_maturity_reviewer.py tests/unit/test_llm_asset_candidate_generator.py tests/unit/test_llm_experience_summarizer.py tests/unit/test_llm_workflow_router.py tests/unit/test_llm_scan_analyzer.py -q
PATH=/Users/anhui/Documents/myProgram/harness-builder/.venv/bin:$PATH scripts/test-fast.sh
```
