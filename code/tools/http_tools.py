import requests
import json
from typing import Dict, Optional
from paths import COMMANDS_CONFIG_PATH
from utils import load_yaml_file


def register_tools(mcp):
    """Register api pentesting MCP tools"""
    
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
        config = load_yaml_file(COMMANDS_CONFIG_PATH)
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
