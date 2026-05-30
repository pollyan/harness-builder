from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def _strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _find_child_text(root: ET.Element, name: str) -> list[str]:
    values: list[str] = []
    for child in root.iter():
        if _strip_namespace(child.tag) == name and child.text:
            values.append(child.text.strip())
    return values


def _read_modules(pom_path: Path) -> list[str]:
    try:
        root = ET.parse(pom_path).getroot()
    except ET.ParseError:
        return []
    return _find_child_text(root, "module")


def detect_java_maven(repo_root: Path) -> dict:
    pom_files = sorted(
        (p.relative_to(repo_root).as_posix() for p in repo_root.rglob("pom.xml")),
        key=lambda s: (s.count("/"), s),
    )
    root_pom = repo_root / "pom.xml"
    modules = _read_modules(root_pom) if root_pom.exists() else []
    spring_configs = sorted(
        p.relative_to(repo_root).as_posix()
        for pattern in ("application.yml", "application.yaml", "application.properties")
        for p in repo_root.rglob(pattern)
    )
    sql_assets = sorted(p.relative_to(repo_root).as_posix() for p in repo_root.rglob("*.sql"))

    return {
        "detected": bool(pom_files),
        "buildFiles": pom_files,
        "mavenModules": [{"name": m, "path": m} for m in modules],
        "springConfigFiles": spring_configs,
        "sqlAssets": sql_assets,
    }
