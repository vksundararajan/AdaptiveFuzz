from typing import Literal
from .state import AdaptiveState
from consts import (
    FUZZER,
    SCANNER,
    ENUMERATOR,
    WEB_ANALYZER,
    EXPLOIT_RESEARCHER,
    REPORTER,
)


def route_from_fuzzer(state: AdaptiveState) -> Literal["scanner", "exploit_researcher", "reporter"]:
    """
    Conditional routing function from Fuzzer (Supervisor).
    
    Routing Logic:
    1. Scanner → when no scan completed
    2. Exploit Researcher → when enumeration done, no exploit research
    3. Reporter → when all phases complete
    """
    has_scan_data = state.get('scan_completed', False)
    has_enumeration_data = (
        state.get('enumeration_completed', False) or 
        state.get('web_analysis_completed', False)
    )
    has_exploit_data = state.get('exploit_research_completed', False)
    
    if not has_scan_data:
        print("🔀 Fuzzer routing to: SCANNER (no scan data)\n")
        return SCANNER
    elif has_enumeration_data and not has_exploit_data:
        print("🔀 Fuzzer routing to: EXPLOIT_RESEARCHER (scan complete, needs exploit research)\n")
        return EXPLOIT_RESEARCHER
    elif has_enumeration_data and has_exploit_data:
        print("🔀 Fuzzer routing to: REPORTER (all data collected)\n")
        return REPORTER
    else:
        # Default to scanner if state is unclear
        print("🔀 Fuzzer routing to: SCANNER (default)\n")
        return SCANNER


def route_from_scanner(state: AdaptiveState) -> Literal["web_analyzer", "enumerator", "fuzzer"]:
    """
    Conditional routing function from Scanner.
    
    Routing Logic:
    1. Web Analyzer → when web ports detected
    2. Enumerator → when non-web ports found
    3. Fuzzer → when no specific ports (fallback)
    """
    web_ports_detected = state.get('web_ports_detected', False)
    non_web_ports = state.get('non_web_ports', [])
    
    if web_ports_detected:
        print("🔀 Scanner routing to: WEB_ANALYZER (web ports detected)\n")
        return WEB_ANALYZER
    elif non_web_ports and len(non_web_ports) > 0:
        print("🔀 Scanner routing to: ENUMERATOR (non-web ports detected)\n")
        return ENUMERATOR
    else:
        print("🔀 Scanner routing to: FUZZER (no specific ports, return to supervisor)\n")
        return FUZZER
