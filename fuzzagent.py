import logging
from typing import Any
from utils.recipe import CTF_RECIPE
from utils.tools import register_tools
from mcp.server.fastmcp import FastMCP

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# Initialize FastMCP server
mcp = FastMCP("AdaptizeFuzzAgent", prompt=CTF_RECIPE)

# Register your tools
register_tools(mcp)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
