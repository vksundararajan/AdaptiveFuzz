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
        Searches the Exploit Database for publicly available exploits matching software versions or CVE IDs. 
        Uses the searchsploit command-line tool with flexible filtering options. Useful for finding known 
        vulnerabilities in identified technologies.
        
        Args:
            query: Software name and version to search (e.g., "Apache 2.4", "WordPress 5.0")
            case_sensitive: Enable case-sensitive matching
            exact_match: Match exact exploit title only
            strict: Disable fuzzy matching for precise version searches
            title_only: Search exploit titles only, ignore file paths
            exclude: Pipe-separated terms to filter out (e.g., "PoC|dos")
            cve: Search by CVE identifier instead of query string
            json_output: Return structured JSON instead of text
            show_url: Show exploit-db.com URLs rather than local paths
            
        Returns:
            List of matching exploits with titles, paths/URLs, and metadata
            
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
        Fingerprints web technologies, frameworks, and libraries used by a target website. Analyzes HTTP headers 
        and page content to identify technologies like web servers, CMS platforms, JavaScript frameworks, and more. 
        Returns detailed JSON with confidence levels for each detection.
        
        Args:
            url: Target URL or domain (scheme optional, defaults to http://)
            headers_only: Skip page content analysis and use only HTTP headers for faster but less complete detection
            
        Returns:
            JSON report with detected technologies, versions, categories, and confidence scores
            
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
        Retrieves detailed vulnerability information from the National Vulnerability Database (NVD) API. 
        Provides comprehensive CVE data including descriptions, severity scores (CVSS), affected products, 
        and reference links. Essential for understanding the impact and exploitability of identified vulnerabilities.
        
        Args:
            cve_id: CVE identifier in format CVE-YYYY-NNNNN (e.g., CVE-2021-44228)
            
        Returns:
            Complete JSON response from NVD with vulnerability description, CVSS metrics, references, and affected configurations
            
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

