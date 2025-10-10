import json
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from typing import Any, Dict, Sequence, List

from paths import PROMPTS_CONFIG_PATH
from to_help import load_yaml_file



PROMPTS_CONFIG: Dict[str, Any] = load_yaml_file(PROMPTS_CONFIG_PATH)


def s_prompt(agent: str) -> str:
    """Construct a system prompt string for the given agent key defined in prompts.yaml."""

    agent_entry = PROMPTS_CONFIG["adaptive_system"]["agents"][agent]
    raw_config: Dict[str, Any] = dict(agent_entry.get("prompt_config", {}))
    parts = [f"Agent: {agent}"]

    section_order = (
        ("role", "Role"),
        ("tools", "Tools"),
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
        if key == "tools" and isinstance(value, dict):
            if not value.get("mcp_access"):
                formatted = "MCP Access: No"
            else:
                tool_list = value.get("available_tools", [])
                if not tool_list:
                    formatted = "MCP Access: Yes\nAvailable Tools: None"
                else:
                    tool_strings = [f"- {tool['name']}: {tool['description']}" for tool in tool_list]
                    formatted = "MCP Access: Yes\nAvailable Tools:\n" + "\n".join(tool_strings)
        else:
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
    executed_commands: List[Dict[str, Any]] = None,
) -> str:
    """Formats the current state of the fuzzer into a human-readable string."""
    response_parts = ["\nFuzzer Status Update", "--------------------"]

    if executed_commands:
        response_parts.append("\nExecuted Commands:")
        for cmd in executed_commands:
            command = cmd.get("command", "N/A")
            output = cmd.get("output", "No output")
            # Truncate long outputs
            if len(output) > 200:
                output = output[:200] + "... (truncated)"
            response_parts.append(f"- Command: {command}")
            response_parts.append(f"  Output: {output}")

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
                # Handle details as either a dict or a list
                if isinstance(finding["details"], dict):
                    for key, value in finding["details"].items():
                        response_parts.append(f"  - {key}: {value}")
                elif isinstance(finding["details"], list):
                    for detail_item in finding["details"]:
                        if isinstance(detail_item, dict):
                            for detail_value in detail_item.values():
                                response_parts.append(f"  - {detail_value}")
                        else:
                            response_parts.append(f"  - {detail_item}")

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


def b_message(*sources):
    """Normalize mixed lists of messages and data into valid LangChain Message objects."""
    messages = []
    for src in sources:
        for m in src or []:
            if isinstance(m, (AIMessage, HumanMessage, SystemMessage, ToolMessage)):
                messages.append(m)
            elif isinstance(m, str):
                messages.append(SystemMessage(content=m))
            else:
                messages.append(SystemMessage(content=json.dumps(m)))
    return messages


def show_state(state: Dict[str, Any]) -> str:
    """Formats and prints the current state of the fuzzer."""

    def format_value(value: Any, indent: int = 0) -> str:
        """Helper to format values recursively."""
        prefix = "  " * indent
        if isinstance(value, dict):
            return "\n" + "\n".join(f"{prefix}- {k}: {format_value(v, indent + 1)}" for k, v in value.items())
        if isinstance(value, list):
            if not value:
                return "[]"
            return "\n" + "\n".join(f"{prefix}- {format_value(item, indent + 1)}" for item in value)
        return str(value)

    output = [
        "--------------------",
        "Fuzzer State Details",
        "--------------------",
    ]

    # Prioritize key fields
    priority_order = [
        "fuzz_id", "target_ip", "user_query", "cycle", "last_update_ts",
        "is_inappropriate", "to_loop", "policy"
    ]

    for key in priority_order:
        if key in state:
            output.append(f"{key.replace('_', ' ').title()}: {state[key]}")

    # Handle complex list fields
    list_fields = {
        "pending_tasks": "Pending Tasks",
        "completed_tasks": "Completed Tasks",
        "executed_commands": "Executed Commands",
        "findings": "Findings",
        "strategies": "Strategies",
    }

    for key, title in list_fields.items():
        if state.get(key):
            output.append(f"\n{title}:")
            for item in state[key]:
                output.append(format_value(item, indent=1))

    # Handle message fields
    message_fields = {
        "conversational_handler_messages": "Conversational Handler Messages",
        "recon_executor_messages": "Recon Executor Messages",
        "result_interpreter_messages": "Result Interpreter Messages",
        "strategy_advisor_messages": "Strategy Advisor Messages",
        "human_in_loop_messages": "Human In Loop Messages",
    }

    output.append("\nMessage Logs:")
    for key, title in message_fields.items():
        if state.get(key):
            count = len(state[key])
            output.append(f"  - {title}: {count} message(s)")

    output.append("--------------------")
    return "\n".join(output)