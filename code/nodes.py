import json
from typing import Any, Callable, Dict
from state import AdaptiveState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt
from to_prompt import h_response, _s_state
from langgraph.prebuilt import create_react_agent

from consts import (
    CONVERSATIONAL_HANDLER_MESSAGES,
    RECON_EXECUTOR_MESSAGES,
    RESULT_INTERPRETER_MESSAGES,
    STRATEGY_ADVISOR_MESSAGES,
    HUMAN_IN_LOOP_MESSAGES,

    PENDING_TASKS,
    EXECUTED_COMMANDS,
    FINDINGS,
    CYCLE,
    LAST_UPDATE_TS,
    STRATEGIES,
    TO_LOOP,
    IS_INAPPROPRIATE,
    FUZZ_ID,
    TARGET_IP,
    COMPLETED_TASKS,
    USER_QUERY,

    CONVERSATIONAL_HANDLER,
    RECON_EXECUTOR,
    RESULT_INTERPRETER,
    STRATEGY_ADVISOR,
    HUMAN_IN_LOOP,
)

from to_help import (
    get_llm,
    update_ts
)

from schemata import (
    conversational_handler_schema,
    strategy_advisor_schema
)


def make_ch_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def conversational_handler_node(state: AdaptiveState) -> Dict[str, Any]:
        """Plan reconnaissance tasks from the user query."""       
        messages = [
            list(state[CONVERSATIONAL_HANDLER_MESSAGES]),
            HumanMessage(content="Here is the query, please help me solve the pentest tasks.."),
            list(state[HUMAN_IN_LOOP_MESSAGES])
        ]

        # ai_response = llm.with_structured_output(conversational_handler_schema).invoke(messages)
        ai_response = {
            "is_inappropriate": False,
            "pending_tasks": [
                {"task": "Check the ip is reachable", "status": "Pending"},
            ]
        }

        next_messages = list(state[CONVERSATIONAL_HANDLER_MESSAGES])
        next_messages.append(AIMessage(content=json.dumps(ai_response)))
        
        u_state = {
            TO_LOOP: False,
            CYCLE: state.get(CYCLE, 0) + 1,
            PENDING_TASKS: ai_response.get(PENDING_TASKS, state.get(PENDING_TASKS, [])),
            IS_INAPPROPRIATE: ai_response.get(IS_INAPPROPRIATE, state.get(IS_INAPPROPRIATE, [])),
            CONVERSATIONAL_HANDLER_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }
        
        _s_state(u_state, "🅰  Conversational Handler")
        return u_state

    return conversational_handler_node


def make_re_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def recon_executor_node(state: AdaptiveState) -> Dict[str, Any]:
        """Execute tasks using MCP tools and record results (stub)."""        
        messages = [
            list(state[RECON_EXECUTOR_MESSAGES]),
            SystemMessage(content="Below is the Tasks set "),
            state.get(CYCLE, 0) + 1 ,
            list(state[PENDING_TASKS])
        ]
        
        # ai_response.tool_calls
        # ai_response = model_with_tools.ainvoke({"messages": messages})
        ai_response = {
            "pending_tasks": [
                {"task": "Check the ip is reachable", "status": "Completed"},
            ],
            "executed_commands": [
                {"input": "ping 8.8.8.8", "output": "64 bytes from 8.8.8.8: icmp_seq=0 ttl=118 time=23.224 ms"}
            ]
        }
        
        next_messages = list(state[RECON_EXECUTOR_MESSAGES])
        next_messages.append(AIMessage(content=json.dumps(ai_response)))
        updated_tasks = ai_response.get("pending_tasks", state[PENDING_TASKS])
        newly_completed = [task for task in updated_tasks if task.get("status") == "completed"]
        pending_tasks = [task for task in updated_tasks if task.get("status") != "completed"]
        completed_tasks = list(state.get(COMPLETED_TASKS, [])) + newly_completed

        u_state = {
            PENDING_TASKS: pending_tasks,
            COMPLETED_TASKS: completed_tasks,
            EXECUTED_COMMANDS: ai_response.get(EXECUTED_COMMANDS, state.get(EXECUTED_COMMANDS, [])),
            RECON_EXECUTOR_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }
        
        _s_state(u_state, "🅰  Recon Executor")        
        return u_state

    return recon_executor_node


