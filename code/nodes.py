import json
import uuid
from langgraph.types import interrupt
from langchain_core.tools import BaseTool
from typing import Any, Callable, Dict, List
from langchain_core.messages import HumanMessage, SystemMessage

from state import AdaptiveState
from tools import call_tools
from to_prompt import h_response
from to_help import get_llm, load_yaml_file
from paths import PROMPTS_CONFIG_PATH
from schemata import (
    conversational_handler_schema, 
    result_interpreter_schema,
    strategy_advisor_schema,
)
from consts import (
    TASKS,
    FINDINGS,
    STRATEGIES,
    TO_LOOP,
    IS_INAPPROPRIATE,
    TARGET_IP,
    USER_QUERY,
)


def make_ch_node(llm_model: str, prompt: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def conversational_handler_node(state: AdaptiveState) -> Dict[str, Any]:
        """Plan reconnaissance tasks from the user query."""
        
        target_ip = interrupt("📌  AdaptiveFuzz: Target IP")
        user_query = interrupt("Your assistant is coming online... \n Ask Anything!")
        
        # target_ip = "8.8.8.8"
        # user_query = "Check the open ports in the target ip and find vulnerabilities"
        
        messages = [
            SystemMessage(content=
                "Imagine you are a part of reconnisance phase of penetration testing team." + "\n"
                + "Your goal is to break down the user's high-level request into a series of smaller, manageable tasks." + "\n"
                + "You should only create tasks that can be accomplished using the available tools." + "\n"
                + "If the request is inappropriate, respond accordingly." + "\n"
                + "Available tools are: " + "\n"
                + "1. port_scanner: A tool to scan open ports on a target IP address." + "\n"
                + "2. web_search: A tool to perform web searches for gathering information." + "\n"
                + "When creating tasks, ensure they are specific, actionable, and relevant to the user's request." + "\n"
                + "Do not create tasks that cannot be accomplished with the available tools." + "\n"
                + "If the request is inappropriate, respond with is_inappropriate as true and do not create any tasks." + "\n"            
            ),
            HumanMessage(content= "\n"
                "Here is the target IP Address: " + target_ip + "\n"
                + "Here is the user query: " + user_query 
            )
        ]

        ai_response = llm.with_structured_output(conversational_handler_schema).invoke(messages)
        response = ai_response.model_dump()
        
        tasks = response.get(TASKS, [])
        is_inappropriate = response.get(IS_INAPPROPRIATE, True)
        for task in tasks: task["task_id"] = str(uuid.uuid4())
        
        return {
            TO_LOOP: False,
            TASKS: tasks,
            TARGET_IP: target_ip,
            USER_QUERY: list(user_query),
            IS_INAPPROPRIATE: is_inappropriate
        }

    return conversational_handler_node


def make_re_node(llm_model: str, prompt: str, tools: List[BaseTool]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {tool.name: tool for tool in tools}

    async def recon_executor_node(state: AdaptiveState) -> Dict[str, Any]:
        """Execute tasks using MCP tools and record results (stub)."""
        tasks = state.get(TASKS, [])
        
        messages = [
            SystemMessage(content=prompt + "\n"
                + "Your goal is to execute the pending tasks using the available tools." + "\n"
                + "Available tools are: " + "\n"
                + "port_scanner: A tool to scan open ports on a target IP address." + "\n"
                + "Note: While sending tool call, include for which task you are sending the tool call in response. (task_id)" + "\n"
            ),
            HumanMessage(content= "\n"
                "Here are the pending tasks:" + json.dumps(tasks) + "\n"
                + "Solve this by executing the necessary tools." + "\n"
            ),
        ]

        ai_tool_call = await llm_with_tools.ainvoke(messages)
        tool_results = await call_tools(ai_tool_call, tool_map)
        
        by_task_id = {result.get("task_id"): result for result in tool_results}
        for task in tasks:
            result = by_task_id.get(task.get("task_id"))
            if result:
                task["status"] = "Completed"
                task["results"] = result.get("output")
        
        messages = [
            SystemMessage(content=prompt + "\n"
                + "Your goal is to execute the pending tasks using the available tools." + "\n"
                + "Available tools are: " + "\n"
                + "web_search: A tool to perform web searches for gathering information." + "\n"
                + "Based on the tool outputs, i need to create some findings like" + "\n"
                + "If one the task results contains port scan results, " + "\n"
                + "then you can check what kind of scans we can do next on that open port using web_search tool" + "\n"
                + "If you want to do web search regarding anything like this, please do so." + "\n"
                + "web_search MCP tool is available"
            ),
            HumanMessage(content=prompt+ "\n"
                + "Now here are the tasks we already completed: " + json.dumps([task for task in tasks if task["status"] == "Completed"]) + "\n"
                + "Here are the tasks we couldn't complete: " + json.dumps([task for task in tasks if task["status"] != "Completed"]) + "\n"
                + "Here are the executed request inputs we sent: " + ' '.join([item['input'] for item in tool_results]) + "\n"
                + "Here are the request outputs we received: " + ' '.join([item['output'] for item in tool_results]) + "\n"
            )
        ]
        
        ai_tool_call = await llm_with_tools.ainvoke(messages)
        tool_results = await call_tools(ai_tool_call, tool_map)
        
        by_task_id = {result.get("task_id"): result for result in tool_results}
        for task in tasks:
            result = by_task_id.get(task.get("task_id"))
            if result:
                task["web_info"] = result.get("output")
        
        return {
            TASKS: tasks
        }

    return recon_executor_node


def make_ri_node(llm_model: str, prompt: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    
    async def result_interpreter_node(state: AdaptiveState) -> Dict[str, Any]:
        """Interpret tool results and extract findings (stub)."""
        tasks = state.get(TASKS, [])
        
        messages = [
            SystemMessage(content=prompt
                + "Your goal is to analyze the results of the executed tasks and extract concise, human-readable security findings." + "\n"
                + "Focus on identifying potential vulnerabilities, misconfigurations, or any other security-relevant information." + "\n"
                + "If no significant findings are present, return an empty list." + "\n"
            ),
            HumanMessage(content= "\n"
                + "Here are the executed tasks with their results:" + json.dumps(tasks) + "\n"
                + "Based on the tool outputs, extract and list the most relevant security findings." + "\n"
            ),
        ]
        
        ai_response = llm.with_structured_output(result_interpreter_schema).invoke(messages)
        response = ai_response.model_dump()
        findings = response.get(FINDINGS, [])
        
        return {
            FINDINGS: findings
        }

    return result_interpreter_node


def make_sa_node(llm_model: str, prompt: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    
    def strategy_advisor_node(state: AdaptiveState) -> Dict[str, Any]:
        """Advise on strategic next steps (stub)."""
        
        messages = [
            SystemMessage(content=prompt + "\n"
                + "Your goal is to provide strategic next steps for the penetration test based on the current findings." + "\n"
                + "Consider the overall security posture of the target and suggest actions that would be most impactful." + "\n"
                + "Provide exactly three prioritized strategies."
            ),
            HumanMessage(content= "\n"
                + "Here are the current findings:" + json.dumps(state.get(FINDINGS, [])) + "\n"
                + "Based on these findings, suggest three strategic next steps for the penetration test." + "\n"
            )
        ]
        
        ai_response = llm.with_structured_output(strategy_advisor_schema).invoke(messages)
        response = ai_response.model_dump()
        strategies = response.get(STRATEGIES, [])
         
        return {
            STRATEGIES: strategies
        }

    return strategy_advisor_node


def make_hr_node() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def human_in_loop_node(state: AdaptiveState) -> Dict[str, Any]:
        """Pause for human review and input."""
        summary = h_response(
            completed_tasks=state.get(TASKS, []),
            findings=state.get(FINDINGS, []),
            strategies=state.get(STRATEGIES, []),
        )

        from_human = interrupt(summary)  # will be the resume value when resumed
        
        u_state = {
            TO_LOOP: True if from_human else False,
            USER_QUERY: list(from_human)
        }
        
        return u_state

    return human_in_loop_node


