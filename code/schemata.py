conversational_handler_schema = {
    "title": "conversational_handler",
    "description": "Track pending moderation tasks and appropriateness flag.",
    "type": "object",
    "properties": {
        "pending_tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "completed", "failed"]}
                },
                "required": ["task_id", "description", "status"],
                "additionalProperties": False
            }
        },
        "is_inappropriate": {"type": "boolean"}
    },
    "required": ["pending_tasks", "is_inappropriate"],
    "additionalProperties": False
}

recon_executor_schema = {
    "title": "recon_executor",
    "description": "Record recon tasks and executed command outputs.",
    "type": "object",
    "properties": {
        "pending_tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "completed", "failed"]}
                },
                "required": ["task_id", "description", "status"],
                "additionalProperties": False
            }
        },
        "executed_commands": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "output": {"type": "string"}
                },
                "required": ["command", "output"],
                "additionalProperties": False
            }
        }
    },
    "required": ["pending_tasks", "executed_commands"],
    "additionalProperties": False
}

result_interpreter_schema = {
    "title": "result_interpreter",
    "description": "Summarise and detail findings from recon.",
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "details": {
                        "type": "object",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "additionalProperties": False
            }
        }
    },
    "required": ["findings"],
    "additionalProperties": False
}

strategy_advisor_schema = {
    "title": "strategy_advisor",
    "description": "Advise next steps based on results.",
    "type": "object",
    "properties": {
        "strategies": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["strategies"],
    "additionalProperties": False
}


response_t = {
    "conversational_handler": conversational_handler_schema,
    "recon_executor": recon_executor_schema,
    "result_interpreter": result_interpreter_schema,
    "strategy_advisor": strategy_advisor_schema
}

