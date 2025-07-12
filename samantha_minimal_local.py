import os
import json
import webbrowser
import tkinter as tk
from tkinter import Label, Entry, Button, Text
import pyttsx3
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import requests
from bs4 import BeautifulSoup
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

MODEL_NAME = "microsoft/DialoGPT-small"
DATA_FILE = "samantha_local_data.json"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 185)
tts_engine.setProperty('volume', 1.0)

def speak(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

def save_interaction(command, response):
    data = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = []
    data.append({"command": command, "response": response})
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def detect_intent(command):
    cmd = command.lower()
    if "search" in cmd and ("brave" in cmd or "chromium" in cmd or "chrome" in cmd):
        return "browserautomation"
    elif "open" in cmd and ("brave" in cmd or "chromium" in cmd or "chrome" in cmd):
        return "browserautomation"
    elif "open" in cmd or "launch" in cmd:
        return "openapp"
    elif "close" in cmd or "quit" in cmd:
        return "closeapp"
    elif "google" in cmd or "search" in cmd or "find" in cmd:
        return "websearch"
    elif "scrape" in cmd or "extract" in cmd or "get info from" in cmd:
        return "webscraping"
    elif "write" in cmd or "story" in cmd or "poem" in cmd:
        return "creative"
    elif "code" in cmd or "function" in cmd or "script" in cmd:
        return "coding"
    else:
        return "general"

def get_system_prompt(task):
    if task == "coding":
        return (
            "You are Samantha, an AI assistant inspired by ChatGPT and Claude. "
            "Generate production-quality code, explain reasoning, avoid hallucinations, and provide actionable steps. "
            "Reference standards and cite docs. Never output unexplained code."
        )
    elif task == "websearch":
        return (
            "You are Samantha, an AI assistant. Perform web search using Google and summarize findings. Never send user data online."
        )
    elif task == "webscraping":
        return (
            "You are Samantha, an AI assistant. Scrape websites using offline tools. "
            "Return concise, relevant info. Never send user data online."
        )
    elif task == "browserautomation":
        return (
            "You are Samantha, an AI assistant. Automate any browser: open, close, navigate, search, play media, and interact. Confirm actions before executing."
        )
    elif task == "openapp":
        return (
            "You are Samantha, an AI assistant for Mac. Open system apps using safe, generic commands."
        )
    elif task == "closeapp":
        return (
            "You are Samantha, an AI assistant for Mac. Close system apps using safe, generic commands."
        )
    elif task == "creative":
        return (
            "You are Samantha, a creative AI writer. Write with empathy and creativity, structure work like a pro author, avoid cliché responses."
        )
    else:
        return (
            "You are Samantha, a safe, context-aware, privacy-respecting offline AI assistant. "
            "All interests and history are local. Clarify ambiguous queries, avoid hallucinations, cite sources if possible."
        )

def get_response(user_input, task="general", history=[]):
    prompt = get_system_prompt(task) + f"\nUser: {user_input}\nAssistant:"
    inputs = tokenizer(prompt, return_tensors='pt', padding=True)
    chat_history_ids = model.generate(
        inputs['input_ids'],
        attention_mask=inputs['attention_mask'],
        max_length=1000,
        pad_token_id=tokenizer.eos_token_id
    )
    output = tokenizer.decode(chat_history_ids[:, inputs['input_ids'].shape[-1]:][0], skip_special_tokens=True)
    return output

def perform_system_action(command, intent):
    command_lower = command.lower()
    # Open app (generic, any installed app)
    if intent == "openapp":
        app_name = command_lower.replace("open", "").replace("launch", "").strip()
        app_name = app_name.title()
        os.system(f'open -a "{app_name}"')
        return f"Opening {app_name}."
    # Close app (generic, any installed app)
    elif intent == "closeapp":
        app_name = command_lower.replace("close", "").replace("quit", "").strip()
        app_name = app_name.title()
        os.system(f'osascript -e \'tell application "{app_name}" to quit\'')
        return f"Closing {app_name}."
    # Web search (Google)
    elif intent == "websearch":
        if "search" in command_lower:
            query = command_lower.split("search",1)[1].strip()
        elif "google" in command_lower:
            query = command_lower.split("google",1)[1].strip()
        elif "find" in command_lower:
            query = command_lower.split("find",1)[1].strip()
        else:
            query = command_lower
        url = f"https://www.google.com/search?q={query.replace(' ','+')}"
        webbrowser.open(url)
        return f"Searching for '{query}' on Google."
    # Web scraping
    elif intent == "webscraping":
        words = command.split()
        url = ""
        q = ""
        for w in words:
            if w.startswith("http") or "." in w:
                url = w if w.startswith("http") else f"https://{w.strip()}"
            else:
                q += w + " "
        if not url:
            return "Please specify a valid URL for scraping."
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            results = soup.find_all(string=lambda t: q.lower().strip() in t.lower())
            return "\n".join([res.strip() for res in results[:5]]) or "No relevant info found."
        except Exception as e:
            return f"Web scraping failed: {e}"
    # Browser automation (Selenium)
    elif intent == "browserautomation":
        def browser_task():
            # Detect which browser to use
            browser_path = None
            if "chromium" in command_lower:
                browser_path = "/Applications/Chromium.app/Contents/MacOS/Chromium"
            elif "brave" in command_lower:
                browser_path = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
            elif "chrome" in command_lower:
                browser_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            else:
                browser_path = "/Applications/Chromium.app/Contents/MacOS/Chromium"

            options = webdriver.ChromeOptions()
            options.binary_location = browser_path
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            chromedriver_path = "/usr/local/bin/chromedriver" # Ensure chromedriver is installed

            try:
                driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)
                if "search" in command_lower:
                    # Extract search query
                    if "search for" in command_lower:
                        search_query = command_lower.split("search for",1)[1].strip()
                    elif "search" in command_lower:
                        search_query = command_lower.split("search",1)[1].strip()
                    else:
                        search_query = "spotify"
                    driver.get(f"https://www.google.com/search?q={search_query.replace(' ','+')}")
                    time.sleep(2)
                if "spotify" in command_lower:
                    driver.get("https://open.spotify.com/")
                    time.sleep(2)
                    # Try to search for a song if specified
                    if "run" in command_lower or "play" in command_lower:
                        song_query = ""
                        # Try to extract song name
                        if "run" in command_lower:
                            song_query = command_lower.split("run", 1)[1].strip()
                        elif "play" in command_lower:
                            song_query = command_lower.split("play", 1)[1].strip()
                        # If song specified, try to interact
                        if song_query:
                            try:
                                # Wait for search box and enter song
                                search_box = driver.find_element(By.XPATH, "//input[@placeholder='What do you want to listen to?']")
                                search_box.send_keys(song_query)
                                search_box.send_keys(Keys.RETURN)
                                time.sleep(3)
                            except Exception as e:
                                print("Could not auto-search song on Spotify (not logged in?):", e)
                if "youtube" in command_lower:
                    driver.get("https://youtube.com")
                    time.sleep(2)
                driver.quit()
            except Exception as e:
                print(f"Browser automation failed: {e}")
        Thread(target=browser_task).start()
        return "Browser automation started!"
    else:
        return "System command not recognized."

class SamanthaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Samantha AI (Local Mac, Text Only)")
        self.root.geometry("600x700")
        self.root.configure(bg="#2c3e50")

        self.status_label = Label(root, text="Ready - Type your command!", font=("Arial", 16), fg="#3498db", bg="#2c3e50")
        self.status_label.pack(pady=10)

        self.command_entry = Entry(root, font=("Arial", 12), bg="#ecf0f1", fg="#2c3e50", relief="flat", bd=10)
        self.command_entry.pack(fill="x", pady=5)
        self.command_entry.bind("<Return>", self.process_command)

        send_button = Button(root, text="Send", font=("Arial", 12, "bold"), command=self.process_command, bg="#3498db", fg="white")
        send_button.pack(pady=10)

        self.response_text = Text(root, font=("Arial", 11), bg="#ecf0f1", fg="#2c3e50", wrap=tk.WORD, height=20)
        self.response_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def process_command(self, event=None):
        command = self.command_entry.get().strip()
        if not command:
            return
        self.command_entry.delete(0, tk.END)
        self.status_label.config(text="Processing...")
        self.root.update_idletasks()

        intent = detect_intent(command)
        # direct system actions
        if intent in ["openapp", "closeapp", "websearch", "webscraping", "browserautomation"]:
            response = perform_system_action(command, intent)
            self.response_text.insert(tk.END, f"You: {command}\nSamantha: {response}\n\n")
            speak(response)
            save_interaction(command, response)
            self.status_label.config(text="Ready - Type your next command!")
            return
        # LLM-based
        response = get_response(command, intent)
        self.response_text.insert(tk.END, f"You: {command}\nSamantha: {response}\n\n")
        speak(response)
        save_interaction(command, response)
        self.status_label.config(text="Ready - Type your next command!")

def main():
    root = tk.Tk()
    gui = SamanthaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()