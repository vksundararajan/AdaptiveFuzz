import json
from typing import Any, Callable, Dict
from state import AdaptiveState
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt
from to_prompt import h_response, b_message

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

        print("🅰  Conversational Handler")

        return {
            TO_LOOP: False,
            STRATEGIES: [],
            PENDING_TASKS: ai_response.get("pending_tasks", state[PENDING_TASKS]),
            IS_INAPPROPRIATE: ai_response.get("is_inappropriate", state[IS_INAPPROPRIATE]),
            CONVERSATIONAL_HANDLER_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }

    return conversational_handler_node


def make_re_node(llm_model: str, tools: list) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    llm = get_llm(llm_model)
    model_with_tools = llm.bind_tools(tools)

    def recon_executor_node(state: AdaptiveState) -> Dict[str, Any]:
        """Execute tasks using MCP tools and record results (stub)."""
        messages = b_message(
            list(state[RECON_EXECUTOR_MESSAGES])
            + list(state[PENDING_TASKS])
        )
        ai_response = model_with_tools.with_structured_output(response_t[RECON_EXECUTOR]).invoke(messages)

        updated_tasks = ai_response.get("pending_tasks", state[PENDING_TASKS])
        newly_completed = [task for task in updated_tasks if task.get("status") == "completed"]
        pending_tasks = [task for task in updated_tasks if task.get("status") != "completed"]
        completed_tasks = list(state[COMPLETED_TASKS]) + newly_completed

        next_messages = list(state.get(RECON_EXECUTOR_MESSAGES, []))
        next_messages.append(AIMessage(content=json.dumps(ai_response)))

        print("🅰  Recon Executor")

        return {
            PENDING_TASKS: pending_tasks,
            COMPLETED_TASKS: completed_tasks,
            EXECUTED_COMMANDS: ai_response.get("executed_commands", state[EXECUTED_COMMANDS]),
            RECON_EXECUTOR_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }

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

        print("🅰  Result Interpreter")

        return {
            FINDINGS: ai_response.get("findings", state[FINDINGS]),
            RESULT_INTERPRETER_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }

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

        print("🅰  Strategy Advisor")

        return {
            STRATEGIES: ai_response.get("strategies", state[STRATEGIES]),
            STRATEGY_ADVISOR_MESSAGES: next_messages,
            LAST_UPDATE_TS: update_ts(),
        }

    return strategy_advisor_node


def make_hr_node(llm_model: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    def human_in_loop_node(state: AdaptiveState) -> Dict[str, Any]:
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

        return {
            TO_LOOP: True,
            CYCLE: state.get(CYCLE, 0) + 1,
            FUZZ_ID: state.get(FUZZ_ID),
            USER_QUERY: human_message or state.get(USER_QUERY),
            HUMAN_IN_LOOP_MESSAGES: messages,
            LAST_UPDATE_TS: update_ts(),
        }

    return human_in_loop_node


