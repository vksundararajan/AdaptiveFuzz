import json
from typing import Any, Callable, Dict
from state import AdaptiveState
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import interrupt
from to_prompt import h_response, b_message, show_state

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
        print(show_state(state))

        return {
            TO_LOOP: False,
            STRATEGIES: [],
            CYCLE: state.get(CYCLE, 0) + 1,
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
        """Execute tasks using MCP tools and record results."""
        print(show_state(state))
        
        # Add target IP context for the LLM
        from langchain_core.messages import SystemMessage
        context_msg = SystemMessage(content=f"Target IP Address: {state.get('target_ip', 'N/A')}")
        
        messages = b_message(
            list(state[RECON_EXECUTOR_MESSAGES])
            + [context_msg]
            + list(state[PENDING_TASKS])
        )
        
        # Check if we have ToolMessages in the conversation (meaning tools were just executed)
        from langchain_core.messages import ToolMessage
        has_tool_results = any(isinstance(m, ToolMessage) for m in messages)
        
        # If we already have tool results, force structured output instead of allowing more tool calls
        if has_tool_results:
            print("🅰  Recon Executor (processing tool results)")
            # Force structured output after tools have been executed
            # Use plain LLM (not with_structured_output) to avoid function call format issues
            prompt = HumanMessage(content="""Based on the tool execution results above, provide your response as a JSON object with these exact fields:
{
  "pending_tasks": [array of task objects with task_id, description, and status fields - update status to "completed" for executed tasks],
  "executed_commands": [array of objects with "command" and "output" fields for each command that was executed]
}

Return ONLY the JSON object, nothing else.""")
            response = llm.invoke(messages + [prompt])
            # Parse the JSON from the response
            try:
                import re
                # Extract JSON from response (handle cases where LLM adds extra text)
                content = response.content
                # Try to find JSON block
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    ai_response = json.loads(json_match.group(0))
                else:
                    ai_response = json.loads(content)
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"⚠️  Failed to parse JSON response: {e}")
                print(f"Response content: {response.content[:200]}")
                # Fallback: use with_structured_output as last resort
                ai_response = llm.with_structured_output(response_t[RECON_EXECUTOR]).invoke(messages + [prompt])
        else:
            # First time - invoke the model with tools
            response = model_with_tools.invoke(messages)
            
            # Check if the response contains tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # If there are tool calls, return the response and let the graph handle tool execution
                next_messages = list(state.get(RECON_EXECUTOR_MESSAGES, []))
                next_messages.append(response)
                print("🅰  Recon Executor (calling tools)")
                return {
                    RECON_EXECUTOR_MESSAGES: next_messages,
                }
            
            # No tool calls, try to parse response for structured output
            try:
                if isinstance(response.content, str):
                    ai_response = json.loads(response.content)
                else:
                    ai_response = response.content
            except (json.JSONDecodeError, AttributeError):
                # If parsing fails, ask for structured output explicitly
                structured_messages = messages + [response]
                structured_messages.append(HumanMessage(content="Please provide your response in the required JSON format with 'pending_tasks' and 'executed_commands' fields."))
                ai_response = llm.with_structured_output(response_t[RECON_EXECUTOR]).invoke(structured_messages)

        updated_tasks = ai_response.get("pending_tasks", state[PENDING_TASKS])
        newly_completed = [task for task in updated_tasks if task.get("status") == "completed"]
        pending_tasks = [task for task in updated_tasks if task.get("status") != "completed"]
        completed_tasks = list(state[COMPLETED_TASKS]) + newly_completed

        next_messages = list(state.get(RECON_EXECUTOR_MESSAGES, []))
        # Append the response to messages (response variable exists in both branches)
        if 'response' in locals():
            next_messages.append(response)

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
        
        # Check if we have ToolMessages in the conversation (meaning tools were just executed)
        from langchain_core.messages import ToolMessage
        has_tool_results = any(isinstance(m, ToolMessage) for m in messages)
        
        # If we already have tool results, force structured output instead of allowing more tool calls
        if has_tool_results:
            print("🅰  Result Interpreter (processing tool results)")
            # Force structured output after tools have been executed
            # Use plain LLM to avoid function call format issues
            prompt = HumanMessage(content="""Based on the command outputs and any tool results above, provide your response as a JSON object with this exact field:
{
  "findings": [array of finding objects, each with "summary" and optionally "details" dict]
}

Return ONLY the JSON object, nothing else.""")
            response = llm.invoke(messages + [prompt])
            # Parse the JSON from the response
            try:
                import re
                # Extract JSON from response
                content = response.content
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    ai_response = json.loads(json_match.group(0))
                else:
                    ai_response = json.loads(content)
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"⚠️  Failed to parse JSON response: {e}")
                print(f"Response content: {response.content[:200]}")
                # Fallback
                ai_response = llm.with_structured_output(response_t[RESULT_INTERPRETER]).invoke(messages + [prompt])
        else:
            # First time - invoke the model with tools
            response = model_with_tools.invoke(messages)
            
            # Check if the response contains tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # If there are tool calls, return the response and let the graph handle tool execution
                next_messages = list(state[RESULT_INTERPRETER_MESSAGES])
                next_messages.append(response)
                print("🅰  Result Interpreter (calling tools)")
                return {
                    RESULT_INTERPRETER_MESSAGES: next_messages,
                }
            
            # No tool calls, so parse the response for structured output
            try:
                if isinstance(response.content, str):
                    ai_response = json.loads(response.content)
                else:
                    ai_response = response.content
            except (json.JSONDecodeError, AttributeError):
                # If parsing fails, ask for structured output explicitly
                structured_messages = messages + [response]
                structured_messages.append(HumanMessage(content="Please provide your response in the required JSON format with 'findings' field."))
                ai_response = llm.with_structured_output(response_t[RESULT_INTERPRETER]).invoke(structured_messages)

        next_messages = list(state[RESULT_INTERPRETER_MESSAGES])
        # Append the response to messages (response variable exists in both branches)
        if 'response' in locals():
            next_messages.append(response)

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
            executed_commands=state.get(EXECUTED_COMMANDS, []),
        )

        from_human = interrupt(summary)  # will be the resume value when resumed

        human_message = None
        val = from_human.get("human_reply")
        human_message = val

        messages = list(state.get(HUMAN_IN_LOOP_MESSAGES, []))
        messages.append(HumanMessage(content=human_message))

        return {
            TO_LOOP: True,
            FUZZ_ID: state.get(FUZZ_ID),
            USER_QUERY: human_message or state.get(USER_QUERY),
            HUMAN_IN_LOOP_MESSAGES: messages,
            LAST_UPDATE_TS: update_ts(),
        }

    return human_in_loop_node


