#!/usr/bin/env python3
"""
Samantha - AI Voice Assistant
Main entry point for the voice assistant with speech recognition and natural language processing.
"""

import speech_recognition as sr
import pyttsx3
import threading
import time
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from assistant.intent_classifier import classify_intent
from assistant.spotify_control import control_spotify
from assistant.browser_control import browser_action
from assistant.whatsapp_integration import whatsapp_action

class SamanthaAssistant:
    def __init__(self):
        """Initialize the voice assistant"""
        print("🤖 Initializing Samantha...")

        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Initialize text-to-speech
        self.tts_engine = pyttsx3.init()
        self._configure_tts()

        # Assistant state
        self.listening = False
        self.running = True

        # Wake words
        self.wake_words = ["samantha", "hey samantha", "hello samantha"]

        print("✅ Samantha initialized successfully!")
        self._speak("Hello! I'm Samantha, your voice assistant. Say 'Hey Samantha' to wake me up.")

    def _configure_tts(self):
        """Configure text-to-speech settings"""
        try:
            # Set voice properties
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to use a female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower() or 'susan' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use first available voice
                    self.tts_engine.setProperty('voice', voices[0].id)

            # Set speech rate and volume
            self.tts_engine.setProperty('rate', 180)  # Speed of speech
            self.tts_engine.setProperty('volume', 0.8)  # Volume level (0.0 to 1.0)

        except Exception as e:
            print(f"⚠️ TTS configuration warning: {e}")

    def _speak(self, text: str):
        """Convert text to speech"""
        try:
            print(f"🗣️  Samantha: {text}")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"❌ Speech error: {e}")

    def _listen(self, timeout: int = 5) -> str:
        """Listen for audio input and convert to text"""
        try:
            with self.microphone as source:
                print("🎤 Listening...")
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # Listen for audio with timeout
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)

            print("🔄 Processing speech...")
            # Recognize speech using Google's service
            text = self.recognizer.recognize_google(audio).lower()
            print(f"👤 You said: {text}")
            return text

        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return ""
        except sr.WaitTimeoutError:
            return ""
        except Exception as e:
            print(f"❌ Listening error: {e}")
            return ""

    def _check_wake_word(self, text: str) -> bool:
        """Check if the text contains a wake word"""
        text_lower = text.lower().strip()
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                return True
        return False

    def _process_command(self, command: str) -> str:
        """Process a voice command and return response"""
        try:
            if not command.strip():
                return "I didn't catch that. Could you please repeat?"

            # Classify the intent
            intent = classify_intent(command)
            print(f"🧠 Detected intent: {intent}")

            # Route to appropriate handler based on intent
            if intent == "spotify":
                return control_spotify(command)

            elif intent == "browser":
                return browser_action(command)

            elif intent == "whatsapp":
                return whatsapp_action(command)

            elif intent == "greeting":
                return self._handle_greeting(command)

            elif intent == "goodbye":
                return self._handle_goodbye(command)

            elif intent == "assistant_control":
                return self._handle_assistant_control(command)

            elif intent == "time_date":
                return self._handle_time_date(command)

            elif intent == "weather":
                return "Weather functionality coming soon! I'll be able to check weather for you."

            elif intent == "general":
                return self._handle_general_query(command)

            else:
                return f"I understand you want help with {intent}, but I'm still learning that skill. Try asking about Spotify, browser control, or WhatsApp!"

        except Exception as e:
            print(f"❌ Command processing error: {e}")
            return "Sorry, I encountered an error processing your request."

    def _handle_greeting(self, command: str) -> str:
        """Handle greeting commands"""
        greetings = [
            "Hello! How can I help you today?",
            "Hi there! What can I do for you?",
            "Hey! I'm here to assist you.",
            "Hello! Ready to help with Spotify, browser, or WhatsApp tasks!"
        ]
        import random
        return random.choice(greetings)

    def _handle_goodbye(self, command: str) -> str:
        """Handle goodbye commands"""
        self.running = False
        return "Goodbye! Have a great day!"

    def _handle_assistant_control(self, command: str) -> str:
        """Handle assistant control commands"""
        command_lower = command.lower()

        if any(word in command_lower for word in ["stop listening", "stop", "quiet", "shut up"]):
            self.listening = False
            return "I'll stop listening now. Say 'Hey Samantha' to wake me up again."

        elif any(word in command_lower for word in ["what can you do", "help", "capabilities"]):
            return """I can help you with:
            🎵 Spotify: Play, pause, next, previous, volume control, playlists, liked songs
            🌐 Browser: Open websites, search, navigate
            💬 WhatsApp: Send messages, make calls, share files
            ⏰ Time and date queries
            Just say 'Hey Samantha' followed by your request!"""

        elif any(word in command_lower for word in ["volume up", "speak louder"]):
            current_volume = self.tts_engine.getProperty('volume')
            new_volume = min(1.0, current_volume + 0.1)
            self.tts_engine.setProperty('volume', new_volume)
            return "I'll speak louder now."

        elif any(word in command_lower for word in ["volume down", "speak quieter"]):
            current_volume = self.tts_engine.getProperty('volume')
            new_volume = max(0.1, current_volume - 0.1)
            self.tts_engine.setProperty('volume', new_volume)
            return "I'll speak more quietly now."

        else:
            return "I'm here and listening! How can I help you?"

    def _handle_time_date(self, command: str) -> str:
        """Handle time and date queries"""
        from datetime import datetime

        now = datetime.now()
        command_lower = command.lower()

        if "time" in command_lower:
            current_time = now.strftime("%I:%M %p")
            return f"The current time is {current_time}"

        elif "date" in command_lower:
            current_date = now.strftime("%A, %B %d, %Y")
            return f"Today is {current_date}"

        else:
            current_datetime = now.strftime("%I:%M %p on %A, %B %d, %Y")
            return f"It's currently {current_datetime}"

    def _handle_general_query(self, command: str) -> str:
        """Handle general queries"""
        responses = [
            "That's an interesting question! I'm focused on helping with Spotify, browser, and WhatsApp tasks right now.",
            "I'm still learning about that topic. For now, I can help with music, web browsing, and messaging.",
            "I don't have information about that yet, but I can help you with Spotify controls, web browsing, or WhatsApp!"
        ]
        import random
        return random.choice(responses)

    def run(self):
        """Main loop for the voice assistant"""
        print("\n🎤 Samantha is ready! Say 'Hey Samantha' to start...")
        print("💡 Available commands:")
        print("   🎵 Spotify: 'play music', 'pause', 'next song', 'volume up'")
        print("   🌐 Browser: 'open google', 'search for cats'")
        print("   💬 WhatsApp: 'message John hello', 'call Mom'")
        print("   ❌ Exit: 'goodbye' or Ctrl+C")
        print("-" * 50)

        try:
            while self.running:
                if not self.listening:
                    # Listen for wake word
                    speech = self._listen(timeout=1)
                    if speech and self._check_wake_word(speech):
                        self.listening = True
                        self._speak("Yes? How can I help you?")

                        # Listen for command
                        command_speech = self._listen(timeout=10)
                        if command_speech:
                            response = self._process_command(command_speech)
                            self._speak(response)
                        else:
                            self._speak("I didn't hear anything. Say 'Hey Samantha' to try again.")

                        self.listening = False

                else:
                    time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            self._speak("Goodbye!")
        except Exception as e:
            print(f"❌ Assistant error: {e}")
            self._speak("I encountered an error. Goodbye!")

def main():
    """Main function to start the assistant"""
    print("🚀 Starting Samantha Voice Assistant...")

    try:
        assistant = SamanthaAssistant()
        assistant.run()
    except Exception as e:
        print(f"❌ Failed to start assistant: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
