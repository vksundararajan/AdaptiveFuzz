from smolagents import ToolCallingAgent, Model
from tools.sandbox import ExecuteCommandTool

def get_executor_agent(model: Model) -> ToolCallingAgent:
    """
    Executor Agent: Executes commands in the sandbox environment.
    """

    sandbox_tool = ExecuteCommandTool()
    
    agent = ToolCallingAgent(
        tools=[sandbox_tool],
        model=model,
        name="executor",
        description="Executes tasks by running commands in a sandbox."
    )
    return agent
