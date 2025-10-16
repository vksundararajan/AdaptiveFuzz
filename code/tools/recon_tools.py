import socket
from typing import List, Dict
from fastmcp import FastMCP

mcp = FastMCP("Executor Tools")


@mcp.tool(tags={"recon"})
def port_scanner(target_ip: str, ports: List[int], task_id: str) -> List[int]:
    """
    Scans the specified ports on the target IP and returns a list of open ports.
    Args:
        target_ip (str): The target IP address to scan. (REQUIRED)
        ports (List[int]): A list of port numbers to scan, e.g., [21, 22, 25, 80, 443, 8080]. (REQUIRED)
        task_id (str): The ID of the task this scan is for. (REQUIRED)
    Returns:
        List[int]: A list of open ports.
    """
    open_ports = []
    try:
        ip = socket.gethostbyname(target_ip)
        for port in ports:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)  # 1-second timeout
                if sock.connect_ex((ip, port)) == 0:
                    open_ports.append(port)
    except socket.gaierror:
        return []
    except socket.error:
        return []
        
    return open_ports


@mcp.tool(tags={"recon"})
def banner_grabber(target_ip: str, ports: List[int], task_id: str) -> Dict[int, str]:
    """
    Simple TCP banner grabber for PoC use.
    Args:
        target_ip: target host or IP
        ports: list of ports to check
        task_id: required task id
    Returns:
        Dict[port, banner]
    """
    results = {}
    try:
        ip = socket.gethostbyname(target_ip)
    except socket.gaierror:
        return {}

    for port in ports:
        try:
            sock = socket.socket()
            sock.settimeout(1)
            sock.connect((ip, port))
            sock.sendall(b"\r\n")
            banner = sock.recv(1024).decode(errors="ignore").strip()
            results[port] = banner or "No banner"
            sock.close()
        except Exception:
            results[port] = "Closed or no response"
    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
    