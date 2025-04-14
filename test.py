from scapy.all import *
from scapy.layers.dns import DNS, DNSQR, DNSRR, IP, UDP

MDNS_GROUP = "224.0.0.251"
MDNS_PORT = 5353

def send_mdns_query(hostname):
    """Sends an mDNS query and listens for a response."""

    # Construct mDNS query (A record request)
    packet = IP(dst=MDNS_GROUP) / UDP(dport=MDNS_PORT, sport=MDNS_PORT) / \
             DNS(id=0, qr=0, qdcount=1, qd=DNSQR(qname=hostname, qtype="A"))

    print(f"Sending mDNS query for {hostname}...")

    # Send the query (send() is better for multicast)
    send(packet, verbose=False)

    # Sniff responses
    responses = sniff(filter=f"udp port {MDNS_PORT}", timeout=2, count=5)

    for rcv in responses:
        if rcv.haslayer(DNS) and rcv[DNS].ancount > 0:
            for i in range(rcv[DNS].ancount):
                rr = rcv[DNS].an[i]
                if rr.type == 1:  # A record (IPv4)
                    print(f"{hostname} resolved to {rr.rdata}")
                    return rr.rdata  # Return first found IP

    print("No response received.")
    return None

# Usage
device_name = "Constance’s MacBook Air.local"  # Replace with actual hostname
send_mdns_query(device_name)
