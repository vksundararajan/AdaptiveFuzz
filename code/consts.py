# Node names
CONVERSATIONAL_HANDLER = "conversational_handler"
RECON_EXECUTOR = "recon_executor"
RESULT_INTERPRETER = "result_interpreter"
STRATEGY_ADVISOR = "strategy_advisor"
HUMAN_IN_LOOP = "human_in_loop"


# Allowed LLM models
ALLOWED_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
]


# MCP Tools
TOOLS = [
    "secure_executor",
    "get_executor_history",
    "get_allowed_commands",
    "make_http_request",
    "check_security_headers",
    "search_exploitdb",
    "detect_technologies",
    "lookup_cve"
]