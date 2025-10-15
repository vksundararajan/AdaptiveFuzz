from typing import Any, Dict, List


def h_response(
    findings: List[Dict[str, Any]],
    completed_tasks: List[Dict[str, str]],
    pending_tasks: List[Dict[str, str]],
    strategies: List[str],
) -> str:
    """Formats the current state of the fuzzer into a human-readable string."""
    response = ["\n--------------------", "AdaptiveFuzz Status", "--------------------"]
    
    if completed_tasks:
        response.append("Completed Tasks:")
        for task in completed_tasks:
            description = task.get("task", "No description")
            status = task.get("status", "unknown")
            response.append(f"- {description} ({status})")

    if pending_tasks:
        response.append("Pending/Failed Tasks:")
        for task in pending_tasks:
            description = task.get("description", "No description")
            status = task.get("status", "pending")
            response.append(f"- {description} ({status})")

    if findings:
        response.append("Findings:")
        for finding in findings:
            response.append(f"- {finding}")

    response.append("\n💡  Next Possible Strategies, choice is yours!!")
    
    if strategies:
        for strategy in strategies:
            response.append(f"- {strategy}")   

    return "\n".join(response)


# print(h_response(
#     strategies=["Strategy 1", "Strategy 2", "Strategy 3"], 
#     findings=["Finding 1", "Finding 2", "Finding 3"], 
#     completed_tasks=[{"task": "scan the ip", "status": "Completed"}, {"task": "enum the services", "status": "Completed"}], 
#     pending_tasks=[{"task": "scan the ip", "status": "Pending"}, {"task": "enum the services", "status": "Failed"}]
# ))