import json
from typing import Any, Callable, Dict
from state import AdaptiveState
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import interrupt
from to_prompt import h_response, b_message, _s_state

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

from schemata import response_t
from langgraph.prebuilt import create_react_agent

from to_help import (
    get_llm,
    update_ts
)


def make_ch_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)

    def conversational_handler_node(state: AdaptiveState) -> Dict[str, Any]:
        """Plan reconnaissance tasks from the user query."""        
        messages = b_message(
            list(state[CONVERSATIONAL_HANDLER_MESSAGES])
            + list(state[HUMAN_IN_LOOP_MESSAGES])
        )

        ai_response = llm.with_structured_output(response_t[CONVERSATIONAL_HANDLER]).invoke(messages)
        next_messages = list(state[CONVERSATIONAL_HANDLER_MESSAGES])
        next_messages.append(AIMessage(content=json.dumps(ai_response)))
        
        u_state = {
            TO_LOOP: False,
            STRATEGIES: [],
            CYCLE: state.get(CYCLE, 0) + 1,
            PENDING_TASKS: ai_response.get("pending_tasks", state[PENDING_TASKS]),
            IS_INAPPROPRIATE: ai_response.get("is_inappropriate", state[IS_INAPPROPRIATE]),
            CONVERSATIONAL_HANDLER_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }
        
        _s_state(u_state, "🅰  Conversational Handler")
        return u_state

    return conversational_handler_node


def make_re_node(llm_model: str, tools: list) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    model_with_tools = create_react_agent(llm, tools)

    async def recon_executor_node(state: AdaptiveState) -> Dict[str, Any]:
        """Execute tasks using MCP tools and record results (stub)."""        
        messages = b_message(
            list(state[RECON_EXECUTOR_MESSAGES])
            + list(state[PENDING_TASKS])
        )
        
        # ai_response.tool_calls
        response = await model_with_tools.ainvoke({"messages": messages})
        print(response)
        final_message = response["messages"][-1]
        data = json.loads(final_message.content)
        updated_tasks = data.get("pending_tasks", state[PENDING_TASKS])
        executed_commands = data.get("executed_commands", state[EXECUTED_COMMANDS])
        newly_completed = [task for task in updated_tasks if task.get("status") == "completed"]
        pending_tasks = [task for task in updated_tasks if task.get("status") != "completed"]
        completed_tasks = list(state[COMPLETED_TASKS]) + newly_completed

        next_messages = list(state.get(RECON_EXECUTOR_MESSAGES, [])) + response["messages"]


        u_state = {
            PENDING_TASKS: pending_tasks,
            COMPLETED_TASKS: completed_tasks,
            EXECUTED_COMMANDS: executed_commands,
            RECON_EXECUTOR_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }
        
        _s_state(u_state, "🅰  Recon Executor")        
        return u_state

    return recon_executor_node


def make_ri_node(llm_model: str, tools: list) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    model_with_tools = llm.bind_tools(tools)

    def result_interpreter_node(state: AdaptiveState) -> Dict[str, Any]:
        """Normalise execution evidence into findings."""
        messages = b_message(
            list(state[RESULT_INTERPRETER_MESSAGES])
            + list(state[EXECUTED_COMMANDS])
            + list(state[COMPLETED_TASKS])
            + list(state[PENDING_TASKS])
        )
        ai_response = model_with_tools.with_structured_output(response_t[RESULT_INTERPRETER]).invoke(messages)

        next_messages = list(state[RESULT_INTERPRETER_MESSAGES])
        next_messages.append(AIMessage(content=json.dumps(ai_response)))
        
        u_state = {
            FINDINGS: ai_response.get("findings", state[FINDINGS]),
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

        messages = b_message(
            list(state[STRATEGY_ADVISOR_MESSAGES])
            + list(state[FINDINGS])
            + list(state[EXECUTED_COMMANDS])
            + list(state[COMPLETED_TASKS])
            + list(state[PENDING_TASKS])
        )
        ai_response = llm.with_structured_output(response_t[STRATEGY_ADVISOR]).invoke(messages)

        next_messages = list(state[STRATEGY_ADVISOR_MESSAGES])
        next_messages.append(AIMessage(content=json.dumps(ai_response)))
        
        u_state = {
            STRATEGIES: ai_response.get("strategies", state[STRATEGIES]),
            STRATEGY_ADVISOR_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }

        _s_state(u_state, "🅰  Strategy Advisor")
        return u_state

    return strategy_advisor_node


def make_hr_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def human_in_loop_node(state: AdaptiveState) -> Dict[str, Any]:
        """Pause for human review and input."""
        
        summary = h_response(
            findings=state[FINDINGS],
            completed_tasks=state.get(COMPLETED_TASKS, []),
            pending_tasks=state.get(PENDING_TASKS, []),
            strategies=state.get(STRATEGIES, []),
        )

        from_human = interrupt(summary)  # will be the resume value when resumed

        human_message = None
        val = from_human.get("human_reply")
        human_message = val

        messages = list(state.get(HUMAN_IN_LOOP_MESSAGES, []))
        messages.append(HumanMessage(content=human_message))
        
        u_state = {
            TO_LOOP: True,
            FUZZ_ID: state.get(FUZZ_ID),
            USER_QUERY: human_message or state.get(USER_QUERY),
            HUMAN_IN_LOOP_MESSAGES: messages,
            LAST_UPDATE_TS: update_ts(),
        }
        
        _s_state(u_state, "🅰  Human IN Loop")
        return u_state

    return human_in_loop_node


