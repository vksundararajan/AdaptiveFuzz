from smolagents import CodeAgent, Model
from typing import List

def get_orchestrator_agent(model: Model) -> CodeAgent:
    """
    AdaptiveFuzz (Orchestrator): Dispatches tasks to executors, checks constraints with StateMonitor.
    It can act as a Manager agent in smolagents, distributing work to managed agents.
    """

    agent = CodeAgent(
        tools=[],
        model=model,
        name="orchestrator",
        description="The main orchestrator of AdaptiveFuzz. Dispatches tasks and manages flow."
    )
    return agent
