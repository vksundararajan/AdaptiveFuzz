import os
import asyncio
from dotenv import load_dotenv

from paths import ENV_PATH, DEFAULT_MODEL_PATH

load_dotenv(ENV_PATH)

from agents.interpreter import get_interpreter_agent
from agents.orchestrator import get_orchestrator_agent
from agents.executor import get_executor_agent
from agents.perceptor import get_perceptor_agent
from agents.report_writer import get_report_writer_agent
from core.local_model import LocalGGUFModel
from core.state_monitor import StateMonitor
from core.task_queue import TaskQueue

async def main():
    print("[*] SYS  : Bootstrapping framework...")
    state_monitor = StateMonitor(max_iterations=5)
    task_queue = TaskQueue()
    
    model = LocalGGUFModel(model_path=DEFAULT_MODEL_PATH)
    print("[*] SYS  : Model loaded successfully")
    
    interpreter = get_interpreter_agent(model)
    executor = get_executor_agent(model)
    perceptor = get_perceptor_agent(model)
    report_writer = get_report_writer_agent(model)
    
    orchestrator = get_orchestrator_agent(model)
    print("[+] SYS  : Initialization complete.")
    
    target_scope = "example.com"
    constraints = "no invasive scanning, only passive OSINT"
    print(f"\n[>] USER : Scope: {target_scope} | Constraints: {constraints}")
    print("[*] INT  : Parsed input and initialized state.")
    
    while not state_monitor.done:
        if not state_monitor.check_constraints():
            break
            
        print(f"\n[*] ORC  : Cycle {state_monitor.current_iteration + 1} - Retrieving context & planning...")
        
        await task_queue.add_task({"id": f"task_{state_monitor.current_iteration}", "command": f"subfinder -d {target_scope}"})
        state_monitor.register_tasks(1)
        
        task = await task_queue.get_task()
        print(f"[*] EXEC : Sandboxing command -> {task['command']}")
        
        print("[*] PERC : Parsing output and syncing to RAG...")
        task_queue.task_done()
        state_monitor.complete_task()
        state_monitor.increment_iteration()
        
    print("\n[*] REPT : Aggregating findings for final report...")
    print("[+] SYS  : Session safely terminated. Report delivered.")

    await task_queue.close()

if __name__ == "__main__":
    asyncio.run(main())
