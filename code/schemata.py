from typing import List, Dict, Literal, Optional
from pydantic import BaseModel, Field


class Task(BaseModel):
    task_id: int = Field(description="A unique identifier for the task.")
    task: str = Field(description="A description of the task.")
    status: Literal["Pending", "Completed", "Failed"] = Field(description="The current status of the task.")
    results: Optional[str] = Field(default=None, description="The results of the task, if completed.")


class result(BaseModel):
    command: str = Field(description="The command that was executed.")
    output: str = Field(description="The output of the executed command.")


class conversational_handler_schema(BaseModel):
    tasks: List[Task] = Field(description="A list of small recon tasks.")
    is_inappropriate: bool = Field(description="A boolean indicating if the content is inappropriate.")


class recon_executor_schema(BaseModel):
    tasks: List[Task] = Field(description="A list of pending recon tasks.")


class result_interpreter_schema(BaseModel):
    findings: List[str] = Field(description="A list of concise, human-readable security findings derived from the tool outputs.")


class strategy_advisor_schema(BaseModel):
    strategies: List[str] = Field(description="A list of exactly three prioritized, strategic next steps for the penetration test.")