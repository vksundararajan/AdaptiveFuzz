import os
import json
from typing import List, Dict, Any, Tuple
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from paths import RECON_TOOLS_PATH, ANALYSIS_TOOLS_PATH


async def get_mcp_tools() -> List[BaseTool]:
    """
    Initializes and returns a list of MCP tools using MultiServerMCPClient.
    """
    mcp_config: Dict[str, Dict[str, Any]] = {
        "recon_tools": {
            "command": "python",
            "args": [RECON_TOOLS_PATH],
            "transport": "stdio",
        },
        "analysis_tools": {
            "command": "python",
            "args": [ANALYSIS_TOOLS_PATH],
            "transport": "stdio",
        },
    }

    client = MultiServerMCPClient(mcp_config)
    mcp_tools = await client.get_tools()
        
    return mcp_tools


async def call_tools(
    ai_response: AIMessage,
    tool_map: Dict[str, BaseTool],
) -> Tuple[List[Dict[str, Any]]]:
    """
    Processes tool calls from an AI response, executes them asynchronously, and returns results.
    """
    if not ai_response.tool_calls:
        return []
    
    io = []
    
    for tool_call in ai_response.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        task_id = tool_args.get("task_id", None)
        tool_input_str = f"{tool_name}({json.dumps(tool_args)})"

        try:
            tool_to_run = tool_map[tool_name]
            observation = await tool_to_run.ainvoke(tool_args)
            
            io.append({
                "task_id": task_id,
                "input": tool_input_str, 
                "output": str(observation)
            })
        except Exception as e:
            error_message = f"Error executing tool {tool_name}: {str(e)}"
            print(f"  - {error_message}")

            io.append({"input": tool_input_str, "output": error_message})
            
    return io


def filter_tools(mcp_tools: List[BaseTool], tag: str) -> List[BaseTool]:
    """
    Filters MCP tools based on a given tag.
    """
    return [tool for tool in mcp_tools if tag in tool.metadata['_meta']['_fastmcp']['tags']]