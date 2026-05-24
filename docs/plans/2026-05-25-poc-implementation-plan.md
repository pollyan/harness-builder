# Harness Builder POC Implementation Plan

> Status: Draft  
> Date: 2026-05-25  
> Scope: Scanner-first POC implementation  
> Method: Spec-first + small-step TDD

---

## 1. Objective

Build the first Harness Builder POC around a scanner-first loop:

```text
RuoYi-Vue + eShopOnWeb
→ deterministic repository scanner
→ project inventory
→ command catalog
→ scanner report
→ next-stage Harness Generator input
```

This POC should prove that the same scanner framework can extract useful Harness inputs from at least two common enterprise technology stacks.

---

## 2. Target Repositories

| Repository | Technology Stack | POC Role |
|---|---|---|
| `yangzongzhuan/RuoYi-Vue` | Java / Spring Boot / Maven / Vue | Java enterprise admin-system baseline |
| `dotnet-architecture/eShopOnWeb` | .NET / ASP.NET Core / EF Core | Non-Java cross-stack baseline |
| `apache/fineract` | Java / Spring Boot / Gradle / PostgreSQL | Second-stage complex business-system candidate |

First implementation targets only RuoYi-Vue and eShopOnWeb.

---

## 3. First Milestone: Scanner Prototype

### Output Contract

For each target repository, generate:

```text
.harness/
  project-inventory.json
  command-catalog.yaml
  scanner-report.md
```

### Required Scanner Capabilities

1. File-system inventory
2. Technology-stack detection
3. Java / Maven detector
4. Node / Vue detector
5. .NET solution / project detector
6. CI / Docker detector
7. Command catalog generation
8. Human-readable scanner report

---

## 4. Development Sequence

### Task 1 — Repository skeleton

- Create scanner package structure.
- Add minimal CLI entrypoint.
- Add test harness and sample fixture directory.

Verification:

```bash
python -m pytest
python scanner/scan_repo.py --help
```

### Task 2 — File-system inventory

- Scan top-level directories.
- Count files by extension.
- Detect common document/config/build files.

Verification:

- Unit tests against fixture repo.
- JSON output contains expected directories and counts.

### Task 3 — Java / Maven detector

- Detect `pom.xml`.
- Extract Maven modules.
- Detect Spring config files.
- Detect SQL files.

Verification:

- Unit tests with Maven fixture.
- Run against RuoYi-Vue and confirm modules are detected.

### Task 4 — Node / Vue detector

- Detect `package.json`.
- Extract scripts.
- Detect Vue project directories.

Verification:

- Unit tests with package fixture.
- Run against `ruoyi-ui` and confirm scripts are extracted.

### Task 5 — .NET detector

- Detect `.sln`, `.csproj`, `global.json`, `Directory.Packages.props`.
- Extract project list and likely project roles.

Verification:

- Unit tests with .NET fixture.
- Run against eShopOnWeb and confirm project structure is detected.

### Task 6 — Command catalog

- Generate build/test/run/frontend command candidates.
- Record source and confidence for each command.

Verification:

- YAML output validates against expected schema.
- Commands include Maven and dotnet candidates.

### Task 7 — Scanner report

- Render human-readable Markdown report.
- Include project overview, detected stack, modules, command candidates, and manual calibration points.

Verification:

- Snapshot-style test or golden-file comparison.
- Report generated for both target repositories.

### Task 8 — Cross-stack validation

- Run scanner against RuoYi-Vue and eShopOnWeb.
- Compare common output contract and stack-specific differences.

Verification:

- Both repositories generate all three required artifacts.
- Summary identifies what is shared and what is stack-specific.

---

## 5. Out of Scope for First Milestone

- Risk-zone detection
- Restricted paths
- Human escalation policy
- Multi-workflow routing
- Experience / self-improvement
- Maturity model
- Security scan integration
- Full project startup
- Web UI
- Database-backed storage

---

## 6. Done Definition

Scanner prototype is done when:

1. Tests pass.
2. Scanner runs on RuoYi-Vue.
3. Scanner runs on eShopOnWeb.
4. Each run outputs `project-inventory.json`, `command-catalog.yaml`, and `scanner-report.md`.
5. Reports are readable enough to support the next Harness Generator design step.
