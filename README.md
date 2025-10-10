# [AdaptiveFuzz](https://github.com/vksundararajan/AdaptiveFuzz)

[![Status: Ongoing](https://img.shields.io/badge/status-Ongoing-gold?style=flat-square)](https://github.com/vksundararajan/AdaptiveFuzz/issues)


AdaptiveFuzz streamlines and manages reconnaissance for authorised penetration testing by using an LLM-based, multi-controller approach. This system coordinates targeted modules and external tools and produces clear, auditable reports that help document the findings.

## Expected Outcome

1. Information Gathering: Collect as much information as possible about a target's systems, networks, and infrastructure. 

2. Vulnerability Identification: This research aims to uncover weak points, open ports, and other vulnerabilities that can be exploited in later stages of an attack. 

3. Attack Strategy Planning: The gathered intelligence helps attackers tailor their approach and increases the chances of a successful breach.


## Architecture

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	conversational_handler(conversational_handler)
	recon_executor(recon_executor)
	result_interpreter(result_interpreter)
	strategy_advisor(strategy_advisor)
	human_in_loop(human_in_loop)
	__end__([<p>__end__</p>]):::last
	__start__ --> conversational_handler;
	conversational_handler -. &nbsp;review&nbsp; .-> human_in_loop;
	conversational_handler -. &nbsp;proceed&nbsp; .-> recon_executor;
	human_in_loop -. &nbsp;stop&nbsp; .-> __end__;
	human_in_loop -. &nbsp;continue&nbsp; .-> conversational_handler;
	recon_executor --> result_interpreter;
	result_interpreter --> strategy_advisor;
	strategy_advisor --> human_in_loop;
	classDef default fill:,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:
```


## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vksundararajan/AdaptiveFuzz.git
   cd AdaptiveFuzz
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python3 code/to_start.py
   ```


## MCP Tools

AdaptiveFuzz is powered by 8 security-focused MCP tools that help pentesters sort out their own security assessment.

- secure_executor
- get_executor_history
- get_allowed_commands
- make_http_request
- check_security_headers
- search_exploitdb 
- detect_technologies
- lookup_cve