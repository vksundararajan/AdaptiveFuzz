from typing import Any, Dict, List, TypedDict
from typing_extensions import Annotated


class AdaptiveState(TypedDict):
    target_ip: str
    to_loop: bool
    in_appropriate: bool
    iteration_count: int
    strategies: List[Any]
    user_query: Annotated[List[Any], lambda left, right: left + right]
    tasks: Annotated[List[Any], lambda left, right: right]
    completed_tasks: Annotated[List[Any], lambda left, right: left + right]
    findings: Annotated[List[Any], lambda left, right: left + right]


def initialize_adaptive_state() -> AdaptiveState:
    return AdaptiveState(
        target_ip="",
        user_query=[],
        iteration_count=0,
        to_loop=False,
        in_appropriate=False,
        tasks=[],
        completed_tasks=[],
        findings=[],
        strategies=[],
    )
