from typing import List, Optional, TypedDict, Dict, Any
from typing_extensions import Annotated
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage
from langgraph.graph.message import add_messages
from prompt_builder import build_prompt


class AdaptiveState(TypedDict):
    """
    State class for the AdaptiveFuzz system.
    """
    
    ### USER INPUT
    target_ip: str
    target_url: Optional[str]
    user_hints: Optional[str]
    scope_notes: Optional[str]
    
    ### FUZZER (SUPERVISOR) STATE
    fuzzer_messages: Annotated[list[AnyMessage], add_messages]
    current_phase: Optional[str]  # "initial", "scanning", "enumeration", "exploitation", "reporting"
    
    ### SCANNER STATE
    scanner_messages: Annotated[list[AnyMessage], add_messages]
    open_ports: Optional[List[Dict[str, Any]]]  # [{port: 80, protocol: "tcp", state: "open", service: "http"}]
    web_ports_detected: Optional[bool]  # True if ports 80, 443, 8080, 8443, etc. are open
    non_web_ports: Optional[List[int]]  # Ports that are not web-related
    os_fingerprint: Optional[str]  # Operating system detection result
    scan_completed: Optional[bool]
    
    ### ENUMERATOR STATE
    enumerator_messages: Annotated[list[AnyMessage], add_messages]
    service_enumeration: Optional[List[Dict[str, Any]]]  # Detailed service info per port
    version_detection: Optional[Dict[str, str]]  # {service_name: version}
    banner_grabbing_results: Optional[Dict[str, str]]  # {port: banner_text}
    enumeration_completed: Optional[bool]
    
    ### WEB ANALYZER STATE
    web_analyzer_messages: Annotated[list[AnyMessage], add_messages]
    detected_technologies: Optional[List[Dict[str, Any]]]  # Web tech fingerprinting results
    security_headers: Optional[Dict[str, Any]]  # Security header analysis
    discovered_directories: Optional[List[str]]  # Directory enumeration results
    discovered_files: Optional[List[str]]  # File enumeration results
    subdomains: Optional[List[str]]  # Subdomain discovery results
    interesting_parameters: Optional[List[str]]  # Fuzzing-discovered parameters
    web_analysis_completed: Optional[bool]
    
    ### EXPLOIT RESEARCHER STATE
    exploit_researcher_messages: Annotated[list[AnyMessage], add_messages]
    identified_vulnerabilities: Optional[List[Dict[str, Any]]]  # CVEs and vulnerabilities
    available_exploits: Optional[List[Dict[str, Any]]]  # ExploitDB matches
    attack_vectors: Optional[List[str]]  # Potential exploitation paths
    exploitability_score: Optional[float]  # Overall exploitability rating (0-10)
    credential_findings: Optional[List[str]]  # Found credentials/hashes
    exploit_research_completed: Optional[bool]
    
    ### REPORTER STATE
    reporter_messages: Annotated[list[AnyMessage], add_messages]
    validation_status: Optional[str]  # "passed", "failed", "needs_retry"
    validation_errors: Optional[List[str]]  # Issues found during validation
    final_report_md: Optional[str]  # Complete markdown report
    risk_assessment: Optional[str]  # "critical", "high", "medium", "low", "info"
    report_completed: Optional[bool]
    
    ### GLOBAL METADATA
    execution_history: Optional[List[Dict[str, Any]]]  # All commands/tools executed
    retry_count: Optional[int]
    max_retries: Optional[int]
    completed_nodes: Optional[List[str]]  # Track which nodes have finished
    start_time: Optional[str]
    end_time: Optional[str]


