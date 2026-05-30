from __future__ import annotations

from pathlib import Path

from harness_builder_agent.schemas.command_catalog import CommandDefinition
from harness_builder_agent.tools.run_sensor import run_sensor


def test_run_sensor_uses_configured_timeout(monkeypatch):
    captured = {}

    def fake_run(*_args, **kwargs):
        captured["timeout"] = kwargs["timeout"]

        class Completed:
            returncode = 0
            stdout = "ok"
            stderr = ""

        return Completed()

    monkeypatch.setenv("HARNESS_BUILDER_SENSOR_TIMEOUT_SECONDS", "45")
    monkeypatch.setattr("harness_builder_agent.tools.run_sensor.shutil.which", lambda _name: "/bin/echo")
    monkeypatch.setattr("harness_builder_agent.tools.run_sensor.subprocess.run", fake_run)

    result = run_sensor(
        Path("/tmp/repo"),
        CommandDefinition(id="unit_test", command="mvn test", type="test", gate="hard", source="pom.xml"),
    )

    assert result["status"] == "passed"
    assert captured["timeout"] == 45

