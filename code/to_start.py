"""Entry point for running the AdaptiveFuzz reconnaissance workflow."""

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


def run_adaptivefuzz(user_query: str) -> Dict[str, Any]:
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

	initial_state = initialize_adaptive_state(
		fuzz_id=final_state["fuzz_id"],
		conversational_handler_prompt=CONVERSATIONAL_HANDLER,
		recon_executor_prompt=RECON_EXECUTOR,
		result_interpreter_prompt=RESULT_INTERPRETER,
		strategy_advisor_prompt=STRATEGY_ADVISOR,
		human_in_loop_prompt=user_query,
		target={"user_request": user_query},
	)

	final_state = graph.invoke(initial_state)
	return final_state


def main() -> None:
	"""CLI entry point for AdaptiveFuzz."""

	print("=" * 80)
	print("🌀 AdaptiveFuzz")
	print("=" * 80)
	print("Provide a single, well-scoped reconnaissance objective for the agents to pursue.\n")

	while True:
		try:
			user_query = input("Enter the reconnaissance objective or target: ").strip()
		except KeyboardInterrupt:  # pragma: no cover - user-controlled exit
			print("\nAborted by user.")
			raise SystemExit(1)

		if user_query:
			break

		print("A non-empty objective is required. Please try again.\n")

	final_state = run_adaptivefuzz(user_query)

	print("\n" + "=" * 80)
	print("✅ AdaptiveFuzz run completed")
	print("=" * 80)
	print("FUZZ ID:", final_state.get("fuzz_id"))
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
