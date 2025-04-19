# import the needed modules
import threading
import platform
import subprocess
import ipaddress
import threading
import eel
import socket
import time
import json
import os
import netifaces
from scapy.all import Ether, ARP, srp, sniff, sendp
from random import randint
from threading import Lock
from datetime import datetime as dt
from concurrent.futures import ThreadPoolExecutor

# Dynamically determine the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the 'web' folder relative to the script's directory
web_folder_path = os.path.join(script_dir, 'web')

# Initialize Eel with the dynamically determined path
eel.init(web_folder_path)

# Initialize a global list to store devices and a lock for thread safety
devices = []
devices_lock = Lock()
stop_event = threading.Event()
executor = None

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
    while not stop_event.is_set():
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

    executor = ThreadPoolExecutor(max_workers=100)
    for ip in subnet.hosts():
        executor.submit(scan_ip, ip, ports)
    return executor

def get_local_subnet():
    """Detect the local subnet dynamically."""
    try:
        # Get the default gateway interface
        default_gateway = netifaces.gateways()['default'][netifaces.AF_INET][1]
        # Get the IP address and subnet mask of the interface
        iface_info = netifaces.ifaddresses(default_gateway)[netifaces.AF_INET][0]
        ip_address = iface_info['addr']
        netmask = iface_info['netmask']
        # Calculate the CIDR notation for the subnet
        subnet = ipaddress.IPv4Network(f"{ip_address}/{netmask}", strict=False)
        return str(subnet)
    except Exception as e:
        print(f"Error detecting local subnet: {e}")
        return None

@eel.expose
def getDeviceList():
    global devices
    return json.dumps(devices)

@eel.expose
def start_scan():
    global executor
    subnet = get_local_subnet()
    if subnet:
        print(f"Scanning subnet: {subnet}")
        executor = scan_subnet(subnet, [21, 22, 23, 25, 53, 80, 443, 135, 139, 445, 5000, 8080])
    else:
        print("Failed to detect subnet. Aborting scan.")

def on_close_callback(route, websockets):
    """Callback function triggered when the main window is closed."""
    print("Main window closed. Terminating program...")
    stop_event.set()  # Signal all threads to stop
    if executor:
        executor.shutdown(wait=True)  # Wait for all threads to finish
    print("All threads terminated. Exiting program.")
    os._exit(0)  # Forcefully exit the program

def start_gui():
    eel.start('index.html', size=(1000, 800), close_callback=on_close_callback)

# Start the GUI in a separate thread
gui_thread = threading.Thread(target=start_gui)
gui_thread.start()

try:
    while True:
        time.sleep(1)  # Sleep to reduce CPU usage
except KeyboardInterrupt:
    print("Keyboard Interrupt detected. Waiting for threads to terminate...")
    stop_event.set()  # Signal all threads to stop
    if executor:
        executor.shutdown(wait=True)  # Wait for all threads to finish
    gui_thread.join()  # Wait for GUI thread to finish
    print("All threads terminated. Exiting program.")

