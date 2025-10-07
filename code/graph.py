from typing import Any, Dict
from langgraph.graph import StateGraph, START, END

from state import AdaptiveState
from nodes import (
    make_fuzzer_node,
    make_scanner_node,
    make_enumerator_node,
    make_web_analyzer_node,
    make_exploit_researcher_node,
    make_reporter_node,
)
from routes import (
    route_from_fuzzer,
    route_from_scanner,
)
from consts import (
    FUZZER,
    SCANNER,
    ENUMERATOR,
    WEB_ANALYZER,
    EXPLOIT_RESEARCHER,
    REPORTER,
)

def build_adaptive_graph(config: Dict[str, Any]) -> StateGraph:
    """
    Creates and returns the AdaptiveFuzz penetration testing graph.
    
    Workflow:
        START → Fuzzer (Supervisor) → Scanner → Web Analyzer/Enumerator → 
        Fuzzer → Exploit Researcher → Fuzzer → Reporter → END
    
    The Fuzzer acts as an intelligent router:
    - Routes to Scanner when only user input exists
    - Routes to Exploit Researcher when enumeration data exists but no exploits
    - Routes to Reporter when both enumeration and exploit data exist
    
    Routing Logic:
    - Start → Fuzzer (always starts with the supervisor)
    - Fuzzer uses conditional routing to decide next step. Based on state content, 
      routes to: Scanner, Exploit Researcher, or Reporter
    - Scanner uses conditional routing based on port types discovered. Routes to 
      Web Analyzer if web ports found, Enumerator otherwise
    - After Web Analyzer completes, return to Fuzzer for next decision
    - After Enumerator completes, return to Fuzzer for next decision
    - After Exploit Researcher completes, return to Fuzzer
    - Reporter validates findings, generates final report, and ends the workflow
    
    Args:
        config: Configuration dictionary containing agent settings
    
    Returns:
        Compiled LangGraph StateGraph
    """
    graph = StateGraph(AdaptiveState)
    

    ### ADD NODES
    fuzzer_node = make_fuzzer_node(llm_model=config["agents"]["fuzzer"]["llm"])
    graph.add_node(FUZZER, fuzzer_node)
    
    scanner_node = make_scanner_node(llm_model=config["agents"]["scanner"]["llm"])
    graph.add_node(SCANNER, scanner_node)
    
    enumerator_node = make_enumerator_node(llm_model=config["agents"]["enumerator"]["llm"])
    graph.add_node(ENUMERATOR, enumerator_node)
    
    web_analyzer_node = make_web_analyzer_node(llm_model=config["agents"]["web_analyzer"]["llm"])
    graph.add_node(WEB_ANALYZER, web_analyzer_node)
    
    exploit_researcher_node = make_exploit_researcher_node(llm_model=config["agents"]["exploit_researcher"]["llm"])
    graph.add_node(EXPLOIT_RESEARCHER, exploit_researcher_node)
    
    reporter_node = make_reporter_node(llm_model=config["agents"]["reporter"]["llm"])
    graph.add_node(REPORTER, reporter_node)
    

    ### ADD EDGES AND CONDITIONAL ROUTING
    graph.add_edge(START, FUZZER)
    
    graph.add_conditional_edges(
        FUZZER,
        route_from_fuzzer,
        {
            SCANNER: SCANNER,
            EXPLOIT_RESEARCHER: EXPLOIT_RESEARCHER,
            REPORTER: REPORTER,
        },
    )
    
    graph.add_conditional_edges(
        SCANNER,
        route_from_scanner,
        {
            WEB_ANALYZER: WEB_ANALYZER,
            ENUMERATOR: ENUMERATOR,
            FUZZER: FUZZER,
        },
    )
    
    graph.add_edge(WEB_ANALYZER, FUZZER)
    graph.add_edge(ENUMERATOR, FUZZER)
    graph.add_edge(EXPLOIT_RESEARCHER, FUZZER)
    graph.add_edge(REPORTER, END)
    
    return graph.compile()
