from typing import Any, Dict, List, Optional, TypedDict
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import Annotated

from to_prompt import s_prompt


class AdaptiveState(TypedDict):
    """State for AdaptiveFuzz reconnaissance."""

    ### Per agent message --- added
    conversational_handler_messages: Annotated[List[AnyMessage], add_messages]
    recon_executor_messages: Annotated[List[AnyMessage], add_messages]
    result_interpreter_messages: Annotated[List[AnyMessage], add_messages]
    strategy_advisor_messages: Annotated[List[AnyMessage], add_messages]
    human_in_loop_messages: Annotated[List[AnyMessage], add_messages]

    ### AdaptiveFuzz State Keys --- added
    fuzz_id: str
    target_ip: str
    user_query: str
    to_loop: bool
    is_inappropriate: bool
    pending_tasks: List[Dict[str, Any]]
    completed_tasks: List[Dict[str, Any]]
    executed_commands: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    policy: Optional[Dict[str, Any]]
    strategies: List[str]
    cycle: int
    last_update_ts: Optional[str]


def initialize_adaptive_state(
    fuzz_id: str,
    target_ip: str,
    user_query: str,
    conversational_handler: str,
    recon_executor: str,
    result_interpreter: str,
    strategy_advisor: str,
    to_loop: bool = True,
    is_inappropriate: bool = False,
) -> AdaptiveState:
    """Initialize a compact reconnaissance-oriented AdaptiveState."""

    ch_msgs: List[AnyMessage] = [SystemMessage(s_prompt(conversational_handler))]
    re_msgs: List[AnyMessage] = [SystemMessage(s_prompt(recon_executor))]
    ri_msgs: List[AnyMessage] = [SystemMessage(s_prompt(result_interpreter))]
    sa_msgs: List[AnyMessage] = [SystemMessage(s_prompt(strategy_advisor))]
    hi_msgs: List[AnyMessage] = [HumanMessage(user_query)]

    return AdaptiveState(
        conversational_handler_messages=ch_msgs,
        recon_executor_messages=re_msgs,
        result_interpreter_messages=ri_msgs,
        strategy_advisor_messages=sa_msgs,
        human_in_loop_messages=hi_msgs,
        fuzz_id=fuzz_id,
        target_ip=target_ip,
        user_query=user_query,
        pending_tasks=[],
        completed_tasks=[],
        executed_commands=[],
        findings=[],
        policy=None,
        strategies=[],
        cycle=0,
        last_update_ts=None,
        to_loop=to_loop,
        is_inappropriate=is_inappropriate,
    )
