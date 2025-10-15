import json
import uuid
import asyncio
from langgraph.types import interrupt
from langchain_core.tools import BaseTool
from typing import Any, Callable, Dict, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from state import AdaptiveState
from tools import call_tools
from to_prompt import h_response
from to_help import get_llm, load_yaml_file
from paths import PROMPTS_CONFIG_PATH
from schemata import (
    conversational_handler_schema, 
    recon_executor_schema, 
    strategy_advisor_schema
)
from consts import (
    TASKS,
    FINDINGS,
    STRATEGIES,
    TO_LOOP,
    IS_INAPPROPRIATE,
    TARGET_IP,
    COMPLETED_TASKS,
    USER_QUERY,

    CONVERSATIONAL_HANDLER,
    RECON_EXECUTOR,
    RESULT_INTERPRETER,
    STRATEGY_ADVISOR,
    HUMAN_IN_LOOP,
)


def make_ch_node(llm_model: str, prompt: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def conversational_handler_node(state: AdaptiveState) -> Dict[str, Any]:
        """Plan reconnaissance tasks from the user query."""
        
        # target_ip = interrupt("📌  AdaptiveFuzz: Target IP")
        # user_query = interrupt("Your assistant is coming online... \n Ask Anything!")
        
        target_ip = "8.8.8.8"
        user_query = "Check the open ports in the target ip and find vulnerabilities"
        
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content="Here is the query: " + user_query + ", and the target ip is " + target_ip),
        ]

        ai_response = llm.with_structured_output(conversational_handler_schema).invoke(messages)
        response = ai_response.model_dump()
        
        u_state = {
            TO_LOOP: False,
            TASKS: response.get(TASKS, state.get(TASKS, [])),
            IS_INAPPROPRIATE: response.get(IS_INAPPROPRIATE, state.get(IS_INAPPROPRIATE, [])),
        }
        
        print(u_state)
        return u_state

    return conversational_handler_node


def make_re_node(llm_model: str, prompt: str, tools: List[BaseTool]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {tool.name: tool for tool in tools}

    async def recon_executor_node(state: AdaptiveState) -> Dict[str, Any]:
        """Execute tasks using MCP tools and record results (stub)."""
        tasks = state.get(TASKS, [])
        
        messages = [
            SystemMessage(content=prompt + "\nBelow are the pending tasks:"),
            SystemMessage(content=json.dumps(tasks)),
            SystemMessage(content="\nSolve this by executing the necessary tools."),
            SystemMessage(content="While sending tool call, include for which task you are sending the tool call in response. (task_id)"),
        ]

        ai_tool_call = await llm_with_tools.ainvoke(messages)
        io = await call_tools(ai_tool_call, tool_map)
        
        message = [
            SystemMessage(content="Here are the tool calls and their results:"),
            SystemMessage(content=json.dumps(io)),
            SystemMessage(content="Update the status of the tasks based on the tool outputs."
                        + "If a task is completed, mark it as 'Completed' and include the results." + 
                        "If a task cannot be completed, mark it as 'Failed' and provide a reason."),
            SystemMessage(content="Return the updated list of tasks, here is the tasks: " + json.dumps(tasks)),
        ]
        
        ai_response = llm.with_structured_output(recon_executor_schema).invoke(messages)
        response = ai_response.model_dump()
        print(response)
        
        u_state = {
            TASKS: response.get(TASKS, state.get(TASKS, []))
        }
       
        print(u_state)
        return u_state

    return recon_executor_node


def make_ri_node(llm_model: str, tools: List[BaseTool]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    _ = get_llm(llm_model)
    async def result_interpreter_node(state: AdaptiveState) -> Dict[str, Any]:
        u_state = {}
        return u_state

    return result_interpreter_node


def make_sa_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    _ = get_llm(llm_model)
    def strategy_advisor_node(state: AdaptiveState) -> Dict[str, Any]:
        u_state = {}
        return u_state

    return strategy_advisor_node


def make_hr_node() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def human_in_loop_node(state: AdaptiveState) -> Dict[str, Any]:
        """Pause for human review and input."""
        summary = h_response(
            completed_tasks=state.get(COMPLETED_TASKS, []),
            pending_tasks=state.get(TASKS, []),
            findings=state.get(FINDINGS, []),
            strategies=state.get(STRATEGIES, []),
        )

        from_human = interrupt(summary)  # will be the resume value when resumed
        
        to_loop = state.get(TO_LOOP, False)
        if from_human is None:
            to_loop = True
        
        messages = list(state.get(USER_QUERY, []))
        messages.append(HumanMessage(content=from_human))
        
        u_state = {
            TO_LOOP: to_loop,
            USER_QUERY: messages
        }
        
        return u_state

    return human_in_loop_node


