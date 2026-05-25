from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

LLM_HINT_POLICY = "LLM 只能生成 hints 和人工校准建议，不得覆盖确定性事实源。"


def _build_prompt(inventory: dict[str, Any]) -> str:
    """Build a concise prompt from the deterministic scan results for LLM analysis."""
    repo_name = inventory.get("repo", {}).get("name", "unknown")
    structure = inventory.get("structure", {})
    stack_ext = inventory.get("stackExtensions", {})
    ci = inventory.get("ci", {})
    code_struct = inventory.get("codeStructure", {})

    detected_stacks = [k for k, v in stack_ext.items() if isinstance(v, dict) and v.get("detected")]
    unknown = stack_ext.get("genericFallback", {})

    prompt = f"""You are a project structure analyst. Analyze the following scan results and provide insights.

Rules:
- You may ONLY suggest hints and calibration points. Do NOT state anything as confirmed fact.
- Every hint must include a confidence level: high / medium / low.
- Every hint must list the evidence from the scan data that supports it.
- Do NOT invent build commands, test commands, or technologies not evidenced in the data.
- Do NOT override the deterministic scan results.

Repository: {repo_name}

Detected tech stacks: {json.dumps(detected_stacks) if detected_stacks else 'None'}

Top-level directories: {json.dumps(structure.get('topLevelDirectories', []))}

Key files: {json.dumps(structure.get('keyFiles', [])[:20])}

File counts by extension (top 10): {json.dumps(dict(list(structure.get('fileCounts', {}).get('byExtension', {}).items())[:10]))}

CI assets: {json.dumps(ci)}

Code structure summary:
- Controllers: {len(code_struct.get('controllers', []))} files
- Services: {len(code_struct.get('services', []))} files
- Entities/Models: {len(code_struct.get('entitiesOrModels', []))} files
- Test files: {len(code_struct.get('tests', []))} files
- Frontend components: {len(code_struct.get('frontendComponents', []))} files

Generic fallback (if no stack detected):
{json.dumps(unknown, ensure_ascii=False) if unknown else 'N/A'}

Please respond in the following JSON format only:
{{
  "stackGuess": {{
    "primary": "<guessed primary tech stack or null>",
    "secondary": ["<guessed secondary tech>"],
    "confidence": "<high|medium|low>",
    "evidence": ["<why>"]
  }},
  "moduleResponsibilities": [
    {{
      "module": "<directory or module name>",
      "guessedRole": "<what this module likely does>",
      "confidence": "<high|medium|low>",
      "evidence": ["<why>"]
    }}
  ],
  "calibrationPoints": [
    {{
      "message": "<what the human should verify>",
      "confidence": "<high|medium|low>",
      "evidence": ["<why>"]
    }}
  ],
  "anomalies": [
    {{
      "message": "<unusual pattern detected>",
      "confidence": "<high|medium|low>",
      "evidence": ["<why>"]
    }}
  ]
}}
"""
    return prompt


def _parse_llm_response(raw: str) -> dict[str, Any]:
    """Parse the LLM JSON response, extracting from markdown code blocks if needed."""
    text = raw.strip()
    # Extract JSON from markdown code block if present
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON: %s", text[:200])
        return {
            "stackGuess": None,
            "moduleResponsibilities": [],
            "calibrationPoints": [],
            "anomalies": [],
            "_parseError": True,
            "_rawPreview": text[:500],
        }


def _format_hints(parsed: dict[str, Any], manual_points: list[str]) -> dict[str, Any]:
    """Format parsed LLM response and manual points into the standard hints structure."""
    hints: list[dict[str, Any]] = []

    # Stack guess
    sg = parsed.get("stackGuess")
    if sg and sg.get("primary"):
        hints.append({
            "type": "stack-guess",
            "message": f"可能的主技术栈：{sg['primary']}" + (f"，辅助：{', '.join(sg.get('secondary', []))}" if sg.get("secondary") else ""),
            "confidence": sg.get("confidence", "low"),
            "evidence": sg.get("evidence", []),
        })

    # Module responsibilities
    for mod in parsed.get("moduleResponsibilities", []):
        hints.append({
            "type": "module-responsibility",
            "message": f"{mod.get('module', '?')}: {mod.get('guessedRole', '')}",
            "confidence": mod.get("confidence", "low"),
            "evidence": mod.get("evidence", []),
        })

    # Anomalies
    for anom in parsed.get("anomalies", []):
        hints.append({
            "type": "anomaly",
            "message": anom.get("message", ""),
            "confidence": anom.get("confidence", "low"),
            "evidence": anom.get("evidence", []),
        })

    # Calibration from LLM
    for cal in parsed.get("calibrationPoints", []):
        hints.append({
            "type": "calibration",
            "message": cal.get("message", ""),
            "confidence": cal.get("confidence", "low"),
            "evidence": cal.get("evidence", []),
        })

    # Manual calibration points (from deterministic scan)
    for point in manual_points:
        hints.append({
            "type": "manual-calibration",
            "message": point,
            "confidence": "low",
            "evidence": [],
        })

    return {
        "enabled": True,
        "policy": LLM_HINT_POLICY,
        "hints": hints,
    }


def build_llm_hints(
    inventory: dict[str, Any],
    manual_points: list[str],
    llm_caller: Optional[Callable[[str], str]] = None,
) -> dict[str, Any]:
    """
    Build LLM hints based on the deterministic scan inventory.

    Args:
        inventory: The deterministic scan inventory dict.
        manual_points: Manual calibration points from deterministic scan.
        llm_caller: A callable that takes a prompt string and returns the LLM response.
                    If None, LLM hints are disabled and only manual points are returned.

    Returns:
        A dict with enabled, policy, and hints list.
    """
    if llm_caller is None:
        # No LLM caller provided — return manual-only hints
        return {
            "enabled": False,
            "policy": LLM_HINT_POLICY,
            "hints": [
                {
                    "type": "manual-calibration",
                    "message": point,
                    "confidence": "low",
                    "evidence": [],
                }
                for point in manual_points
            ],
        }

    prompt = _build_prompt(inventory)

    try:
        raw_response = llm_caller(prompt)
        parsed = _parse_llm_response(raw_response)
        return _format_hints(parsed, manual_points)
    except Exception:
        logger.exception("LLM hint generation failed")
        # Graceful degradation — return manual points only
        return {
            "enabled": False,
            "policy": LLM_HINT_POLICY,
            "hints": [
                {
                    "type": "manual-calibration",
                    "message": point,
                    "confidence": "low",
                    "evidence": [],
                }
                for point in manual_points
            ],
            "_llmError": True,
        }


# Backward compatibility alias
build_llm_hint_placeholder = lambda manual_points: build_llm_hints({}, manual_points, llm_caller=None)
