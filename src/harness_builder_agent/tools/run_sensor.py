from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from harness_builder_agent.schemas.command_catalog import CommandDefinition


def run_sensor(repo: Path, command: CommandDefinition, timeout_seconds: int = 3) -> dict[str, Any]:
    executable = command.command.split()[0]
    started_at = time.time()
    if shutil.which(executable) is None:
        return {
            "id": command.id,
            "command": command.command,
            "status": "skipped",
            "exit_code": None,
            "duration_seconds": 0.0,
            "summary": f"Executable '{executable}' is not available in PATH.",
        }

    try:
        completed = subprocess.run(
            command.command,
            cwd=repo,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "id": command.id,
            "command": command.command,
            "status": "failed",
            "exit_code": None,
            "duration_seconds": round(time.time() - started_at, 3),
            "summary": f"Sensor timed out after {timeout_seconds} seconds.",
            "stdout_tail": (exc.stdout or "")[-2000:],
            "stderr_tail": (exc.stderr or "")[-2000:],
        }

    status = "passed" if completed.returncode == 0 else "failed"
    return {
        "id": command.id,
        "command": command.command,
        "status": status,
        "exit_code": completed.returncode,
        "duration_seconds": round(time.time() - started_at, 3),
        "summary": "Sensor completed." if status == "passed" else "Sensor command failed.",
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }
