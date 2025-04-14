import platform
import subprocess
import ipaddress
import threading
import socket

active_ips = []

def ping_ip(ip):
    """Ping an IP address and return True if online, False otherwise."""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', str(ip)]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if any(keyword in result.stdout.lower() for keyword in ["unreachable", "timed out", "failure"]):
            return False
        return True
    except Exception as e:
        print(f"Error pinging {ip}: {e}")
        return False

def check_port(ip, port):
    """Check if a specific port is open on an IP address."""
    try:
        with socket.create_connection((str(ip), port), timeout=3):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def scan_ip(ip, ports):
    """Scan a single IP address."""
    global active_ips
    print(f"Scanning {ip}...")
    is_online = ping_ip(ip)
    if is_online:
        print(f"{ip} is online (ping successful).")
        active_ips.append({"ip": str(ip), "status": "online", "port": None})
    else:
        print(f"{ip} is offline (ping failed). Trying ports...")
        for port in ports:
            if check_port(ip, port):
                print(f"{ip} responded on port {port}.")
                active_ips.append({"ip": str(ip), "status": "port open", "port": port})
                return
        print(f"{ip} is completely unreachable.")
        active_ips.append({"ip": str(ip), "status": "offline", "port": None})

def scan_subnet(subnet_str, ports):
    """Scan all IPs in the specified subnet."""
    global active_ips
    active_ips = []

    subnet = ipaddress.IPv4Network(subnet_str, strict=False)
    threads = []

    for ip in subnet.hosts():
        t = threading.Thread(target=scan_ip, args=(ip, ports))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    return active_ips

