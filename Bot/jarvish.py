import tkinter as tk
from tkinter import messagebox, colorchooser
import speech_recognition as sr
import pyttsx3
import spacy
from nltk.corpus import cmudict
from textblob import TextBlob
import requests
import random
import threading
import torch
from transformers import pipeline

# Ensure necessary NLTK data is downloaded
import nltk
nltk.download('cmudict')
nltk.download('wordnet')

class AIJarvis:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Jarvis")
        self.root.geometry("600x400")

        # Initialize recognizer and TTS engine
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.nlp = spacy.load("en_core_web_sm")
        self.pronouncing_dict = cmudict.dict()
       
        self.grammar_checker_bart = pipeline("text2text-generation", model="facebook/bart-large-mnli")

        # Create GUI components
        self.create_widgets()
        
    def create_widgets(self):
        """Create GUI components."""
        self.output_area = tk.Text(self.root, height=10, width=70)
        self.output_area.pack(pady=10)

        self.input_entry = tk.Entry(self.root, width=50)
        self.input_entry.pack(pady=10)

        self.send_button = tk.Button(self.root, text="Send", command=self.process_command_from_entry)
        self.send_button.pack(pady=10)

        self.listen_button = tk.Button(self.root, text="Listen", command=self.listen)
        self.listen_button.pack(pady=10)

        self.color_button = tk.Button(self.root, text="Change Bulb Color", command=self.change_color)
        self.color_button.pack(pady=10)

        self.bulb_on_button = tk.Button(self.root, text="Turn Bulb ON", command=lambda: self.control_wipro_bulb("on"))
        self.bulb_on_button.pack(pady=10)

        self.bulb_off_button = tk.Button(self.root, text="Turn Bulb OFF", command=lambda: self.control_wipro_bulb("off"))
        self.bulb_off_button.pack(pady=10)

    def speak(self, text):
        """Convert text to speech output."""
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
        self.output_area.insert(tk.END, f"Jarvis: {text}\n")
        self.output_area.see(tk.END)

    def listen(self):
        """Listen to the user and return recognized text."""
        with sr.Microphone() as source:
            self.output_area.insert(tk.END, "Listening...\n")
            self.root.update()  # Update GUI
            audio = self.recognizer.listen(source)
            try:
                text = self.recognizer.recognize_google(audio)
                self.output_area.insert(tk.END, f"You: {text}\n")
                self.root.update()  # Update GUI
                self.process_command(text)
            except sr.UnknownValueError:
                self.speak("Sorry, I didn't catch that.")
            except sr.RequestError:
                self.speak("Service is down.")

    def process_command_from_entry(self):
        """Process command from input entry."""
        command = self.input_entry.get()
        self.output_area.insert(tk.END, f"You: {command}\n")
        self.input_entry.delete(0, tk.END)
        self.process_command(command)

    def process_command(self, command):
        """Identify and execute commands based on user input."""
        if "teach me English" in command:
            self.teach_english()
        elif "pronounce" in command:
            word = command.split("pronounce")[-1].strip()
            self.pronunciation_help(word)
        elif "correct my sentence" in command:
            self.speak("Please say the sentence you want me to correct.")
            self.listen()
        elif "turn bulb" in command:
            if "on" in command:
                self.control_wipro_bulb("on")
            elif "off" in command:
                self.control_wipro_bulb("off")
        elif "change color" in command:
            self.change_color()
        elif "suggest a vocabulary word" in command:
            self.suggest_vocabulary()
        else:
            self.speak("I didn't understand that command.")

    def correct_english(self, sentence):
        """Analyze and correct the grammar of a given sentence using a deep learning model."""
        # Using T5 model
        corrected_sentence_t5 = self.grammar_checker_t5(sentence)[0]['generated_text']
        # Using BART model
        corrected_sentence_bart = self.grammar_checker_bart(sentence)[0]['generated_text']
        return corrected_sentence_t5, corrected_sentence_bart

    def teach_english(self):
        """A method to engage in English conversation practice."""
        self.speak("Let's practice English! Say something, and I'll help you improve.")
        self.listen()

    def pronunciation_help(self, word):
        """Provide pronunciation help using CMU Pronouncing Dictionary."""
        pronunciation = self.pronouncing_dict.get(word.lower())
        if pronunciation:
            phonetic = ' '.join(pronunciation[0])
            self.speak(f"The pronunciation of '{word}' is: {phonetic}")
        else:
            self.speak(f"Sorry, I couldn't find the pronunciation for '{word}'.")

    def control_wipro_bulb(self, state):
        """Turn the Wipro bulb on or off."""
        bulb_api_url = "http://<bulb-ip>/api"  # Replace with actual IP and API endpoint
        try:
            if state.lower() == "on":
                response = requests.post(f"{bulb_api_url}/turn_on")
                self.speak("Turning the bulb on.")
            elif state.lower() == "off":
                response = requests.post(f"{bulb_api_url}/turn_off")
                self.speak("Turning the bulb off.")
            if response.status_code != 200:
                self.speak("Failed to control the bulb. Check your network and try again.")
        except Exception as e:
            self.speak("There was an error connecting to the bulb.")

    def change_color(self):
        """Change the color of the smart bulb."""  
        color = colorchooser.askcolor()[1]  # Show color picker
        if color:
            bulb_api_url = "http://<bulb-ip>/api"  # Replace with actual IP and API endpoint
            try:
                response = requests.post(f"{bulb_api_url}/change_color", json={"color": color})
                if response.status_code == 200:
                    self.speak(f"Changed the bulb color to {color}.")
                else:
                    self.speak("Failed to change the bulb color.")
            except Exception as e:
                self.speak("There was an error connecting to the bulb.")

    def suggest_vocabulary(self):
        """Suggest vocabulary words with definitions using spaCy.""" 
        words = ["articulate", "eloquent", "lucid", "verbose", "succinct"]
        word = random.choice(words)
        self.speak(f"Today's vocabulary word is '{word}'. It means something clear or expressive.")

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    jarvis = AIJarvis(root)
    root.mainloop()
