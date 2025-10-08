from typing import Literal
from consts import TO_LOOP, IS_INAPPROPRIATE
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
