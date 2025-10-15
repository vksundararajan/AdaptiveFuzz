import socket
from typing import List
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Executor Tools")


@mcp.tool()
def port_scanner(target_ip: str, ports: List[int]):
    """
    Scans the specified ports on the target IP and returns a list of open ports.
    Args:
        target_ip (str): The target IP address to scan.
        ports (List[int]): A list of port numbers to scan.
        task_id (int): The ID of the task from the state the scan.
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


if __name__ == "__main__":
    mcp.run(transport="stdio")
    