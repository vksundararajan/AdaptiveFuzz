from typing import Any, Dict, Sequence

from paths import PROMPTS_CONFIG_PATH
from utils import load_yaml_file


PROMPTS_CONFIG: Dict[str, Any] = load_yaml_file(PROMPTS_CONFIG_PATH)


def make_prompt(agent: str) -> str:
    """Construct a system prompt string for the given agent key defined in prompts.yaml."""

    agent_entry = PROMPTS_CONFIG["adaptive_system"]["agents"][agent]
    raw_config: Dict[str, Any] = dict(agent_entry.get("prompt_config", {}))
    parts = [f"Agent: {agent}"]

    section_order = (
        ("role", "Role"),
        ("context", "Context"),
        ("instruction", "Instruction"),
        ("rules", "Rules"),
        ("examples", "Examples"),
        ("output_format", "Output Format"),
        ("output_constraints", "Output Constraints"),
        ("style_or_tone", "Style / Tone"),
        ("goal", "Goal"),
        ("notes", "Notes"),
    )

    for key, label in section_order:
        if key not in raw_config:
            continue
        value = raw_config.pop(key)
        if value is None:
            continue
        formatted = value.strip() if isinstance(value, str) else str(value)
        if formatted:
            parts.append(f"{label}:\n{formatted}")

    for extra_key in list(raw_config.keys()):
        value = raw_config.pop(extra_key)
        if value is None:
            continue
        formatted = value.strip() if isinstance(value, str) else str(value)
        if formatted:
            label = extra_key.replace("_", " ").title()
            parts.append(f"{label}:\n{formatted}")

    return "\n\n".join(parts)


def c_prompt(
    prompt_text: str,
    empty_warning: str = "Ask Anything!",
) -> str:
    """Prompt the user until a non-empty, stripped response is provided."""

    while True:
        try:
            value = input(prompt_text).strip()
        except KeyboardInterrupt: 
            print("\n⚠️ Aborted by user.")
            raise SystemExit(1)

        if value:
            return value

    print(f"{empty_warning}\n")