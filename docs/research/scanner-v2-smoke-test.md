# Scanner v2 Smoke Test Results

> Date: 2026-05-25
> Scanner: harness-builder v2 (LLM + deterministic pipeline)

## Environment

- Python: 3.9.6 (macOS arm64)
- LLM: DeepSeek v4 Flash (OpenAI-compatible API)
- API Key: loaded from `.env` in harness-builder repo root
- CWD requirement: must run from harness-builder repo root so `.env` is found

## Test 1: RuoYi-Vue (Java/Spring Boot + Vue.js)

**Command:**
```bash
cd /path/to/harness-builder
python3 -m harness_builder.scanner.cli \
  --repo /tmp/openclaw/harness-poc-targets/RuoYi-Vue \
  --out /tmp/openclaw/smoke-ruoyi
```

**Result:** ✅ Success

**Output verification:**
- `project-inventory.json`: 99KB, contains all v2 fields
- `command-catalog.yaml`: generated
- `scanner-report.md`: rendered with all sections
- `fileTree`: 367 files, 155 directories
- `analysis.enabled`: true (LLM analysis active)
- `evidence`: java detected=true, node detected=true, dotnet detected=false
- `validation.summary`: "All LLM claims confirmed by scripts"
- `validation.points`: 0 (no mismatches)
- `moduleAnalysis`: 12 modules identified
- `anomalies`: 9 anomalies found (missing tests, large components, Windows-only scripts, etc.)
- `architecturePattern`: Monolithic Spring Boot with modular packaging + separate Vue.js frontend

**LLM Stack Analysis:** Java 8+ / Spring Boot 2.x / Maven / MySQL / MyBatis / Vue 2.x / Element UI

**Notable findings:**
- LLM correctly identified the full tech stack (Java + Vue.js)
- Detected lack of unit tests as an anomaly
- Identified monolithic component in `ruoyi-ui/src/views/index.vue` (69KB)
- Noted only Windows `.bat` scripts, no `.sh` equivalents

## Test 2: eShopOnWeb (.NET)

**Command:**
```bash
cd /path/to/harness-builder
python3 -m harness_builder.scanner.cli \
  --repo /tmp/openclaw/harness-poc-targets/eShopOnWeb \
  --out /tmp/openclaw/smoke-eshop
```

**Result:** ✅ Success

**Output verification:**
- `project-inventory.json`: contains all v2 fields
- `fileTree`: 444 files, 132 directories
- `analysis.enabled`: true
- `evidence`: script detectors ran (filesystem, ci, codeStructure, genericFallback)
- `validation.summary`: "All LLM claims confirmed by scripts"
- `moduleAnalysis`: 6 modules identified
- `anomalies`: 5 anomalies found
- `architecturePattern`: Clean Architecture / Onion Architecture (DDD-based) with CQRS + MediatR

**LLM Stack Analysis:** .NET / ASP.NET Core / Entity Framework Core / Blazor / Razor Pages

## Test 3: No-LLM Mode (local fixtures)

**Command:**
```bash
python3 -m harness_builder.scanner.cli \
  --repo tests/fixtures/minimal-java-maven \
  --out /tmp/openclaw/smoke-no-llm \
  --no-llm
```

**Result:** ✅ Covered by existing tests (test_cli_no_llm_flag)

## Bug Found and Fixed During Smoke Test

**Issue:** `llm_scanner.py:merge_rounds()` crashed with `AttributeError: 'str' object has no attribute 'get'` when LLM returned moduleAnalysis entries as strings instead of dicts.

**Fix:** Added defensive `_module_key()` helper that handles both dict and string entries in moduleAnalysis.

**Location:** `harness_builder/scanner/detectors/llm_scanner.py:110`

## Report Enhancement Summary

The scanner report now renders:

1. **File tree summary** — file/directory counts
2. **Tech stack** — LLM inference (primary + secondary) with confidence levels
3. **Script evidence** — deterministic facts from script detectors, clearly labeled
4. **Module responsibilities** — LLM-inferred module roles
5. **Architecture pattern** — LLM-inferred architecture
6. **Command catalog** — detailed commands with confidence and working directory
7. **Anomalies** — LLM-detected issues
8. **Validation** — LLM vs script cross-check results
9. **Calibration notes** — human review guidance

Key design decisions:
- Report never crashes on missing fields (all v2 sections are optional)
- Clear distinction between "确定性事实" (script evidence) and "LLM 推断" (inference)
- Works in both LLM-enabled and no-LLM modes

## Test Suite Status

- **Before:** 135 tests passing
- **After Task 7:** 148 tests passing (13 new report tests + bug fix did not require new test)

## Files Changed

| File | Change |
|------|--------|
| `harness_builder/scanner/report.py` | Enhanced to render v2 fields |
| `tests/scanner/test_report.py` | 13 new tests for v2 report features |
| `harness_builder/scanner/detectors/llm_scanner.py` | Bug fix: defensive moduleAnalysis parsing |
| `docs/research/scanner-v2-smoke-test.md` | This file |
