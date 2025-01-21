import tinytuya
import time
import json
import sys
import speech_recognition as sr
import logging

# Set up logging
logging.basicConfig(filename='smart_bulb.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Device ID and key (update with your actual device information)
DEVICE_ID = 'd7926bd5d70a3d6cf0nf7s'  # Your virtual ID
DEVICE_KEY = 'your_device_key'  # Replace with your smart bulb's key
DEVICE_IP = '132.154.59.228'  # Your smart bulb's IP

# Create a TinyTuya device instance
d = tinytuya.Bulb(DEVICE_ID, DEVICE_IP, DEVICE_KEY)

# Knowledge base for common errors
knowledge_base = {
    "device not found": "Please ensure the device is powered on and connected to the network.",
    "invalid command": "Sorry, I did not understand that. Please try rephrasing your command.",
    "connection error": "There seems to be a connection issue. Please check your internet connection.",
    "brightness out of range": "Please set brightness between 0 and 100.",
}

# Function to listen for commands using voice recognition
def listen_for_commands():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for commands...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

        try:
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
            process_voice_command(command)
        except sr.UnknownValueError:
            print("Sorry, I did not understand that.")
            provide_error_solution("invalid command")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            provide_error_solution("connection error")

# Provide solutions for common errors
def provide_error_solution(error_key):
    solution = knowledge_base.get(error_key)
    if solution:
        print(f"Suggestion: {solution}")

# Process the recognized voice command
def process_voice_command(command):
    command = command.lower()
    
    if 'turn on the light' in command or 'turn on' in command:
        try:
            print("Turning on the light...")
            d.turn_on()
            logging.info("Light turned on successfully.")
        except Exception as e:
            print(f"Error turning on the light: {e}")
            logging.error(f"Error turning on the light: {e}")
            provide_error_solution("device not found")
    
    elif 'turn off the light' in command or 'turn off' in command:
        try:
            print("Turning off the light...")
            d.turn_off()
            logging.info("Light turned off successfully.")
        except Exception as e:
            print(f"Error turning off the light: {e}")
            logging.error(f"Error turning off the light: {e}")
            provide_error_solution("device not found")

    elif 'set brightness' in command:
        brightness = extract_brightness(command)
        if brightness is not None:
            if 0 <= brightness <= 100:
                print(f"Setting brightness to {brightness}%")
                try:
                    d.set_brightness_percentage(brightness)
                    logging.info(f"Brightness set to {brightness}%.")
                except Exception as e:
                    print(f"Error setting brightness: {e}")
                    logging.error(f"Error setting brightness: {e}")
                    provide_error_solution("device not found")
            else:
                print("Brightness value out of range.")
                logging.warning("Brightness value out of range.")
                provide_error_solution("brightness out of range")

    elif 'set color' in command or 'change the color to' in command:
        color = extract_color(command)
        if color is not None:
            print(f"Setting color to {color}")
            try:
                d.set_colour(color)  # Assuming color is already in the correct format
                logging.info(f"Color set to {color}.")
            except Exception as e:
                print(f"Error setting color: {e}")
                logging.error(f"Error setting color: {e}")
                provide_error_solution("device not found")
        else:
            print("Invalid color specified.")
            logging.warning("Invalid color specified.")
            provide_error_solution("invalid command")

# Extract brightness from the command
def extract_brightness(command):
    for word in command.split():
        if word.isdigit():
            return int(word)
    return None

# Extract color from the command
def extract_color(command):
    color_mapping = {
        'red': 'red',
        'green': 'green',
        'blue': 'blue',
        'white': 'white',
        'yellow': 'yellow',
        'purple': 'purple',
        'orange': 'orange',
        'pink': 'pink'
    }
    for color in color_mapping.keys():
        if color in command:
            return color_mapping[color]
    return None

# Main logic to connect to the device and process commands
try:
    d.set_version(3.3)  # Set the version to match your device
    status = d.status()  # Fetch the status of the device
    print('Device status:', status)

    # Optionally, check for voice commands
    listen_for_commands()

except Exception as e:
    print(f"Error: {e}")
    logging.error(f"Connection error: {e}")
    provide_error_solution("connection error")

print("Done!")


