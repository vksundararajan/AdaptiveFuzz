from typing import Any, Dict
from datetime import datetime
from pprint import pprint

from code.graph import build_adaptive_graph
from code.state import initialize_adaptive_state
from code.utils import save_graph_visualization, load_yaml_file, save_report
from code.paths import PROMPTS_CONFIG_PATH
from consts import (
    FUZZER,
    SCANNER,
    ENUMERATOR,
    WEB_ANALYZER,
    EXPLOIT_RESEARCHER,
    REPORTER,
)


def run_adaptive_fuzz(
    target_ip: str,
    target_url: str = None,
    user_hints: str = None,
    scope_notes: str = None,
) -> Dict[str, Any]:
    """
    Runs the AdaptiveFuzz penetration testing graph.
    
    Args:
        target_ip: The target IP address to scan
        target_url: Optional target URL for web application testing
        user_hints: Optional hints about the target
        scope_notes: Optional scope restrictions
    
    Returns:
        Final state dictionary with all findings and report
    """
    
    adaptive_config = load_yaml_file(PROMPTS_CONFIG_PATH)['adaptive_system']
    
    # Initialize state
    initial_state = initialize_adaptive_state(
        target_ip=target_ip,
        target_url=target_url,
        user_hints=user_hints,
        scope_notes=scope_notes,
        max_retries=adaptive_config.get('max_retries', 3),
    )
    
    # Build the graph
    graph = build_adaptive_graph(adaptive_config)
    save_graph_visualization(graph, graph_name="adaptive_fuzz")
    
    # Set start time
    initial_state["start_time"] = datetime.now().isoformat()
    
    # Run the graph
    final_state = graph.invoke(initial_state)
    
    return final_state


if __name__ == "__main__":
    
    # ⚠️⚠️⚠️ CAUTION ⚠️⚠️⚠️
    # -------------------------------------------------------------------------------
    # 🚨 This runs actual penetration testing tools
    # 🔒 Only use on systems you have explicit permission to test
    # � May consume significant API tokens
    # -------------------------------------------------------------------------------
    
    print("=" * 80)
    print("ADAPTIVEFUZZ - Agentic Penetration Testing System")
    print("=" * 80)
    print("\n⚠️  WARNING: Only test systems you have explicit permission to access!\n")
    
    # Get target information from user
    target_ip = input("Enter target IP address: ").strip()
    
    if not target_ip:
        print("❌ Target IP is required!")
        exit(1)
    
    # Optional: Target URL 
    target_url = input("Enter target URL (skip=Enter): ").strip()
    target_url = target_url if target_url else None
    
    # Optional: User hints
    user_hints = input("Enter hints about the target (skip=Enter): ").strip()
    user_hints = user_hints if user_hints else None
    
    # Optional: Scope notes
    scope_notes = input("Enter scope notes/restrictions (skip=Enter): ").strip()
    scope_notes = scope_notes if scope_notes else None
    
    print("\n" + "=" * 80)
    confirm = input("\n🫡 Ready to start? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y', 'Yes', 'Y']:
        print("❌ Cancelled by user")
        exit(0)
    
    print("\n🔄 Starting penetration testing workflow...\n")
    
    response = run_adaptive_fuzz(
        target_ip=target_ip,
        target_url=target_url,
        user_hints=user_hints,
        scope_notes=scope_notes,
    )
    
    if response.get('final_report_md'):
        report_filename = save_report(response['final_report_md'], target_ip)
        print(f"\n👉 Report saved to outputs/{report_filename}")
    else:
        print("\n⚠️  No report generated")
    
