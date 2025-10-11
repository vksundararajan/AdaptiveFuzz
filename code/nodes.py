import json
import uuid
from langgraph.types import interrupt
from langchain_core.tools import BaseTool
from typing import Any, Callable, Dict, List
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from tools import call_tools
from state import AdaptiveState
from to_prompt import h_response
from state import initialize_adaptive_state
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
    strategy_advisor_schema,
)


def make_rp_node(config: Dict[str, Any]):
    def request_parser_node(state: AdaptiveState) -> Dict[str, Any]:
        fuzz_id = str(uuid.uuid4())
        
        # target_ip = interrupt("📌  AdaptiveFuzz: Target IP")
        # user_query = interrupt("Your assistant is coming online... \n Ask Anything!")
        
        target_ip = "8.8.8.8"
        user_query = "check this ip is reachable and ready for pentesting"
        
        i_state = initialize_adaptive_state(
            fuzz_id=fuzz_id,
            target_ip=target_ip,
            user_query=user_query,
            conversational_handler=CONVERSATIONAL_HANDLER,
            recon_executor=RECON_EXECUTOR,
            result_interpreter=RESULT_INTERPRETER,
            strategy_advisor=STRATEGY_ADVISOR,
        )
        
        return i_state
    
    return request_parser_node


def make_ch_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def conversational_handler_node(state: AdaptiveState) -> Dict[str, Any]:
        """Plan reconnaissance tasks from the user query."""
        messages = [
            *state.get(CONVERSATIONAL_HANDLER_MESSAGES, []),
            HumanMessage(content="Here is the query, please help me solve the pentest tasks.."),
            *state.get(HUMAN_IN_LOOP_MESSAGES, [])
        ]

        response_dict = {
            "is_inappropriate": False,
            "pending_tasks": [
                {"task": "Check the ip is reachable", "status": "Pending"},
            ]
        }
        # ai_response = llm.with_structured_output(conversational_handler_schema).invoke(messages)
        # response_dict = ai_response.model_dump()

        next_messages = list(state[CONVERSATIONAL_HANDLER_MESSAGES])
        next_messages.append(AIMessage(content=json.dumps(response_dict)))
        
        u_state = {
            TO_LOOP: False,
            CYCLE: state.get(CYCLE, 0) + 1,
            PENDING_TASKS: response_dict.get(PENDING_TASKS, state.get(PENDING_TASKS, [])),
            IS_INAPPROPRIATE: response_dict.get(IS_INAPPROPRIATE, state.get(IS_INAPPROPRIATE, [])),
            CONVERSATIONAL_HANDLER_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }
        
        return u_state

    return conversational_handler_node


