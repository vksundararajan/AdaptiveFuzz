from typing import Any, Dict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode, tools_condition

from state import AdaptiveState
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
    RECON_TOOLS,
    ANALYSIS_TOOLS,
)

def build_adaptive_graph(config: Dict[str, Any], all_tools: List) -> StateGraph:
    """
    Build the AdaptiveFuzz graph.
    """
    graph = StateGraph(AdaptiveState)

    conversational_handler_node = make_ch_node(llm_model=config["agents"][CONVERSATIONAL_HANDLER]["llm"])
    graph.add_node(CONVERSATIONAL_HANDLER, conversational_handler_node)

    recon_executor_node = make_re_node(llm_model=config["agents"][RECON_EXECUTOR]["llm"])
    graph.add_node(RECON_EXECUTOR, recon_executor_node)

    result_interpreter_node = make_ri_node(llm_model=config["agents"][RESULT_INTERPRETER]["llm"])
    graph.add_node(RESULT_INTERPRETER, result_interpreter_node)

    strategy_advisor_node = make_sa_node(llm_model=config["agents"][STRATEGY_ADVISOR]["llm"])
    graph.add_node(STRATEGY_ADVISOR, strategy_advisor_node)

    human_in_loop_node = make_hr_node(llm_model=config["agents"][HUMAN_IN_LOOP]["llm"])
    graph.add_node(HUMAN_IN_LOOP, human_in_loop_node)

    graph.add_edge(START, CONVERSATIONAL_HANDLER)

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

    graph.add_conditional_edges(
        HUMAN_IN_LOOP,
        route_from_human,
        {
            "continue": CONVERSATIONAL_HANDLER,
            "stop": END,
        },
    )

    ### MCP Tools Integration
    recon_tools, analysis_tools = all_tools

    graph.add_node(RECON_TOOLS, ToolNode(recon_tools))
    graph.add_conditional_edges(RECON_EXECUTOR, tools_condition, {"tools": RECON_TOOLS})
    graph.add_edge(RECON_TOOLS, RECON_EXECUTOR)
    
    graph.add_node(ANALYSIS_TOOLS, ToolNode(analysis_tools))
    graph.add_conditional_edges(RESULT_INTERPRETER, tools_condition, {"tools": ANALYSIS_TOOLS})
    graph.add_edge(ANALYSIS_TOOLS, RESULT_INTERPRETER)

    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)
