from flask import Blueprint, render_template, jsonify
import threading
import platform
import subprocess
import ipaddress
import threading
import socket
import time
from random import randint

main = Blueprint('main', __name__)

devices = []

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

def check_ports(ip, ports):
    for port in ports:
        if check_port(ip, port):
            print(f"{ip} is online (port {port} responding).")
            return True
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
    global devices
    while True:
        is_online = ping_ip(ip)
        if is_online:
            print(f"{ip} is online (ping successful).")
            new_device = {"ip": str(ip), "mac": "will implement later"}
            if new_device not in devices:
                devices.append(new_device)
            time.sleep(randint(5, 10))
        else:
            if check_ports(ip, ports):
                new_device = {"ip": str(ip), "mac": "will implement later"}
                if new_device not in devices:
                    devices.append(new_device)
                time.sleep(randint(5, 10))
            else:
                for device in devices:
                    if device["ip"] == ip:
                        print(f"Removing offline endpoint {ip}")
                        devices.remove(device)
                time.sleep(randint(5, 8))
        

def scan_subnet(subnet_str, ports):
    """Scan all IPs in the specified subnet."""
    global devices

    subnet = ipaddress.IPv4Network(subnet_str, strict=False)

    for ip in subnet.hosts():
        print(f"Starting tracking thread for {ip}...")
        t = threading.Thread(target=scan_ip, args=(ip, ports))
        t.start()


       
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/devices')
def devices_json():
    return jsonify({'devices': devices})


scan_thread = threading.Thread(target=scan_subnet, args=("192.168.1.0/24", [80, 443, 135, 139, 445]))
scan_thread.start()