def make_re_node(llm_model: str, tools: List[BaseTool]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {tool.name: tool for tool in tools}

    async def recon_executor_node(state: AdaptiveState) -> Dict[str, Any]:
        """Execute tasks using MCP tools and record results (stub)."""
        tasks = state.get(PENDING_TASKS, [])
        
        if tasks:
            tasks_str = "\n".join([f"- {task.get('task', 'No description')}" for task in tasks])
        else:
            tasks_str = "No pending tasks."
        
        prompt = (
            "You are an expert penetration tester. Your goal is to execute the reconnaissance tasks "
            f"listed below against the target IP: {state.get(TARGET_IP)}.\n\n"
            "Review the following pending tasks and use ONLY the provided tools to accomplish them:\n"
            f"{tasks_str}\n\n"
            "If there are no pending tasks, do not call any tools and respond with an empty tool call list."
        )
        
        messages = [
            *state.get(RECON_EXECUTOR_MESSAGES, []),
            HumanMessage(content=prompt)
        ]
        
        # ai_response = {
        #     "pending_tasks": [
        #         {"task": "Check the ip is reachable", "status": "Completed"},
        #     ],
        #     "executed_commands": [
        #         {"input": "ping 8.8.8.8", "output": "64 bytes from 8.8.8.8: icmp_seq=0 ttl=118 time=23.224 ms"}
        #     ]
        # }
        ai_response = await llm_with_tools.ainvoke(messages)
        executed_commands = list(state.get(EXECUTED_COMMANDS, []))
        
        updated_commands, tool_messages = await call_tools(
            ai_response=ai_response,
            tool_map=tool_map,
            io=executed_commands
        )

        next_messages = list(state[RECON_EXECUTOR_MESSAGES])
        next_messages.append(ai_response)
        if tool_messages:
            next_messages.extend(tool_messages)
            
        completed_tasks = list(state.get(COMPLETED_TASKS, [])) + state[PENDING_TASKS]
        pending_tasks = []

        u_state = {
            PENDING_TASKS: pending_tasks,
            COMPLETED_TASKS: completed_tasks,
            EXECUTED_COMMANDS: updated_commands,
            RECON_EXECUTOR_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }
       
        return u_state

    return recon_executor_node


def make_ri_node(llm_model: str, tools: List[BaseTool]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    llm_with_tools = llm.bind_tools(tools)
    tool_map = {tool.name: tool for tool in tools}

    async def result_interpreter_node(state: AdaptiveState) -> Dict[str, Any]:
        """Synthesize evidence and use analysis tools to generate findings."""
        executed_str = "\n".join(
            [f"Input: {cmd.get('input', '')}\nOutput: {cmd.get('output', '')}" for cmd in state.get(EXECUTED_COMMANDS, [])]
        )
        completed_tasks_str = "\n".join(
            [f"- {task.get('task', '')}" for task in state.get(COMPLETED_TASKS, [])]
        )

        prompt = (
            f"Please analyze the following data from a penetration test reconnaissance phase.\n\n"
            f"Original User Query:\n{state.get(USER_QUERY)}\n\n"
            f"Completed Tasks:\n{completed_tasks_str}\n\n"
            f"Previously Executed Commands and their Outputs:\n---\n{executed_str}\n---\n\n"
            "Your task is to use your specialized tools (like lookup_cve, search_exploitdb) to dig deeper into these results. "
            "Based on the outputs, decide which analysis tools to run next to find vulnerabilities or gather more intelligence."
        )

        messages = [
            *state.get(RESULT_INTERPRETER_MESSAGES, []),
            HumanMessage(content=prompt),
        ]

        ai_response = await llm_with_tools.ainvoke(messages)
        current_commands = list(state.get(EXECUTED_COMMANDS, []))
        updated_commands, tool_messages = await call_tools(
            ai_response=ai_response,
            tool_map=tool_map,
            io=current_commands
        )
        
        newly_executed = updated_commands[len(current_commands):]
        new_findings = [cmd.get('output', 'No output.') for cmd in newly_executed]

        all_findings = list(state.get(FINDINGS, [])) + new_findings
        
        next_messages = list(state.get(RESULT_INTERPRETER_MESSAGES, []))
        next_messages.append(ai_response)
        if tool_messages:
            next_messages.extend(tool_messages)
        
        u_state = {
            FINDINGS: all_findings,
            EXECUTED_COMMANDS: updated_commands, 
            RESULT_INTERPRETER_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }

        return u_state

    return result_interpreter_node


def make_sa_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def strategy_advisor_node(state: AdaptiveState) -> Dict[str, Any]:
        """Recommend next-cycle strategies and policy tweaks."""
        findings_str = "\n".join([f"- {finding}" for finding in state.get(FINDINGS, [])])
        executed_str = "\n".join(
            [f"Input: {cmd.get('input', '')}\nOutput: {cmd.get('output', '')}\n---" for cmd in state.get(EXECUTED_COMMANDS, [])]
        )
        completed_tasks_str = "\n".join(
            [f"- {task.get('task', '')}" for task in state.get(COMPLETED_TASKS, [])]
        )

        prompt = (
            "You are a security strategy advisor. Based on the complete reconnaissance data below, "
            "please devise the next three logical steps for this penetration test.\n\n"
            f"Key Findings:\n{findings_str}\n\n"
            f"Completed Tasks:\n{completed_tasks_str}\n\n"
            f"Full Command History:\n{executed_str}\n\n"
            "Provide your analysis and recommended strategies in the required JSON format."
        )

        messages = [
            *state.get(STRATEGY_ADVISOR_MESSAGES, []),
            HumanMessage(content=prompt),
        ]
        
        ai_response = llm.with_structured_output(strategy_advisor_schema).invoke(messages)
        # ai_response = {
        #     "strategies": [
        #     "1. Since the ip is reachable, we can start nmap scan to check the open ports",
        #     "2. Or we can check the what CMS is running in HTTP",
        #     "3. Or We can check is there any files we can find inside ftp"
        #     ]
        # }

        response_dict = ai_response.model_dump()

        next_messages = list(state.get(STRATEGY_ADVISOR_MESSAGES, []))
        next_messages.append(AIMessage(content=json.dumps(response_dict)))
        
        # 4. Update the state with the list of strategy objects
        u_state = {
            STRATEGIES: response_dict.get(STRATEGIES, []),
            STRATEGY_ADVISOR_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }

        return u_state

    return strategy_advisor_node


def make_hr_node() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def human_in_loop_node(state: AdaptiveState) -> Dict[str, Any]:
        """Pause for human review and input."""
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
            FUZZ_ID: state.get(FUZZ_ID),
            LAST_UPDATE_TS: update_ts(),
            TARGET_IP: state.get(TARGET_IP),
            USER_QUERY: human_message or state.get(USER_QUERY, ""),
            HUMAN_IN_LOOP_MESSAGES: messages,
        }
        
        return u_state

    return human_in_loop_node


