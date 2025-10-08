from typing import Literal
from state import AdaptiveState


def route_from_human(state: AdaptiveState) -> Literal["continue", "stop"]:
	"""
	Router decides whether agents loop or stop.
	"""
	return "continue" if state.get("keep_loop") else "stop"
