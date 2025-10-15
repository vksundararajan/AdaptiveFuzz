from typing import Any, Dict, List, TypedDict
from typing_extensions import Annotated


def append_to_list(left: List[Any], right: List[Any]) -> List[Any]:
    if not isinstance(left, list) or not isinstance(right, list):
        raise TypeError("Both operands must be lists")
    return left + right


class Strategy(TypedDict):
    display_text: str  # The human-readable option shown to the user.
    task_command: str  # The machine-readable task to execute if chosen.


class ToolCall(TypedDict):
    task: str  # The high-level task that prompted this tool call.
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: str


class AdaptiveState(TypedDict):
    target_ip: str
    to_loop: bool
    in_appropriate: bool
    initial_query: str
    tasks: List[str]
    findings: List[str]
    strategy_options: List[Strategy]
    iteration_count: int
    completed_tasks: Annotated[List[ToolCall], append_to_list]


def initialize_adaptive_state() -> AdaptiveState:
    return AdaptiveState(
        target_ip="",
        initial_query="",
        tasks=[],
        completed_tasks=[],
        findings=[],
        strategy_options=[],
        iteration_count=0,
        to_loop=False,
        in_appropriate=False,
    )
