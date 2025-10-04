"""
Secure MCP Tools for AdaptiveFuzz
Provides controlled terminal execution with multi-layer security mechanisms
"""

import subprocess
import json
import yaml
import re
from typing import List, Dict
from paths import COMMANDS_CONFIG_PATH


class TerminalExecutor:
    """Simple terminal executor with command history"""
    
    def __init__(self):
        self.history: List[Dict] = []
    
    def execute_command(self, command: str) -> str:
        """Execute a shell command and return the output"""
        # Load config
        with open(COMMANDS_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        # Security check: Validate against blacklist patterns
        for pattern in config['blacklist_patterns']:
            if re.search(pattern, command, re.IGNORECASE):
                blocked_msg = f"🚫 COMMAND BLOCKED\n\nCommand matched blacklist pattern: {pattern}\n\nThis command is not allowed for security reasons."
                self.history.append({
                    "command": command,
                    "output": blocked_msg,
                    "return_code": -1,
                    "blocked": True
                })
                return blocked_msg
        
        try:
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=config['limits']['command_timeout']
            )
            
            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]\n{result.stderr}"
            
            # Store in history
            self.history.append({
                "command": command,
                "output": output,
                "return_code": result.returncode,
                "blocked": False
            })
            
            return output if output else "Command executed successfully (no output)"
            
        except subprocess.TimeoutExpired:
            error_msg = f"⏱️ TIMEOUT: Command exceeded {config['limits']['command_timeout']}s"
            self.history.append({
                "command": command,
                "output": error_msg,
                "return_code": -1,
                "blocked": False
            })
            return error_msg
            
        except Exception as e:
            error_msg = f"❌ ERROR: {str(e)}"
            self.history.append({
                "command": command,
                "output": error_msg,
                "return_code": -1,
                "blocked": False
            })
            return error_msg
    
    def get_history(self) -> str:
        """Get all executed commands and their results"""
        return json.dumps(self.history, indent=2)


# Singleton instance
_executor = TerminalExecutor()


def register_tools(mcp):
    """Register MCP tools"""
    
    @mcp.tool()
    def secure_executor(command: str) -> str:
        """
        Execute a shell command in the terminal and return the output.
        
        Args:
            command: Shell command to execute
            
        Returns:
            Command output or error message
            
        Examples:
            {"command": "whoami"}
            {"command": "ls -la"}
            {"command": "curl -I http://example.com"}
        """
        return _executor.execute_command(command)
    
    @mcp.tool()
    def get_executor_history() -> str:
        """
        Get the history of all previously executed commands and their results.
        
        Returns:
            JSON array of command history with outputs and return codes
        """
        return _executor.get_history()
    
    @mcp.tool()
    def get_allowed_commands() -> str:
        """
        Get the list of allowed/safe commands for pentesting operations.
        
        Returns:
            JSON object with safe commands list from configuration
        """
        with open(COMMANDS_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        return json.dumps({
            "system_commands": sorted(config['system_commands']),
            "pentest_commands": sorted(config['pentest_commands']),
            "note": "These are whitelisted commands for pentesting operations"
        }, indent=2)

