from __future__ import annotations


def is_safe_ai_relative_path(path: str) -> bool:
    parts = path.split("/")
    return len(parts) > 1 and parts[0] == ".ai" and all(part not in {"", ".", ".."} for part in parts[1:])
