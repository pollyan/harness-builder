# Harness Builder Agent POC

Harness Builder Agent scans a codebase, generates a project-level `.ai/` AI Coding Harness, and runs a small controlled task workflow.

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[test]"
```

For local DeepSeek smoke testing, create a local `.env` file. Do not commit it.

```bash
DEEPSEEK_API_KEY=...
HARNESS_BUILDER_LLM_PROVIDER=deepseek
HARNESS_BUILDER_LLM_BASE_URL=https://api.deepseek.com
HARNESS_BUILDER_LLM_MODEL=deepseek-v4-pro
```

## Commands

```bash
.venv/bin/harness-builder-agent init --repo tests/fixtures/mini-spring-boot
.venv/bin/harness-builder-agent run --repo tests/fixtures/mini-spring-boot "修复登录接口错误提示不一致的问题"
.venv/bin/harness-builder-agent benchmark --repo tests/fixtures/mini-spring-boot --profile java-spring
```

Real repository benchmarks use ignored local clones:

```bash
mkdir -p .benchmarks
git clone --depth 1 https://github.com/yangzongzhuan/RuoYi-Vue.git .benchmarks/RuoYi-Vue
git clone --depth 1 https://github.com/dotnet-architecture/eShopOnWeb.git .benchmarks/eShopOnWeb

.venv/bin/harness-builder-agent init --repo .benchmarks/RuoYi-Vue
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/RuoYi-Vue --profile java-spring
.venv/bin/harness-builder-agent init --repo .benchmarks/eShopOnWeb
.venv/bin/harness-builder-agent benchmark --repo .benchmarks/eShopOnWeb --profile dotnet-aspnet
```

## Validation

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/e2e -q
.venv/bin/python -m pytest tests/e2e/test_real_repositories_e2e.py -q
```

When `.env` contains `DEEPSEEK_API_KEY`, `tests/e2e/test_real_llm_smoke.py` performs a real DeepSeek request. Without a key, that smoke test is skipped so CI can still run fixture validation.
