from __future__ import annotations

from pprint import pprint
from typing import Any, Dict
import uuid

from consts import (
	CONVERSATIONAL_HANDLER,
	RECON_EXECUTOR,
	RESULT_INTERPRETER,
	STRATEGY_ADVISOR,
	ADAPTIVE_SYSTEM,
)
from graph import build_adaptive_graph
from paths import PROMPTS_CONFIG_PATH
from state import initialize_adaptive_state
from utils import load_yaml_file, save_graph_visualization
from to_prompt import c_prompt


def run_adaptivefuzz(target_ip: str, user_query: str) -> Dict[str, Any]:
	"""Run the AdaptiveFuzz LangGraph for the provided reconnaissance request."""

	config = load_yaml_file(PROMPTS_CONFIG_PATH)
	adaptive_config = config[ADAPTIVE_SYSTEM]

	graph = build_adaptive_graph(adaptive_config)
	
    ### --- GRAPH VIEW ---
	# saved_path = save_graph_visualization(graph)
	# print(f"➡️  Graph visualisation saved to: {saved_path}")

	# final_state: Dict[str, Any] = {
	# 	"fuzz_id": str(uuid.uuid4()),
	# 	"cycle": 0,
	# 	"pending_tasks": [],
	# 	"executed_commands": [],
	# 	"findings": [],
	# 	"graph_saved_path": saved_path,
	# 	"user_query": user_query,
	# }

	fuzz_id = str(uuid.uuid4())

	initial_state = initialize_adaptive_state(
		fuzz_id=fuzz_id,
		target_ip=target_ip,
		human_in_loop=user_query,
		conversational_handler=CONVERSATIONAL_HANDLER,
		recon_executor=RECON_EXECUTOR,
		result_interpreter=RESULT_INTERPRETER,
		strategy_advisor=STRATEGY_ADVISOR,
	)

	final_state = graph.invoke(initial_state)
	return final_state


def main() -> None:
	"""CLI entry point for AdaptiveFuzz."""

	print("=" * 80)
	print("⚠️  AdaptiveFuzz")
	print("=" * 80)
	print("\n")

	target_ip = c_prompt("Target IP Address: ")
	print("\n⚠️  Your assistant is coming online...")
	user_query = c_prompt("Fuzzer⋙ ")

	final_state = run_adaptivefuzz(target_ip, user_query)

	print("\n" + "=" * 80)
	print("✅  AdaptiveFuzz run completed")
	print("=" * 80)
	print("FUZZ ID:", final_state.get("fuzz_id"))
	print("Target IP:", final_state.get("target_ip"))
	print("Cycle count:", final_state.get("cycle"))
	print("Pending tasks:")
	pprint(final_state.get("pending_tasks", []))
	print("Executed commands:")
	pprint(final_state.get("executed_commands", []))
	print("Findings:")
	pprint(final_state.get("findings", []))

	graph_path = final_state.get("graph_saved_path")
	if graph_path:
		print("Graph visualisation saved to:", graph_path)


if __name__ == "__main__":
	main()
