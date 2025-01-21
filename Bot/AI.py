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
from transformers import pipeline

import nltk
nltk.download('cmudict')
nltk.download('wordnet')
# it's not worked

class AIJarvis:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Jarvis")
        self.root.geometry("600x400")

        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        self.nlp = spacy.load("en_core_web_sm")
        self.pronouncing_dict = cmudict.dict()

        # Initialize NLP models
        self.conversational_model = pipeline("conversational", model="microsoft/DialoGPT-medium")
        self.translation_pipeline = pipeline("translation_en_to_fr")

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
            self.root.update()
            audio = self.recognizer.listen(source)
            try:
                text = self.recognizer.recognize_google(audio)
                self.output_area.insert(tk.END, f"You: {text}\n")
                self.root.update()
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
        if "translate" in command:
            _, _, text = command.partition("translate")
            self.translate_text(text.strip())
        elif "suggest a vocabulary word" in command:
            self.suggest_vocabulary()
        else:
            self.default_conversation(command)

    def default_conversation(self, text):
        """Handle general conversation using a conversational AI model."""
        response = self.conversational_model(text)[0]["generated_text"]
        self.speak(response)

    def translate_text(self, text):
        """Translate text from English to French."""
        translated_text = self.translation_pipeline(text)[0]["translation_text"]
        self.speak(f"The French translation is: {translated_text}")

    def suggest_vocabulary(self):
        """Suggest vocabulary words with definitions."""
        words = ["articulate", "eloquent", "lucid", "verbose", "succinct"]
        word = random.choice(words)
        self.speak(f"Today's vocabulary word is '{word}'. It means something clear or expressive.")

    def change_color(self):
        """Change the color of the smart bulb."""  
        color = colorchooser.askcolor()[1]
        if color:
            self.speak(f"Changed the bulb color to {color}.")
