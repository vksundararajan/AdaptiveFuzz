from typing import Any, Dict, Sequence, List

from paths import PROMPTS_CONFIG_PATH
from to_help import load_yaml_file


PROMPTS_CONFIG: Dict[str, Any] = load_yaml_file(PROMPTS_CONFIG_PATH)


def ai_prompt(agent: str) -> str:
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
            print("\n⚠️  Aborted by user.")
            raise SystemExit(1)

        if value:
            return value


def h_response(
    findings: List[Dict[str, Any]],
    completed_tasks: List[Dict[str, str]],
    pending_tasks: List[Dict[str, str]],
    strategies: List[str],
) -> str:
    """Formats the current state of the fuzzer into a human-readable string."""
    response_parts = ["\nFuzzer Status Update", "--------------------"]

    if strategies:
        response_parts.append("\nStrategies:")
        for strategy in strategies:
            response_parts.append(f"- {strategy}")

    if findings:
        response_parts.append("\nFindings:")
        for finding in findings:
            if "summary" in finding:
                response_parts.append(f"- Summary: {finding['summary']}")
            if "details" in finding and finding["details"]:
                response_parts.append("  Details:")
                for detail_item in finding["details"]:
                    for detail_value in detail_item.values():
                        response_parts.append(f"  - {detail_value}")

    if completed_tasks:
        response_parts.append("\nCompleted Tasks:")
        for task in completed_tasks:
            task_id = task.get("task_id", "N/A")
            description = task.get("description", "No description")
            status = task.get("status", "unknown")
            response_parts.append(f"- ({task_id}) {description} - {status}")

    if pending_tasks:
        response_parts.append("\nPending Tasks:")
        for task in pending_tasks:
            task_id = task.get("task_id", "N/A")
            description = task.get("description", "No description")
            status = task.get("status", "pending")
            response_parts.append(f"- ({task_id}) {description} - {status}")
    
    response_parts.append("\n🔀  What do we do next?")

    return "\n".join(response_parts)