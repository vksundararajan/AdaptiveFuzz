import os
import aiohttp
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()
mcp = FastMCP("Analysis Tools")


@mcp.tool(tags={"web"})
async def web_search(query: str, task_id: str, num_results: int = 5):
    """
    Performs a web search using the Google Custom Search API and returns combined query and search results.
    Args:
        query (str): The search query.
        num_results (int): The number of search results to return.
        task_id (str): The ID of the task this search is for. (REQUIRED)
    Returns:
        str: The combined query and search results.
    """
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
    