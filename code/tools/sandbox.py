from smolagents import Tool

class ExecuteCommandTool(Tool):
    name = "execute_command_in_sandbox"
    description = "Executes a bash command in a restricted sandbox environment and returns the raw output."
    inputs = {
        "command": {
            "type": "string",
            "description": "The command to run in the sandbox."
        }
    }
    output_type = "string"

    def forward(self, command: str) -> str:
        """
        Simulate command execution in a sandbox.
        In a real scenario, this would use a secure container/subprocess.
        """
        return f"Simulated output for command: {command}"