def make_ri_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def result_interpreter_node(state: AdaptiveState) -> Dict[str, Any]:
        """Normalise execution evidence into findings."""
        messages = [
            list(state[RESULT_INTERPRETER_MESSAGES]),
            SystemMessage(content="Below is the commands we executed before and it's outputs"),
            list(state[EXECUTED_COMMANDS]),
            SystemMessage(content="Below are the completed and pending tasks"),
            list(state[COMPLETED_TASKS]),
            list(state[PENDING_TASKS])
        ]

        # ai_response = model_with_tools.ainvoke(messages)
        ai_response = {
            "findings" : [
                "1. The IP is reachable",
                "2. It is ready for pentesting"
            ]
        }
        
        next_messages = list(state[RESULT_INTERPRETER_MESSAGES])
        next_messages.append(AIMessage(content=json.dumps(ai_response)))
        
        u_state = {
            FINDINGS: ai_response.get(FINDINGS, state.get(FINDINGS, [])),
            RESULT_INTERPRETER_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }

        _s_state(u_state, "🅰  Result Interpreter")
        return u_state

    return result_interpreter_node


def make_sa_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def strategy_advisor_node(state: AdaptiveState) -> Dict[str, Any]:
        """Recommend next-cycle strategies and policy tweaks."""

        messages = [
            list(state[STRATEGY_ADVISOR_MESSAGES]),
            HumanMessage(content="Here are the findings I have donne:"),
            list(state[FINDINGS]),
            HumanMessage(content="Here are the commands I executed along with its output:"),
            list(state[EXECUTED_COMMANDS]),
            HumanMessage(content="Here are the completed and pending tasks:"),
            list(state[COMPLETED_TASKS]),
            list(state[PENDING_TASKS])
        ]
        # ai_response = llm.with_structured_output(strategy_advisor_schema).invoke(messages)
        ai_response = {
            "strategies": [
            "1. We can start nmap scan to check the open ports",
            "2. We can check the http is open or not by fetch the request",
            "3. We can check the ftp is open"
            ]
        }

        next_messages = list(state[STRATEGY_ADVISOR_MESSAGES])
        next_messages.append(AIMessage(content=json.dumps(ai_response)))
        
        u_state = {
            STRATEGIES: ai_response.get("strategies", state.get(STRATEGIES, [])),
            STRATEGY_ADVISOR_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }

        _s_state(u_state, "🅰  Strategy Advisor")
        return u_state

    return strategy_advisor_node


def make_hr_node() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def human_in_loop_node(state: AdaptiveState) -> Dict[str, Any]:
        """Pause for human review and input."""
        if not state.get(TARGET_IP):
            ip_from_human = interrupt("Target IP")
            from_human = interrupt("Ask anything!")
        else:
            summary = h_response(
                findings=state.get(FINDINGS, []),
                completed_tasks=state.get(COMPLETED_TASKS, []),
                pending_tasks=state.get(PENDING_TASKS, []),
                strategies=state.get(STRATEGIES, []),
            )

            from_human = interrupt(summary)  # will be the resume value when resumed

        human_message = None
        human_message = from_human

        messages = list(state.get(HUMAN_IN_LOOP_MESSAGES, []))
        messages.append(HumanMessage(content=human_message))
        
        u_state = {
            TO_LOOP: True,
            TARGET_IP: ip_from_human or state.get(TARGET_IP, ""),
            FUZZ_ID: state.get(FUZZ_ID),
            USER_QUERY: human_message or state.get(USER_QUERY, ""),
            HUMAN_IN_LOOP_MESSAGES: messages,
            LAST_UPDATE_TS: update_ts(),
        }
        
        _s_state(u_state, "🅰  Human IN Loop")
        return u_state

    return human_in_loop_node


