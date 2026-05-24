from __future__ import annotations

from pathlib import Path


def detect_ci_docker(repo_root: Path) -> dict:
    workflows_dir = repo_root / ".github" / "workflows"
    workflows: list[str] = []
    if workflows_dir.exists():
        workflows = sorted(p.relative_to(repo_root).as_posix() for p in workflows_dir.glob("*.yml"))
        workflows += sorted(p.relative_to(repo_root).as_posix() for p in workflows_dir.glob("*.yaml"))
    compose = sorted(p.relative_to(repo_root).as_posix() for p in repo_root.glob("docker-compose*.yml"))
    compose += sorted(p.relative_to(repo_root).as_posix() for p in repo_root.glob("docker-compose*.yaml"))
    dockerfiles = sorted(p.relative_to(repo_root).as_posix() for p in repo_root.rglob("Dockerfile"))
    return {"githubActions": sorted(workflows), "dockerComposeFiles": sorted(compose), "dockerfiles": dockerfiles}
