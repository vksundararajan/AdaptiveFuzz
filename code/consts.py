# Node names
CONVERSATIONAL_HANDLER = "conversational_handler"
RECON_EXECUTOR = "recon_executor"
RESULT_INTERPRETER = "result_interpreter"
STRATEGY_ADVISOR = "strategy_advisor"
HUMAN_IN_LOOP = "human_in_loop"


# Config Keys
ADAPTIVE_SYSTEM = "adaptive_system"


# State Keys
TARGET_IP = "target_ip"
TASKS = "tasks"
FINDINGS = "findings"
TO_LOOP = "to_loop"
STRATEGIES = "strategies"
IS_INAPPROPRIATE = "is_inappropriate"
USER_QUERY = "user_query"
TOOL_RESULTS = "tool_results"


# Allowed LLM models
ALLOWED_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "openai/gpt-oss-120b"
]


# MCP Tools
RECON_TOOLS = "recon_tools"
ANALYSIS_TOOLS = "analysis_tools"

ALL_TOOLS = [
    "port_scanner",
    "web_search",
]