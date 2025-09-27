import pexpect
from utils.recipe import CTF_RECIPE

class PersistentTerminal:
    def __init__(self):
        try:
            # Start a persistent bash shell
            self.shell = pexpect.spawn("/bin/bash", encoding="utf-8", timeout=1000)
            self.shell.expect(r"\$")  # Wait for the initial shell prompt
        except pexpect.ExceptionPexpect as e:
            raise RuntimeError(f"Failed to start shell: {e}")

    def execute_command(self, command: str) -> str:
        try:
            self.shell.sendline(command)
            self.shell.expect(r"\$")  # Wait for the next prompt
            output = self.shell.before.strip()
            cleaned_output = output.split(command, 1)[-1].strip()  # Remove echoed command
            return cleaned_output if cleaned_output else "Command executed, but no output returned."
        except pexpect.TIMEOUT:
            return "Command timed out."
        except pexpect.EOF:
            return "Shell closed unexpectedly."
        except Exception as e:
            return f"Unexpected error: {e}"

    def close(self):
        try:
            self.shell.sendline("exit")
            self.shell.close()
        except Exception:
            pass  # Ignore errors on closing

# Singleton instance for MCP use
persistent_terminal = PersistentTerminal()

def register_tools(mcp):
    @mcp.tool()
    def get_terminal(command: str) -> str:
        """
        The command should be a string that can be executed in a bash shell.
        This tool allows the agent to execute terminal command in a persistent bash shell.
        The command is executed in a non-blocking manner, and the output is returned to the agent.
        The command is executed in a persistent shell, so the agent can maintain context across multiple commands.
        The agent can use this tool to perform various tasks, such as network scanning, web enumeration, and service discovery.
        
        Example usage:
        {
            "tool": "get_terminal",
            "input": { "command": "whoami" }
        }
        ### Web Pentesting Command Reference List (Extended)

        A complete enumeration and reconnaissance command list for LLM-based agents or manual red teamers targeting web apps.

        ---

        #### 1. Network Reachability & Initial Checks

        - ping <IP>                                             # Check if target is live
        - traceroute <IP>                                       # Trace route to target
        - curl <IP>                                             # Check web response
        - curl -I <IP>                                          # Check headers
        - curl -s <IP>/robots.txt                               # Check restricted paths
        - curl -s <IP>/sitemap.xml                              # Discover indexed pages
        - curl -s <IP>/crossdomain.xml                          # Check Flash cross-domain policy
        - curl -s <IP> | grep -i cookie                         # Check for cookies in response
        - curl -s <IP>/server-status                            # Apache server status (if exposed)

        ---

        #### 2. Port & Service Enumeration (Nmap & Netcat)

        - `rustscan -a 10.10.128.147 --scripts none -u 5000` → Script scan with rustscan, donot use nmap scan it takes too much time.

        ---

        #### 3. Directory/File Fuzzing (ffuf, dirsearch, gobuster)

        - ffuf -w AdaptiveFuzz/supp/small.txt -u http://<IP>/FUZZ
        - ffuf -w AdaptiveFuzz/supp/small.txt -u http://<IP>/FUZZ
        - ffuf -X POST -w AdaptiveFuzz/supp/small.txt -u http://<IP>/FUZZ -d 'param=value'

        ---

        #### 4. Web App Info & CMS Discovery

        - curl -s -D - http://<IP>                              # Full header + body
        - curl -s http://<IP>/login                             # Discover login pages
        - curl -s http://<IP>/admin                             # Check admin panels
        - curl -s http://<IP>/config.php                        # Sensitive config files
        - whatweb http://<IP>                                   # Identify web technologies
        - wappalyzer http://<IP>                                # (Browser plugin/CLI) Detect CMS & frameworks
        - builtwith http://<IP>                                 # Technology lookup (online or API)

        ---

        #### 5. CMS Exploits & Searchsploit

        - searchsploit SweetRice 1.5.1                          # CMS version specific exploit search
        - searchsploit -w Wordpress                             # Check WordPress exploits
        - searchsploit Joomla                                   # Check Joomla CMS exploits
        - searchsploit Drupal                                   # Check Drupal vulnerabilities

        ---

        #### 6. Authentication & Login Page Testing

        - curl -X POST http://<IP>/login -d "user=admin&pass=admin"      # Try default login
        - hydra -L users.txt -P passwords.txt http-post-form "/login.php:user=^USER^&pass=^PASS^:Invalid" -V
        - wfuzz -w common-usernames.txt -w common-passwords.txt --hc 403,404 http://<IP>/login

        ---

        #### 7. Parameter Discovery & Injection Testing

        - curl http://<IP>/index.php?id=1                            # Check for parameter-based routing
        - curl -G http://<IP>/search --data-urlencode "q=test'"      # Test for SQLi
        - paramspider -d <domain.com>                                # Find URL parameters
        - arjun -u http://<IP>/page.php                               # Bruteforce parameter names

        ---

        #### 8. Login Bypass, Hash & Cookie Enumeration

        - curl -s -X POST http://<IP>/login -d "username=admin' -- -"    # SQLi login bypass
        - curl -s http://<IP> | grep -i 'Set-Cookie'                     # Check for cookie-based session
        - curl -s http://<IP> | grep -i 'csrf'                           # CSRF token check
        - curl -s http://<IP> | grep -Eo '[a-f0-9]{32,}'                 # Search for MD5/SHA1 hashes

        ---

        #### 9. Additional Recon Tools

        - nikto -h http://<IP>                                   # Web server vulnerability scanner
        - nuclei -u http://<IP>                                  # Template-based scanning
        - metasploit (use auxiliary/scanner/http/...)            # Web modules
        - amass enum -d <domain>                                 # Subdomain discovery
        - subfinder -d <domain>                                  # Subdomain enumeration
        - httpx -l hosts.txt                                     # Check which hosts are alive

        ---
        
        """
        try:
            return persistent_terminal.execute_command(command)
        except Exception as err:
            return f"Failed to run command: {err}"
        
    @mcp.tool()
    def get_recipe() -> str:
        """
        This will Briefly explain your purpose and key capabilities. Returns the full explanation used as the prompt for the LLM agent.
        This is the complete guide to do Pentesting Enumeration part. 
        This recipe includes step-by-step instructions and methodology for performing a red team Capture The Flag (CTF) challenge, 
        such as enumeration, information gathering, and exploitation.
        """
        return CTF_RECIPE