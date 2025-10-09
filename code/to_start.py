from __future__ import annotations

import asyncio
from pprint import pprint
from typing import Any, Dict
import uuid

from langgraph.types import Command
from langchain_mcp_adapters.client import MultiServerMCPClient

from consts import (
	ADAPTIVE_SYSTEM,
    CONVERSATIONAL_HANDLER,
    RECON_EXECUTOR,
    RESULT_INTERPRETER,
    STRATEGY_ADVISOR,
)
from graph import build_adaptive_graph
from paths import PROMPTS_CONFIG_PATH
from state import initialize_adaptive_state
from to_help import load_yaml_file, save_graph_visualization
from to_prompt import c_prompt


async def run_adaptivefuzz(target_ip: str, user_query: str) -> Dict[str, Any]:
    """Run the AdaptiveFuzz LangGraph for the provided reconnaissance request."""
    config = load_yaml_file(PROMPTS_CONFIG_PATH)
    adaptive_config = config[ADAPTIVE_SYSTEM]
	
    ### Tools for recon
    recon_tools = MultiServerMCPClient({
        "http": {
            "command": "python",
            "args": ["code/tools/recon_tools.py"],
            "transport": "stdio",
        },
    })
    recon_tools = await recon_tools.get_tools()

    ### Tools for analysis
    analysis_tools = MultiServerMCPClient({
        "terminal": {
            "command": "python",
            "args": ["code/tools/analysis_tools.py"],
            "transport": "stdio",
        },
    })    
    analysis_tools = await analysis_tools.get_tools()
    
    graph = build_adaptive_graph(adaptive_config, [
        recon_tools, 
        analysis_tools
    ])
    
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

	asyncio.run(run_adaptivefuzz(target_ip, user_query))

if __name__ == "__main__":
	main()
