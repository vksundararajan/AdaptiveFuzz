import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
CODE_DIR = os.path.join(ROOT_DIR, "code")
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")

PROMPTS_CONFIG_PATH = os.path.join(CODE_DIR, "config", "prompts.yaml")
AI_RESPONSE_PATH = os.path.join(CODE_DIR, "config", "ai_responses.yaml")