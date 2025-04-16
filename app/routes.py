# import the needed modules
from flask import Blueprint, render_template, jsonify
import threading
import platform
import subprocess
import ipaddress
import threading
import socket
import time
from scapy.all import Ether, ARP, srp, sniff, sendp
from random import randint
from threading import Lock
from datetime import datetime as dt

# initialize the Flask blueprint
main = Blueprint('main', __name__)

# Initialize a global list to store devices and a lock for thread safety	
devices = []
devices_lock = Lock()

# function to ping and ip address and check if it is online
def ping_ip(ip):
    """Ping an IP address and return True if online, False otherwise."""
    param = '-n' if platform.system().lower() == 'windows' else '-c' # Windows uses -n, Linux uses -c
    # Construct the ping command
    command = ['ping', param, '1', str(ip)]
    
    try:
        # Execute the ping command and capture the output
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        # Check the output for keywords indicating success or failure
        if any(keyword in result.stdout.lower() for keyword in ["unreachable", "timed out", "failure"]):
            return False
        return True
    except Exception as e:
        # Handle any exceptions that occur during the ping process
        print(f"Error pinging {ip}: {e}")
        return False
    
# function to check if an ip address is online using ARP
def arp_check(ip):
    """Send an ARP request to the specified IP and check for a response."""
    try:
        # Construct the ARP request packet
        arp_request = ARP(pdst=str(ip))
        ether_frame = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether_frame / arp_request

        # Send the packet and wait for a response
        answered, unanswered = srp(packet, timeout=3, verbose=False)

        # Process the responses
        for sent, received in answered:
            if received and received.op == 2:  # ARP reply
                return received.hwsrc  # Return the MAC address

        return False  # No response
    except Exception as e:
        # handle exceptions
        print(f"Error in ARP check for {ip}: {e}")
        return False
    
# function to check if a device is online by connecting to common ports
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
        
# function to scan a specific IP address and check its status
def scan_ip(ip, ports):
    global devices
    while True:
        a = arp_check(ip)
        if a:
            print(f"{ip} is online (ARP successful).")
            last_seen = str(dt.now().time())
            with devices_lock:
                # Check if the IP already exists in the devices list
                existing_device = next((device for device in devices if device["ip"] == str(ip)), None)
                if existing_device:
                    existing_device["mac"] = a  # Update MAC address if it exists
                    existing_device["last_seen"] = last_seen
                else:
                    devices.append({"ip": str(ip), "mac": a, "last_seen": last_seen})
            time.sleep(randint(8, 14))
        else:
            is_online = ping_ip(ip)
            if is_online:
                print(f"{ip} is online (ping successful).")
                last_seen = str(dt.now().time())
                with devices_lock:
                    existing_device = next((device for device in devices if device["ip"] == str(ip)), None)
                    if existing_device:
                        existing_device["last_seen"] = last_seen
                    else:
                        devices.append({"ip": str(ip), "mac": None, "last_seen": last_seen})
                time.sleep(randint(7, 15))
            else:
                if check_ports(ip, ports):
                    print(f"{ip} is online (port responding).")
                    last_seen = str(dt.now().time())
                    with devices_lock:
                        existing_device = next((device for device in devices if device["ip"] == str(ip)), None)
                        if existing_device:
                            existing_device["last_seen"] = last_seen
                        else:
                            devices.append({"ip": str(ip), "mac": None, "last_seen": last_seen})
                    time.sleep(randint(8, 16))
                else:
                    # Remove offline endpoint
                    with devices_lock:
                        devices = [device for device in devices if device["ip"] != str(ip)]
                    time.sleep(randint(10, 14))
        

def scan_subnet(subnet_str, ports):
    """Scan all IPs in the specified subnet."""
    global devices

    subnet = ipaddress.IPv4Network(subnet_str, strict=False)
    threads = []
    for ip in subnet.hosts():
        t = threading.Thread(target=scan_ip, args=(ip, ports))
        t.start()
        threads.append(t)


       
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/devices')
def devices_json():
    return jsonify({'devices': devices})


scan_thread = threading.Thread(target=scan_subnet, args=("192.168.1.0/24", [21, 22, 23, 25, 53 ,80, 443, 135, 139, 445, 5000, 8080]))
scan_thread.start()


