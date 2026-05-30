from __future__ import annotations

import json
import re
from collections.abc import Callable

from pydantic import ValidationError

from harness_builder_agent.schemas.scan import EvidenceBundle, LLMScanProposal
from harness_builder_agent.tools.deepseek_client import call_deepseek
from harness_builder_agent.tools.llm_config import DeepSeekConfig

SCAN_PROMPT_VERSION = "llm-first-scan-v1"


def analyze_evidence_with_llm(
    evidence: EvidenceBundle,
    caller: Callable[[list[dict[str, str]]], str] | None = None,
    config: DeepSeekConfig | None = None,
) -> LLMScanProposal:
    messages = build_scan_messages(evidence)
    content = caller(messages) if caller else call_deepseek(messages, config=config)
    if not content.strip():
        raise ValueError("DeepSeek scan response is empty")
    return parse_llm_scan_response(content)


def build_scan_messages(evidence: EvidenceBundle) -> list[dict[str, str]]:
    schema_contract = """
Return one JSON object only. Do not include markdown commentary.

Allowed primary_stack values: java-spring, dotnet-aspnet, node, unknown.
Use canonical lowercase stack labels in stacks, such as java, maven, spring-boot,
dotnet, aspnet-core, node, npm, typescript. Do not use display labels like
"Spring Boot" for primary_stack.

Field contract:
- primary_stack: one allowed canonical value.
- stacks: array of canonical lowercase strings.
- modules: array of objects with name, path, kind.
- architecture_signals: array of strings grounded in evidence.
- risk_areas: array of objects with path and reason.
- command_candidates: array of objects with id, command, type, gate, source, confidence.
- command_candidates.type must be one of build, test, lint, typecheck, other.
- command_candidates.gate must be one of hard or soft. gate is quality strictness, not command category.
- command_candidates.confidence must be one of low, medium, high.
- confidence must be one of low, medium, high. Never use numeric confidence.
- configs and ci_files must be arrays of objects.
- needs_human_confirmation must be boolean.
- reasoning_summary must be a short evidence-based string.

Stack decision rules:
- Choose java-spring when evidence contains Spring Boot or Spring Framework signals such as
  spring-boot-starter dependencies, org.springframework imports, @SpringBootApplication,
  @RestController, @Controller, or a DemoController under a Java/Maven/Gradle project.
- Choose dotnet-aspnet when evidence contains ASP.NET Core signals such as Microsoft.NET.Sdk.Web,
  Program.cs minimal API setup, controllers, MapGet/MapPost endpoints, .sln, or .csproj web SDK.
- Choose node when evidence contains package.json plus Node application/runtime signals.
- Choose unknown only when stack evidence is genuinely insufficient or conflicting.

Example JSON shape:
{
  "schema_version": "1.0",
  "primary_stack": "java-spring",
  "stacks": ["java", "maven", "spring-boot"],
  "modules": [{"name": "app", "path": ".", "kind": "backend"}],
  "architecture_signals": ["Spring MVC controller evidence in src/main/java"],
  "risk_areas": [{"path": "pom.xml", "reason": "No explicit CI file was found"}],
  "command_candidates": [
    {
      "id": "unit_test",
      "command": "mvn test",
      "type": "test",
      "gate": "hard",
      "source": "pom.xml",
      "confidence": "high"
    }
  ],
  "configs": [{"path": "pom.xml", "kind": "maven"}],
  "ci_files": [],
  "confidence": "high",
  "needs_human_confirmation": false,
  "reasoning_summary": "Maven and Spring evidence were found in pom.xml and source files."
}
""".strip()
    return [
        {
            "role": "system",
            "content": (
                "You are the scan analyzer for Harness Builder. "
                "You convert repository evidence into a strict machine-readable scan proposal. "
                "If evidence is weak, use unknown/low confidence instead of inventing facts."
            ),
        },
        {
            "role": "user",
            "content": (
                f"{schema_contract}\n\n"
                f"Evidence JSON:\n{evidence.model_dump_json()}"
            ),
        },
    ]


def parse_llm_scan_response(content: str) -> LLMScanProposal:
    raw = _extract_json_text(content)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek scan response must be valid JSON") from exc

    try:
        return LLMScanProposal.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"DeepSeek scan response failed schema validation: {exc}") from exc


def _extract_json_text(content: str) -> str:
    stripped = content.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped
