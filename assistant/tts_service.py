"""
Text-to-Speech service for Samantha Voice Assistant.
Provides multiple TTS backends with graceful fallbacks.
"""

import platform
import subprocess
import sys
import os

class TTSService:
    """Text-to-Speech service with multiple backend options"""

    def __init__(self):
        """Initialize the TTS service with the best available backend"""
        self.backend = None
        self.voice_id = None
        self.rate = 180
        self.volume = 0.8

        # Try to initialize backends in order of preference
        if self._try_init_pyttsx3():
            self.backend = "pyttsx3"
        elif self._try_init_system():
            self.backend = "system"
        else:
            print("❌ No TTS backend available!")
            print("Installing required packages...")
            self._install_dependencies()

            # Try again after installing dependencies
            if self._try_init_pyttsx3():
                self.backend = "pyttsx3"
            elif self._try_init_system():
                self.backend = "system"
            else:
                raise RuntimeError("Failed to initialize any TTS backend!")

        print(f"✅ TTS initialized using {self.backend} backend")

    def _install_dependencies(self):
        """Install required dependencies"""
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pyobjc", "pyttsx3"])
            else:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pyttsx3"])
        except Exception as e:
            print(f"❌ Failed to install dependencies: {e}")

    def _try_init_pyttsx3(self):
        """Try to initialize pyttsx3"""
        try:
            import pyttsx3
            self.pyttsx3_engine = pyttsx3.init()

            # Configure voice
            voices = self.pyttsx3_engine.getProperty('voices')
            if voices:
                # Try to use a female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower() or 'susan' in voice.name.lower():
                        self.pyttsx3_engine.setProperty('voice', voice.id)
                        self.voice_id = voice.id
                        break
                else:
                    # Use first available voice
                    self.pyttsx3_engine.setProperty('voice', voices[0].id)
                    self.voice_id = voices[0].id

            # Set speech rate and volume
            self.pyttsx3_engine.setProperty('rate', self.rate)
            self.pyttsx3_engine.setProperty('volume', self.volume)

            return True
        except Exception as e:
            print(f"⚠️ pyttsx3 initialization warning: {e}")
            return False

    def _try_init_system(self):
        """Try to initialize system speech commands"""
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                # Test if "say" command is available
                subprocess.run(["say", "-v", "?"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.voice = "Samantha"  # Default macOS female voice
                return True
            elif system == "Windows":
                # Test if PowerShell is available with speech synthesis
                cmd = 'powershell -Command "Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.GetInstalledVoices()"'
                subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return True
            elif system == "Linux":
                # Test if espeak is available
                subprocess.run(["espeak", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return True
            return False
        except Exception as e:
            print(f"⚠️ System speech initialization warning: {e}")
            return False

    def speak(self, text):
        """Convert text to speech"""
        if not text:
            return

        print(f"🗣️  Samantha: {text}")

        if self.backend == "pyttsx3":
            try:
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
            except Exception as e:
                print(f"❌ pyttsx3 speech error: {e}")
                # Fall back to system speech
                self._speak_system(text)
        else:
            self._speak_system(text)

    def _speak_system(self, text):
        """Use system commands for TTS"""
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["say", "-v", self.voice, text])
            elif system == "Windows":
                # Use PowerShell for speech synthesis
                cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak(\'{text}\')"'
                subprocess.run(cmd, shell=True)
            elif system == "Linux":
                subprocess.run(["espeak", text])
        except Exception as e:
            print(f"❌ System speech error: {e}")

    def set_voice(self, voice_id):
        """Set the TTS voice"""
        self.voice_id = voice_id
        if self.backend == "pyttsx3":
            self.pyttsx3_engine.setProperty('voice', voice_id)
        else:
            self.voice = voice_id

    def set_rate(self, rate):
        """Set the speech rate"""
        self.rate = rate
        if self.backend == "pyttsx3":
            self.pyttsx3_engine.setProperty('rate', rate)

    def set_volume(self, volume):
        """Set the speech volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        if self.backend == "pyttsx3":
            self.pyttsx3_engine.setProperty('volume', self.volume)
