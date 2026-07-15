import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT_DIR, ".env")
CODE_DIR = os.path.join(ROOT_DIR, "code")
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_DIR = os.path.join(ROOT_DIR, "outputs")
MODELS_DIR = os.path.join(ROOT_DIR, "models")
PROMPT_CONFIG_PATH = os.path.join(CODE_DIR, "config", "prompt_config.yaml")
REASONING_CONFIG_PATH = os.path.join(CODE_DIR, "config", "reasoning_config.yaml")
VECTOR_DB_DIR = os.path.join(OUTPUT_DIR, "vector_db")
DEFAULT_MODEL_PATH = os.path.join(MODELS_DIR, "google_gemma-4-E4B-it-Q6_K_L.gguf")

# Automatically create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
