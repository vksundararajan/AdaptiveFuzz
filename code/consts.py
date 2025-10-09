# Node names
CONVERSATIONAL_HANDLER = "conversational_handler"
RECON_EXECUTOR = "recon_executor"
RESULT_INTERPRETER = "result_interpreter"
STRATEGY_ADVISOR = "strategy_advisor"
HUMAN_IN_LOOP = "human_in_loop"


# Config Keys
ADAPTIVE_SYSTEM = "adaptive_system"


# State Keys
CONVERSATIONAL_HANDLER_MESSAGES = "conversational_handler_messages"
RECON_EXECUTOR_MESSAGES = "recon_executor_messages"
RESULT_INTERPRETER_MESSAGES = "result_interpreter_messages"
STRATEGY_ADVISOR_MESSAGES = "strategy_advisor_messages"
HUMAN_IN_LOOP_MESSAGES = "human_in_loop_messages"
FUZZ_ID = "fuzz_id"
TARGET_IP = "target_ip"
PENDING_TASKS = "pending_tasks"
EXECUTED_COMMANDS = "executed_commands"
FINDINGS = "findings"
POLICY = "policy"
CYCLE = "cycle"
LAST_UPDATE_TS = "last_update_ts"
TO_LOOP = "to_loop"
STRATEGIES = "strategies"
IS_INAPPROPRIATE = "is_inappropriate"
COMPLETED_TASKS = "completed_tasks"
USER_QUERY = "user_query"


# Allowed LLM models
ALLOWED_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "openai/gpt-oss-120b"
]


# MCP Tools
RECON_TOOLS = "recon_tools"
ANALYSIS_TOOLS = "analysis_tools"