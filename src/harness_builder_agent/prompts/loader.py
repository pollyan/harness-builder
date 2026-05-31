from __future__ import annotations

from importlib import resources

SYSTEM_MARKER = "## System Message"
USER_MARKER = "## User Message"


def load_prompt_sections(filename: str) -> tuple[str, str]:
    prompt = (
        resources.files("harness_builder_agent")
        .joinpath("prompts", filename)
        .read_text(encoding="utf-8")
        .strip()
    )
    if SYSTEM_MARKER not in prompt or USER_MARKER not in prompt:
        raise ValueError(f"Prompt asset {filename} must contain System Message and User Message sections")
    system_text, user_text = prompt.split(USER_MARKER, 1)
    system_text = system_text.replace(SYSTEM_MARKER, "", 1).strip()
    user_text = user_text.strip()
    if not system_text or not user_text:
        raise ValueError(f"Prompt asset {filename} must contain non-empty System Message and User Message sections")
    return system_text, user_text
