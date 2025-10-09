from __future__ import annotations

from pprint import pprint
from typing import Any, Dict
import uuid

from langgraph.types import Command

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
from to_help import load_yaml_file, save_graph_visualization
from to_prompt import c_prompt


def run_adaptivefuzz(target_ip: str, user_query: str) -> Dict[str, Any]:
    """Run the AdaptiveFuzz LangGraph for the provided reconnaissance request."""
    config = load_yaml_file(PROMPTS_CONFIG_PATH)
    adaptive_config = config[ADAPTIVE_SYSTEM]

    graph = build_adaptive_graph(adaptive_config)
    # saved_path = save_graph_visualization(graph)
    # print(f"➡️  Graph visualisation saved to: {saved_path}")

    fuzz_id = str(uuid.uuid4())

    initial_state = initialize_adaptive_state(
        fuzz_id=fuzz_id,
        target_ip=target_ip,
        user_query=user_query,
        conversational_handler=CONVERSATIONAL_HANDLER,
        recon_executor=RECON_EXECUTOR,
        result_interpreter=RESULT_INTERPRETER,
        strategy_advisor=STRATEGY_ADVISOR,
    )

    thread_config = {"configurable": {"thread_id": fuzz_id}}
    state = graph.invoke(initial_state, config=thread_config)

    while True:
        interrupt = state.get("__interrupt__")
        if not interrupt:
            return state

        print("\n⚠️  Your assistant is coming online...")
        print(interrupt[0].value)
        human_reply = input("Fuzzer⫸ ").strip()
        state = graph.invoke(Command(resume={"human_reply": human_reply}), config=thread_config)



def main() -> None:
	"""CLI entry point for AdaptiveFuzz."""

	print("=" * 80)
	print("📌  AdaptiveFuzz")
	print("=" * 80)
	print("\n")

	target_ip = c_prompt("Target IP Address: ")
	print("\n⚠️  Your assistant is coming online...")
	user_query = c_prompt("Fuzzer⫸ ")
	print("\n")

	final_state = run_adaptivefuzz(target_ip, user_query)

if __name__ == "__main__":
	main()
