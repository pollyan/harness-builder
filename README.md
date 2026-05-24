# Harness Builder

Harness Builder is a proof-of-concept project for generating project-level AI Coding Harness assets from existing enterprise codebases.

The current POC focuses on a minimal, verifiable loop:

```text
Target repositories → Scanner → Harness assets → Task mapping → Sensor verification
```

## POC Scope

The first POC validates two common enterprise technology stacks:

- Java / Spring Boot / Maven / Vue: RuoYi-Vue
- .NET / ASP.NET Core / EF Core: eShopOnWeb

Apache Fineract is tracked as a second-stage complex business-system candidate.

## Development Method

This repository follows a spec-first development process:

1. Design before implementation
2. Implementation plan before coding
3. Small TDD-oriented tasks
4. Verification against real target repositories
5. Review before expanding scope

## Status

Early POC planning. No production-ready implementation yet.
