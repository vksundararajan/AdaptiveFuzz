import subprocess
import json
import re
from typing import List, Dict
import requests

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__))) 

from paths import CMD_CONFIG_PATH
from to_help import load_yaml_file
from mcp.server.fastmcp import FastMCP


class TerminalExecutor:
    """Simple terminal executor with command history"""
    
    def __init__(self):
        self.history: List[Dict] = []
    
    def execute_command(self, command: str) -> str:
        """Execute a shell command and return the output"""
        config = load_yaml_file(CMD_CONFIG_PATH)
        
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
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=config['limits']['command_timeout']
            )
            
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


_executor = TerminalExecutor()

mcp = FastMCP("Executor Tools")


@mcp.tool()
def secure_executor(command: str) -> str:
    """
    Executes shell commands with built-in security controls. Commands are validated against a blacklist 
    of dangerous patterns before execution. Has timeout protection and maintains execution history. 
    Use this for running pentesting tools like nmap, curl, nikto, or system commands.
    
    Args:
        command: Shell command to execute (validated against security blacklist)
        
    Returns:
        Command stdout/stderr output, or error/blocked message if command violates security rules
        
    Examples:
        {"command": "whoami"}
        {"command": "ls -la"}
        {"command": "curl -I http://example.com"}
    """
    return _executor.execute_command(command)


@mcp.tool()
def get_executor_history() -> str:
    """
    Retrieves the complete execution log of all commands run during this session. Each entry includes 
    the command text, output, return code, and whether it was blocked. Useful for reviewing what actions 
    have been taken and troubleshooting failed commands.
    
    Returns:
        JSON array containing full command history with commands, outputs, return codes, and blocked status
    """
    return _executor.get_history()


@mcp.tool()
def get_security_tools() -> str:
    """
    Returns the whitelist of approved commands for pentesting from the configuration file. Includes both 
    system commands (ls, cat, grep, etc.) and pentesting tools (nmap, nikto, dirb, etc.). Reference this 
    to understand which commands are available and safe to use.
    
    Returns:
        JSON object with categorized lists of whitelisted system and pentesting commands
    """
    config = load_yaml_file(CMD_CONFIG_PATH)
    
    return json.dumps({
        "system_commands": sorted(config['system_commands']),
        "pentest_commands": sorted(config['pentest_commands']),
        "note": "These are whitelisted commands for pentesting operations"
    }, indent=2)


@mcp.tool()
def make_http_request(url: str, method: str = "GET", headers: str = "{}", data: str = "") -> str:
    """
    Sends HTTP requests to test API endpoints and web services. Use this to probe targets with custom methods, 
    headers, and payloads. Automatically handles URLs without schemes by defaulting to http://.
    
    Args:
        url: Target URL (scheme optional, defaults to http://)
        method: HTTP method - GET, POST, PUT, DELETE, PATCH, etc.
        headers: JSON string containing custom HTTP headers
        data: Request body content for POST/PUT requests
        
    Returns:
        Raw HTTP response body text
        
    Examples:
        {"url": "http://target.com/api", "method": "POST", "data": "test=1"}
        {"url": "https://example.com", "headers": "{\"User-Agent\": \"Custom\"}"}
    """
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    # Parse headers if provided
    request_headers = {}
    if headers and headers != "{}":
        request_headers = json.loads(headers)
    
    # Make request
    response = requests.request(
        method=method.upper(),
        url=url,
        headers=request_headers,
        data=data,
        timeout=30,
        allow_redirects=False
    )
    
    return response.text


@mcp.tool()
def check_security_headers(url: str) -> str:
    """
    Analyzes a website's HTTP response headers for security weaknesses. Checks for presence of critical 
    security headers (CSP, HSTS, etc.) and identifies information disclosure issues like exposed server 
    versions. Returns a formatted report with checkmarks, crosses, and warnings.
    
    Args:
        url: Target URL to analyze (scheme optional, defaults to https://)
        
    Returns:
        Formatted report showing which security headers are present/missing plus any disclosure warnings
        
    Examples:
        {"url": "https://example.com"}
        {"url": "target.com"}
    """
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    response = requests.get(url, timeout=10, allow_redirects=True)
    
    # Load security headers from config
    config = load_yaml_file(CMD_CONFIG_PATH)
    security_headers = config.get('security_headers', {})
    
    # Check which headers are present
    result = []
    for header in security_headers.keys():
        value = response.headers.get(header)
        if value:
            result.append(f"✓ {header}: {value}")
        else:
            result.append(f"✗ {header}: Missing")
    
    # Add warnings for information disclosure
    if response.headers.get('Server'):
        result.append(f"⚠️ Server header disclosed: {response.headers.get('Server')}")
    
    if response.headers.get('X-Powered-By'):
        result.append(f"⚠️ X-Powered-By header disclosed: {response.headers.get('X-Powered-By')}")
    
    return "\n".join(result)


if __name__ == "__main__":
    mcp.run(transport="stdio")
