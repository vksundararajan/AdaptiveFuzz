import os
from typing import Any, Dict

import yaml
from langgraph.graph import StateGraph
from langchain_core.runnables.graph import MermaidDrawMethod
from langchain_google_genai import ChatGoogleGenerativeAI

from consts import ALLOWED_MODELS
from paths import OUTPUT_DIR


def get_llm(llm_model: str):
    """
    Factory function to get LLM instance based on model name.
    
    Args:
        llm_model: Model identifier (e.g., "gemini-2.5-flash")
    
    Returns:
        Configured LLM instance
    
    Raises:
        ValueError: If model name is not in the approved whitelist
    """
    if llm_model in ALLOWED_MODELS:
        return ChatGoogleGenerativeAI(model=llm_model, temperature=0.2)
    else:
        raise ValueError(
            f"Invalid model '{llm_model}'. "
            f"Allowed Gemini models: {sorted(ALLOWED_MODELS)}"
        )


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Load and parse a YAML configuration file.
    
    Args:
        file_path: Path to the YAML file
    
    Returns:
        Parsed YAML content as a dictionary
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
    """
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def save_graph_visualization(
    graph: StateGraph,
    save_dir: str = None,
    graph_name: str = "graph",
):
    """
    Render and save the LangGraph structure as a Mermaid-based mmd or PNG image.
    
    Args:
        graph: Compiled LangGraph StateGraph to visualize
        save_dir: Directory to save the image (defaults to OUTPUT_DIR from paths.py)
        graph_name: Name of the output file without extension (default: "graph")
    """
    if save_dir is None:
        save_dir = OUTPUT_DIR

    graph_output_dir = save_dir
    os.makedirs(graph_output_dir, exist_ok=True)

    mermaid_path = os.path.join(graph_output_dir, f"{graph_name}.mmd")
    png_path = os.path.join(graph_output_dir, f"{graph_name}.png")

    try:
        mermaid_source = graph.get_graph().draw_mermaid()
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write(mermaid_source)
        return mermaid_path
    except Exception:
        try:
            png_bytes = graph.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)
            with open(png_path, "wb") as f:
                f.write(png_bytes)
            return png_path
        except Exception:
            return None
