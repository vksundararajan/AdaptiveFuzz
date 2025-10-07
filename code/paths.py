import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
CODE_DIR = os.path.join(ROOT_DIR, "code")
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")

# Add CODE_DIR to Python path for imports
if CODE_DIR not in sys.path:
    sys.path.insert(0, CODE_DIR)

COMMANDS_CONFIG_PATH = os.path.join(CODE_DIR, "config", "commands.yaml")
PROMPTS_CONFIG_PATH = os.path.join(CODE_DIR, "config", "prompts.yaml")

GRAPH_PATH = os.path.join(CODE_DIR, "graph.py")
STATE_PATH = os.path.join(CODE_DIR, "state.py")
UTILS_PATH = os.path.join(CODE_DIR, "utils.py")
NODES_PATH = os.path.join(CODE_DIR, "nodes.py")

EXECUTER_TOOL_PATH = os.path.join(CODE_DIR, "tools", "terminal.py")
SEARCH_TOOL_PATH = os.path.join(CODE_DIR, "tools", "search.py")
API_ANALYSIS_TOOL_PATH = os.path.join(CODE_DIR, "tools", "api.py")
