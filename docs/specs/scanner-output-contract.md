# Scanner Output Contract

## Required Files

```text
.harness/
  project-inventory.json
  command-catalog.yaml
  scanner-report.md
```

## project-inventory.json

Captures deterministic repository inventory:

- repository metadata
- technology stack signals
- directory structure
- build files
- config files
- documentation assets
- test assets
- CI and Docker assets
- file counts

## command-catalog.yaml

Captures command candidates:

- build
- test
- run
- frontend
- docker

Each command should include:

- name
- command
- working directory
- source file
- confidence
- verified flag

## scanner-report.md

Human-readable summary for review and demo.
