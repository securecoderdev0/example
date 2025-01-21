import os
import sqlite3
import win32crypt  # Ensure you have pypiwin32 installed
from Cryptodome.Cipher import AES
import json
import base64

# Replace 'Profile 7' with your actual profile name
chrome_path = os.path.join(os.environ['LOCALAPPDATA'], 
                           r"Google\Chrome\User Data\Profile 7\Login Data")

# Connect to the Chrome database
conn = sqlite3.connect(chrome_path)
cursor = conn.cursor()

# Retrieve and decrypt passwords
cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
for row in cursor.fetchall():
    origin_url = row[0]
    username = row[1]
    encrypted_password = row[2]
    
    # Attempt to decrypt the password
    try:
        decrypted_password = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1].decode('utf-8')
    except Exception as e:
        decrypted_password = "Decryption failed"

    print(f"URL: {origin_url}, Username: {username}, Password: {decrypted_password}")

conn.close()
