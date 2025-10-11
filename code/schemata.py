from typing import List, Dict, Literal, Optional
from pydantic import BaseModel, Field


class Task(BaseModel):
    """Inner class defining the structure of a single task."""
    task: str = Field(description="A description of the task.")
    status: Literal["Pending", "Completed", "Failed"] = Field(
        description="The current status of the task."
    )


class Command(BaseModel):
    command: str = Field(description="The command that was executed.")
    output: str = Field(description="The output of the executed command.")


class conversational_handler_schema(BaseModel):
    """Class that defines the structure of the conversational handler."""
    pending_tasks: List[Task] = Field(description="A list of small recon tasks.")
    is_inappropriate: bool = Field(
        description="A boolean indicating if the content is inappropriate."
    )


class recon_executor_schema(BaseModel):
    """Class that defines the structure of the recon executor."""
    pending_tasks: List[Task] = Field(description="A list of pending recon tasks.")
    completed_tasks: List[Task] = Field(description="A list of completed recon tasks.")
    executed_commands: List[Command] = Field(description="A list of executed commands and its output.")


class result_interpreter_schema(BaseModel):
    """Class that defines the structure of the result interpreter."""
    findings: List[str] = Field(description="list your exploit findings.")


class strategy_advisor_schema(BaseModel):
    """Class that defines the structure of the strategy advisor."""
    strategies: List[str] = Field(description="list your strategies.")