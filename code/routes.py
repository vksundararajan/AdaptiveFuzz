from typing import Literal
from consts import TO_LOOP, IS_INAPPROPRIATE, RECON_EXECUTOR_MESSAGES, RESULT_INTERPRETER_MESSAGES
from state import AdaptiveState


def route_from_human(state: AdaptiveState) -> Literal["continue", "stop"]:
	"""
	Router decides whether agents loop or stop.
	"""
	return "continue" if state.get(TO_LOOP) else "stop"


def route_from_conversational_handler(state: AdaptiveState) -> Literal["review", "proceed"]:
	"""
	Determine whether to escalate to the human or continue automated recon.
	"""
	return "review" if state.get(IS_INAPPROPRIATE) else "proceed"


def route_recon_executor_tools(state: AdaptiveState) -> Literal["tools", "continue"]:
	"""
	Route recon executor to tools if the last message has tool calls, otherwise continue.
	"""
	messages = state.get(RECON_EXECUTOR_MESSAGES, [])
	if not messages:
		return "continue"
	
	last_message = messages[-1]
	if hasattr(last_message, "tool_calls") and last_message.tool_calls:
		return "tools"
	return "continue"


def route_result_interpreter_tools(state: AdaptiveState) -> Literal["tools", "continue"]:
	"""
	Route result interpreter to tools if the last message has tool calls, otherwise continue.
	"""
	messages = state.get(RESULT_INTERPRETER_MESSAGES, [])
	if not messages:
		return "continue"
	
	last_message = messages[-1]
	if hasattr(last_message, "tool_calls") and last_message.tool_calls:
		return "tools"
	return "continue"
