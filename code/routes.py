from typing import Literal
from state import AdaptiveState


def route_from_human(state: AdaptiveState) -> Literal["continue", "stop"]:
	"""
	Router decides whether agents loop or stop.
	"""
	return "continue" if state.get("keep_loop") else "stop"


def route_from_conversational_handler(state: AdaptiveState) -> Literal["escalate", "proceed"]:
	"""
	Determine whether to escalate to the human or continue automated recon.
	"""
	return "review" if state.get("is_inappropriate") else "proceed"
