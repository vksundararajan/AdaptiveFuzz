import requests
import json
import yaml
from typing import Dict, Optional
from ..paths import COMMANDS_CONFIG_PATH


def register_tools(mcp):
    """Register api pentesting MCP tools"""
    
    @mcp.tool()
    def make_http_request(url: str, method: str = "GET", headers: str = "{}", data: str = "") -> str:
        """
        Make a custom HTTP request with full control over method, headers, and data.
        
        Args:
            url: Target URL
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            headers: JSON string of custom headers
            data: Request body/data
            
        Returns:
            HTTP response body
            
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
        Check a website for important security headers.
        
        Args:
            url: Target URL to analyze
            
        Returns:
            List of security headers with status (present/missing) and warnings
            
        Examples:
            {"url": "https://example.com"}
            {"url": "target.com"}
        """
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        response = requests.get(url, timeout=10, allow_redirects=True)
        
        # Load security headers from config
        with open(COMMANDS_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
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
