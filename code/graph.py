# --- Langsmith Fix ---
# Add the 'code' directory (which contains this file) to the Python path.
# This must be done BEFORE importing any other local modules.
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# --- End of Fix ---

import uuid
from typing import Any, Dict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode

from state import AdaptiveState
from paths import PROMPTS_CONFIG_PATH
from to_help import load_yaml_file_async, save_graph_visualization
from routes import route_from_human, route_from_conversational_handler
from nodes import (
    make_ch_node,
    make_re_node,
    make_ri_node,
    make_sa_node,
    make_hr_node,
)
from consts import (
    CONVERSATIONAL_HANDLER,
    RECON_EXECUTOR,
    RESULT_INTERPRETER,
    STRATEGY_ADVISOR,
    HUMAN_IN_LOOP,
    ADAPTIVE_SYSTEM,
)


async def build_adaptive_graph() -> StateGraph:
    """
    Build the AdaptiveFuzz graph.
    """
    graph = StateGraph(AdaptiveState)
    # recon_tools, analysis_tools = all_tools
    # recon_tools, analysis_tools = asyncio.run(all_tools.get_tools())
    
    a_config = await load_yaml_file_async(PROMPTS_CONFIG_PATH)
    config = a_config[ADAPTIVE_SYSTEM]
    config['fuzz_id'] = str(uuid.uuid4())

    graph.add_node(CONVERSATIONAL_HANDLER, make_ch_node(llm_model=config["agents"][CONVERSATIONAL_HANDLER]["llm"]))
    graph.add_node(RECON_EXECUTOR, make_re_node(llm_model=config["agents"][RECON_EXECUTOR]["llm"]))
    graph.add_node(RESULT_INTERPRETER, make_ri_node(llm_model=config["agents"][RESULT_INTERPRETER]["llm"]))
    graph.add_node(STRATEGY_ADVISOR, make_sa_node(llm_model=config["agents"][STRATEGY_ADVISOR]["llm"]))
    graph.add_node(HUMAN_IN_LOOP, make_hr_node())

    graph.add_edge(START, HUMAN_IN_LOOP)
    graph.add_conditional_edges(
        HUMAN_IN_LOOP,
        route_from_human,
        {
            "continue": CONVERSATIONAL_HANDLER,
            "stop": END,
        },
    )

    graph.add_conditional_edges(
        CONVERSATIONAL_HANDLER,
        route_from_conversational_handler,
        {
            "review": HUMAN_IN_LOOP,
            "proceed": RECON_EXECUTOR,
        },
    )

    graph.add_edge(RECON_EXECUTOR, RESULT_INTERPRETER)
    graph.add_edge(RESULT_INTERPRETER, STRATEGY_ADVISOR)
    graph.add_edge(STRATEGY_ADVISOR, HUMAN_IN_LOOP)    
    
    ### Checkpointer for human loop
    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)


# graph = build_adaptive_graph()
# saved_path = save_graph_visualization(graph)    
# print(f"➡️  Graph visualisation saved to: {saved_path}")