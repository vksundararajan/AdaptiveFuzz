from typing import Any, Dict, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode

from state import AdaptiveState
from routes import (
    route_from_human, 
    route_from_conversational_handler,
    route_recon_executor_tools,
    route_result_interpreter_tools
)
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
    RECON_EXECUTOR_MESSAGES,
    RESULT_INTERPRETER_MESSAGES,
)

def build_adaptive_graph(config: Dict[str, Any], all_tools: List) -> StateGraph:
    """
    Build the AdaptiveFuzz graph.
    """
    graph = StateGraph(AdaptiveState)
    recon_tools, analysis_tools = all_tools

    # Create wrapper functions for ToolNodes that handle message field mapping
    def recon_tools_node(state: AdaptiveState) -> Dict[str, Any]:
        """Wrapper for recon tools that maps message fields correctly."""
        # Create a temporary state with 'messages' field for ToolNode
        temp_state = {"messages": state[RECON_EXECUTOR_MESSAGES]}
        tool_node = ToolNode(recon_tools)
        result = tool_node.invoke(temp_state)
        # Return updates for the correct message field
        return {RECON_EXECUTOR_MESSAGES: result["messages"]}
    
    def analysis_tools_node(state: AdaptiveState) -> Dict[str, Any]:
        """Wrapper for analysis tools that maps message fields correctly."""
        # Create a temporary state with 'messages' field for ToolNode
        temp_state = {"messages": state[RESULT_INTERPRETER_MESSAGES]}
        tool_node = ToolNode(analysis_tools)
        result = tool_node.invoke(temp_state)
        # Return updates for the correct message field
        return {RESULT_INTERPRETER_MESSAGES: result["messages"]}

    conversational_handler_node = make_ch_node(llm_model=config["agents"][CONVERSATIONAL_HANDLER]["llm"])
    graph.add_node(CONVERSATIONAL_HANDLER, conversational_handler_node)

    recon_executor_node = make_re_node(llm_model=config["agents"][RECON_EXECUTOR]["llm"], tools=recon_tools)
    graph.add_node(RECON_EXECUTOR, recon_executor_node)

    result_interpreter_node = make_ri_node(llm_model=config["agents"][RESULT_INTERPRETER]["llm"], tools=analysis_tools)
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

    ### MCP Tools Integration
    graph.add_node(RECON_TOOLS, recon_tools_node)
    graph.add_conditional_edges(
        RECON_EXECUTOR, 
        route_recon_executor_tools, 
        {
            "tools": RECON_TOOLS,
            "continue": RESULT_INTERPRETER
        }
    )
    graph.add_edge(RECON_TOOLS, RECON_EXECUTOR)
    
    graph.add_node(ANALYSIS_TOOLS, analysis_tools_node)
    graph.add_conditional_edges(
        RESULT_INTERPRETER, 
        route_result_interpreter_tools, 
        {
            "tools": ANALYSIS_TOOLS,
            "continue": STRATEGY_ADVISOR
        }
    )
    graph.add_edge(ANALYSIS_TOOLS, RESULT_INTERPRETER)

    graph.add_edge(STRATEGY_ADVISOR, HUMAN_IN_LOOP)

    graph.add_conditional_edges(
        HUMAN_IN_LOOP,
        route_from_human,
        {
            "continue": CONVERSATIONAL_HANDLER,
            "stop": END,
        },
    )

    ### Checkpointer for human loop
    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)