def initialize_adaptive_state(
    target_ip: str,
    target_url: Optional[str] = None,
    user_hints: Optional[str] = None,
    scope_notes: Optional[str] = None,
    max_retries: int = 3,
    fuzzer_prompt: Optional[str] = None,
    scanner_prompt: Optional[str] = None,
    enumerator_prompt: Optional[str] = None,
    web_analyzer_prompt: Optional[str] = None,
    exploit_researcher_prompt: Optional[str] = None,
    reporter_prompt: Optional[str] = None,
) -> AdaptiveState:
    """
    Initialize the AdaptiveFuzz state with default values and system prompts.
    
    Args:
        target_ip: The target IP address to scan
        target_url: Optional target URL if web application testing
        user_hints: Optional hints from user about the target
        scope_notes: Optional scope restrictions or notes
        max_retries: Maximum number of retry attempts for failed operations
        fuzzer_prompt: System prompt for Fuzzer (Supervisor) agent
        scanner_prompt: System prompt for Scanner agent
        enumerator_prompt: System prompt for Enumerator agent
        web_analyzer_prompt: System prompt for Web Analyzer agent
        exploit_researcher_prompt: System prompt for Exploit Researcher agent
        reporter_prompt: System prompt for Reporter agent
    
    Returns:
        Initialized AdaptiveState
    """
    default_fuzzer_prompt = build_prompt('fuzzer')
    default_scanner_prompt = build_prompt('scanner')
    default_enumerator_prompt = build_prompt('enumerator')
    default_web_analyzer_prompt = build_prompt('web_analyzer')
    default_exploit_researcher_prompt = build_prompt('exploit_researcher')
    default_reporter_prompt = build_prompt('reporter')
    
    target_info = f"Target IP: {target_ip}"
    if target_url:
        target_info += f"\nTarget URL: {target_url}"
    if user_hints:
        target_info += f"\nUser Hints: {user_hints}"
    if scope_notes:
        target_info += f"\nScope Notes: {scope_notes}"
    
    fuzzer_messages = [
        SystemMessage(content=fuzzer_prompt or default_fuzzer_prompt),
        HumanMessage(content=f"Starting penetration test.\n\n{target_info}"),
    ]
    
    scanner_messages = [
        SystemMessage(content=scanner_prompt or default_scanner_prompt),
        SystemMessage(content=f"Target information:\n{target_info}"),
    ]
    
    enumerator_messages = [
        SystemMessage(content=enumerator_prompt or default_enumerator_prompt),
        SystemMessage(content=f"Target information:\n{target_info}"),
    ]
    
    web_analyzer_messages = [
        SystemMessage(content=web_analyzer_prompt or default_web_analyzer_prompt),
        SystemMessage(content=f"Target information:\n{target_info}"),
    ]
    
    exploit_researcher_messages = [
        SystemMessage(content=exploit_researcher_prompt or default_exploit_researcher_prompt),
        SystemMessage(content=f"Target information:\n{target_info}"),
    ]
    
    reporter_messages = [
        SystemMessage(content=reporter_prompt or default_reporter_prompt),
        SystemMessage(content=f"Target information:\n{target_info}"),
    ]
    
    return AdaptiveState(
        ### User input
        target_ip=target_ip,
        target_url=target_url,
        user_hints=user_hints,
        scope_notes=scope_notes,
        
        ### Fuzzer (Supervisor)
        fuzzer_messages=fuzzer_messages,
        current_phase="initial",
        
        ### Scanner
        scanner_messages=scanner_messages,
        open_ports=None,
        web_ports_detected=None,
        non_web_ports=None,
        os_fingerprint=None,
        scan_completed=False,
        
        ### Enumerator
        enumerator_messages=enumerator_messages,
        service_enumeration=None,
        version_detection=None,
        banner_grabbing_results=None,
        enumeration_completed=False,
        
        ### Web Analyzer
        web_analyzer_messages=web_analyzer_messages,
        detected_technologies=None,
        security_headers=None,
        discovered_directories=None,
        discovered_files=None,
        subdomains=None,
        interesting_parameters=None,
        web_analysis_completed=False,
        
        ### Exploit Researcher
        exploit_researcher_messages=exploit_researcher_messages,
        identified_vulnerabilities=None,
        available_exploits=None,
        attack_vectors=None,
        exploitability_score=None,
        credential_findings=None,
        exploit_research_completed=False,
        
        ### Reporter
        reporter_messages=reporter_messages,
        validation_status=None,
        validation_errors=None,
        final_report_md=None,
        risk_assessment=None,
        report_completed=False,
        
        ### Global metadata
        execution_history=[],
        retry_count=0,
        max_retries=max_retries,
        completed_nodes=[],
        start_time=None,
        end_time=None,
    )
