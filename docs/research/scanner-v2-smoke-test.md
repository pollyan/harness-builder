# Scanner v2 Smoke Test Results

> Date: 2026-05-25  
> Scanner: harness-builder v2（LLM + deterministic evidence pipeline）

## Environment

- Python: 3.9.6（macOS arm64）
- LLM: DeepSeek v4 Flash（OpenAI-compatible API）
- API Key: loaded from `.env` in harness-builder repo root（key not committed）
- Command must run from harness-builder repo root so `.env` can be found.

## Test 1: RuoYi-Vue（Java/Spring Boot + Vue.js）

**Command:**

```bash
python3 -m harness_builder.scanner.cli \
  --repo /tmp/openclaw/harness-poc-targets/RuoYi-Vue \
  --out /tmp/openclaw/smoke-ruoyi
```

**Result:** ✅ Success

**Output verification:**

- `project-inventory.json`: generated
- `command-catalog.yaml`: generated
- `scanner-report.md`: generated
- `analysis.enabled`: `true`
- `evidence.java.detected`: `true`
- `evidence.node.detected`: `true`
- `validation.summary`: `All LLM claims confirmed by scripts`
- `validation.points`: `0`
- command counts:
  - build: 6
  - test: 1
  - run: 2
  - frontend: 1
  - docker: 0

**Notable result:** Scanner correctly combined LLM inference with deterministic evidence. Java/Maven and Vue/npm were both confirmed by script detectors.

## Test 2: eShopOnWeb（.NET / ASP.NET Core）

**Command:**

```bash
python3 -m harness_builder.scanner.cli \
  --repo /tmp/openclaw/harness-poc-targets/eShopOnWeb \
  --out /tmp/openclaw/smoke-eshop
```

**Result:** ✅ Success

**Output verification:**

- `project-inventory.json`: generated
- `command-catalog.yaml`: generated
- `scanner-report.md`: generated
- `analysis.enabled`: `true`
- `evidence.dotnet.detected`: `true`
- `validation.summary`: `All LLM claims confirmed by scripts`
- `validation.points`: `0`
- command counts:
  - build: 10
  - test: 5
  - run: 0
  - frontend: 0
  - docker: 2

**Notable result:** Scanner handled DeepSeek's grouped `commandCandidates` shape (`build.commands`, `test.commands`, etc.) and produced a non-empty command catalog.

## Test 3: No-LLM Mode（local fixture）

**Command:**

```bash
python3 -m harness_builder.scanner.cli \
  --repo tests/fixtures/minimal-java-maven \
  --out /tmp/openclaw/smoke-no-llm \
  --no-llm
```

**Result:** ✅ Covered by CLI tests

- `analysis.enabled`: `false`
- deterministic evidence still available
- evidence-based command fallback remains available

## Bugs Found and Fixed During Smoke Testing

### 1. `merge_rounds()` crashed on non-dict module entries

**Symptom:** Real LLM returned `moduleAnalysis` entries as strings, causing `AttributeError: 'str' object has no attribute 'get'`.

**Fix:** Added defensive module key handling for dict and non-dict module entries.

### 2. Nested `stackAnalysis` was not inspected

**Symptom:** Real LLM returned structures like:

```json
{
  "stackAnalysis": {
    "backend": {"language": "Java", "buildTool": "Maven"},
    "frontend": {"framework": "Vue.js", "buildTool": "npm"}
  }
}
```

Earlier code only looked at `primary.name` / `secondary[].name`, so Java/Node/.NET detectors were skipped.

**Fix:** Flatten nested `stackAnalysis` text before keyword matching.

### 3. Keyword false positives in validation

**Symptom:** `JavaScript` in a .NET repo was treated as `Java`, causing false validation mismatches.

**Fix:** Keyword matching now uses word-boundary / special-token matching instead of raw substring matching.

### 4. Real LLM command candidates had multiple shapes

Observed shapes:

- list of command dicts
- grouped dict: `build.commands[]`, `test.commands[]`, `other.commands[]`
- malformed / non-dict entries

**Fix:** Normalize list and grouped dict command candidates; skip malformed entries; fall back to deterministic evidence commands when no valid LLM commands can be parsed.

## Report Enhancement Summary

The scanner report now renders:

1. File tree summary
2. Tech stack analysis（LLM inference）
3. Script evidence（deterministic facts）
4. Module responsibilities（LLM inference）
5. Architecture pattern（LLM inference）
6. Command catalog summary and details
7. Anomalies（LLM inference）
8. Validation results（LLM vs script evidence）
9. Human calibration notes

Design rules:

- Report does not crash on missing fields.
- LLM inference and deterministic facts are explicitly separated.
- Both LLM-enabled and `--no-llm` modes are supported.

## Final Test Suite Status

- `python3 -m pytest -q`
- Result: `156 passed`

## Files Changed in Task 7 / Smoke Hardening

| File | Change |
|---|---|
| `harness_builder/scanner/report.py` | Render v2 inventory fields |
| `tests/scanner/test_report.py` | Add v2 report coverage |
| `harness_builder/scanner/detectors/llm_scanner.py` | Harden merge against non-dict module entries |
| `harness_builder/scanner/detectors/evidence_extractor.py` | Flatten nested stack analysis; reduce keyword false positives |
| `harness_builder/scanner/core.py` | Normalize real LLM command candidate shapes; infer categories; fallback safely |
| `tests/scanner/test_core.py` | Add real-shape regression tests |
| `tests/scanner/test_evidence_extractor.py` | Add nested stack / false-positive regression tests |
| `tests/scanner/test_llm_scanner.py` | Add non-dict module merge regression test |
| `docs/research/scanner-v2-smoke-test.md` | Record smoke results |
