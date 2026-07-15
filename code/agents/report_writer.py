from smolagents import ToolCallingAgent, Model
from tools.rag_tools import ReadFromRAGTool

def get_report_writer_agent(model: Model) -> ToolCallingAgent:
    """
    Report Writer Agent: Reads context from RAG and delivers the final report to the user.
    """

    read_tool = ReadFromRAGTool()
    
    agent = ToolCallingAgent(
        tools=[read_tool],
        model=model,
        name="report_writer",
        description="Reads from the Knowledge Base and compiles a final report."
    )
    return agent
