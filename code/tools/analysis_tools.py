import os
import json
import aiohttp
import asyncio
import asyncio
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
mcp = FastMCP("Analysis Tools")


@mcp.tool()
async def web_search(query: str, num_results: int = 5):
    search_api = os.getenv("GOOGLE_SEARCH_API")
    engine_id = os.getenv("SEARCH_ENGINE_ID")
    
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        'key': search_api,
        'cx': engine_id,
        'q': query,
        'num': num_results
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            response_json = await response.json()
            if 'items' in response_json:
                search_results_text = "\n".join(
                    f"Snippet: {item['snippet']}\nLink: {item['link']}"
                    for item in response_json['items']
                )

    combined_input = f"Query: {query}\nSearch Results:\n{search_results_text}"
    return combined_input

    
if __name__ == "__main__":
    mcp.run(transport="stdio")
    