from smolagents import CodeAgent, Model
import os

def get_interpreter_agent(model: Model) -> CodeAgent:
    """
    Interpreter Agent: Parses user prompt, sets scope & limits for the StateMonitor,
    and returns parsed details for the Orchestrator.
    """

    agent = CodeAgent(
        tools=[],
        model=model,
        name="interpreter",
        description="Parses user input, sets scope and limits, and prepares details for the orchestrator."
    )
    return agent
