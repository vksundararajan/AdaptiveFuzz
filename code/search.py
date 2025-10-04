import requests
import json
import subprocess
from typing import Dict, Optional
from urllib.parse import urlparse
from webtech import WebTech


def register_tools(mcp):
    """Register web search MCP tools"""
    
    @mcp.tool()
    def search_exploitdb(
        query: str, 
        case_sensitive: bool = False,
        exact_match: bool = False,
        strict: bool = False,
        title_only: bool = False,
        exclude: str = "",
        cve: str = "",
        json_output: bool = False,
        show_url: bool = False
    ) -> str:
        """
        Search Exploit Database for known exploits with advanced options.
        
        Args:
            query: Search term (e.g., "Apache 2.4", "WordPress 5.0")
            case_sensitive: Perform case-sensitive search (default: False)
            exact_match: Exact match on exploit title (default: False)
            strict: Strict version matching, no fuzzy search (default: False)
            title_only: Search only exploit title, not file path (default: False)
            exclude: Terms to exclude from results, separated by "|" (e.g., "PoC|dos")
            cve: Search by CVE ID instead of query (e.g., "CVE-2021-44228")
            json_output: Return results in JSON format (default: False)
            show_url: Show exploit-db.com URLs instead of local paths (default: False)
            
        Returns:
            Search results from ExploitDB
            
        Examples:
            {"query": "Apache 2.4.49", "title_only": true}
            {"query": "WordPress", "exclude": "PoC|dos"}
            {"cve": "CVE-2021-44228", "json_output": true}
            {"query": "linux kernel 3.2", "strict": true}
        """
        try:
            cmd = ['searchsploit']
            
            if cve:
                cmd.extend(['--cve', cve])
            else:
                if case_sensitive:
                    cmd.append('-c')
                if exact_match:
                    cmd.append('-e')
                if strict:
                    cmd.append('-s')
                if title_only:
                    cmd.append('-t')
                cmd.extend(query.split())
            
            if exclude:
                cmd.append(f'--exclude={exclude}')
            if json_output:
                cmd.append('-j')
            if show_url:
                cmd.append('-w')
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout if result.stdout else result.stderr
            return output if output else "No results found"
            
        except FileNotFoundError:
            return "❌ searchsploit not installed. Install with: sudo apt install exploitdb"
        except subprocess.TimeoutExpired:
            return "⏱️ Search timed out"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    @mcp.tool()
    def detect_technologies(url: str, headers_only: bool = False) -> str:
        """
        Detect web technologies and frameworks used by a website using webtech.
        
        Args:
            url: Target URL or domain
            headers_only: Only use HTTP headers for detection, skip page content analysis (default: False)
            
        Returns:
            Detected technologies, versions, categories, and confidence levels
            
        Examples:
            {"url": "example.com"}
            {"url": "https://target.com", "headers_only": true}
        """
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        wt = WebTech(options={'json': True})
        
        try:
            report = wt.start_from_url(url)
        except Exception as e:
            return f"❌ Connection error: {str(e)}"
        
        return json.dumps(report, indent=2)
    
    @mcp.tool()
    def lookup_cve(cve_id: str) -> str:
        """
        Lookup CVE vulnerability details from National Vulnerability Database.
        
        Args:
            cve_id: CVE identifier (format: CVE-YYYY-NNNNN)
            
        Returns:
            CVE details including description, CVSS score, and references
            
        Examples:
            {"cve_id": "CVE-2021-44228"}
            {"cve_id": "CVE-2023-12345"}
        """
        if not cve_id.upper().startswith('CVE-'):
            return "❌ Invalid CVE format. Use format: CVE-YYYY-NNNNN"
        
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id.upper()}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 404:
            return f"❌ CVE {cve_id} not found"
        
        response.raise_for_status()
        
        return json.dumps(response.json(), indent=2)

