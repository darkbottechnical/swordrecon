from flask import Blueprint, render_template, jsonify
from .scanner import scan_subnet
import threading

main = Blueprint('main', __name__)

scan_results = []

def run_scan(subnet):
    global scan_results
    scan_results = scan_subnet(subnet, [80, 443, 135, 445])

@main.route('/')
def index():
    scan_thread = threading.Thread(target=run_scan, args=("192.168.1.0/24",))
    scan_thread.start()
    return render_template('index.html')

@main.route('/devices')
def devices_json():
    return jsonify({'devices': scan_results})

