from smolagents import ToolCallingAgent, Model
from tools.rag_tools import WriteToRAGTool

def get_perceptor_agent(model: Model) -> ToolCallingAgent:
    """
    Perceptor Agent: Parses raw sandbox output, cleans data, and writes to RAG.
    """

    write_tool = WriteToRAGTool()
    
    agent = ToolCallingAgent(
        tools=[write_tool],
        model=model,
        name="perceptor",
        description="Parses raw data and writes cleaned insights into the Knowledge Base."
    )
    return agent
