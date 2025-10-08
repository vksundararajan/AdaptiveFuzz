from typing import Any, Dict, List, Optional, TypedDict
from langchain_core.messages import SystemMessage
from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import Annotated
from to_prompt import make_prompt


class AdaptiveState(TypedDict):
    """State for AdaptiveFuzz reconnaissance."""

    ### Per agent message --- added
    conversational_handler_messages: Annotated[List[AnyMessage], add_messages]
    recon_executor_messages: Annotated[List[AnyMessage], add_messages]
    result_interpreter_messages: Annotated[List[AnyMessage], add_messages]
    strategy_advisor_messages: Annotated[List[AnyMessage], add_messages]
    human_in_loop_messages: Annotated[List[AnyMessage], add_messages]

    ### orchestration --- added
    session_id: str
    target: Dict[str, Any] 
    current_agent: str  # e.g. "conversational_handler" | "recon_executor" | ...
    pending_tasks: List[Dict[str, Any]]  # {"id","action","args"}
    executed_commands: List[Dict[str, Any]]  # {"id","tool","command","stdout","stderr","status","ts"}
    findings: List[Dict[str, Any]]  # {"id","type","summary","evidence_ids","confidence"}
    policy: Optional[Dict[str, Any]]  # minimal safety limits, rate limits
    cycle: int  # increments per loop
    last_update_ts: Optional[str]


def initialize_adaptive_state(
    session_id: str,
    conversational_handler_prompt: Dict[str, Any],
    recon_executor_prompt: Dict[str, Any],
    result_interpreter_prompt: Dict[str, Any],
    strategy_advisor_prompt: Dict[str, Any],
    human_in_loop_prompt: Optional[Dict[str, Any]] = None,
    target: Optional[Dict[str, Any]] = None,
) -> AdaptiveState:
    """Initialize a compact reconnaissance-oriented AdaptiveState."""

    ch_msgs: List[AnyMessage] = [SystemMessage(make_prompt(conversational_handler_prompt))]
    re_msgs: List[AnyMessage] = [SystemMessage(make_prompt(recon_executor_prompt))]
    ri_msgs: List[AnyMessage] = [SystemMessage(make_prompt(result_interpreter_prompt))]
    sa_msgs: List[AnyMessage] = [SystemMessage(make_prompt(strategy_advisor_prompt))]
    hi_msgs: List[AnyMessage] = []
    if human_in_loop_prompt:
        hi_msgs.append(SystemMessage(make_prompt(human_in_loop_prompt)))

    return AdaptiveState(
        conversational_handler_messages=ch_msgs,
        recon_executor_messages=re_msgs,
        result_interpreter_messages=ri_msgs,
        strategy_advisor_messages=sa_msgs,
        human_in_loop_messages=hi_msgs,
        session_id=session_id,
        target=target or {},
        current_agent="conversational_handler",
        pending_tasks=[],
        executed_commands=[],
        findings=[],
        policy=None,
        cycle=0,
        last_update_ts=None,
    )
