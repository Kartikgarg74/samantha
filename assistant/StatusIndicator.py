import os
import time
import sys
import threading
import random
import json
import signal
import traceback
from datetime import datetime
from typing import List, Dict, Tuple, Any, Optional
import uuid

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import assistant modules
from assistant.memory_manager import MemoryManager, memory_manager
from assistant.speech_recognition_service import SpeechRecognitionService, speech_recognition_service
from assistant.tts_service import TTSService, tts_service
from assistant.intent_classifier import IntentClassifier, intent_classifier
from assistant.spotify_control import control_spotify
from assistant.browser_control import browser_action
from assistant.whatsapp_integration import whatsapp_action
from assistant.system_prompts import prompt_manager
from assistant.command_processor import CommandProcessor
from assistant.config_manager import config_manager
from assistant.StatusIndicator import StatusIndicator
from assistant.SessionManager import SessionManager
from assistant.SamanthaAssistant import SamanthaAssistant
# Configure logging based on config
import logging
logging_level = config_manager.get('logging.level', 'INFO')
logging_format = config_manager.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.basicConfig(
    level=getattr(logging, logging_level),
    format=logging_format,
    filename=config_manager.get('logging.file_path'),
    filemode='a'
)
logger = logging.getLogger("Samantha")

class StatusIndicator:
    """Visual status indicators for the assistant"""

    # ASCII/emoji indicators
    THINKING = ["🤔", "⏳", "🧠", "💭"]
    LISTENING = ["👂", "🎤", "🔊", "📢"]
    SPEAKING = ["🗣️", "💬", "🔈", "📣"]
    ERROR = ["❌", "⚠️", "🚫", "❗"]
    SUCCESS = ["✅", "👍", "🎉", "✨"]

    @staticmethod
    def show_thinking(message="Thinking...", end="\r"):
        """Display thinking indicator"""
        for i in range(5):  # Animate for a short time
            for indicator in StatusIndicator.THINKING:
                sys.stdout.write(f"{indicator} {message}" + " " * 20 + end)
                sys.stdout.flush()
                time.sleep(0.2)

    @staticmethod
    def show_listening(duration=None, end="\r"):
        """Display listening indicator with optional countdown"""
        start_time = time.time()

        if duration:
            while time.time() - start_time < duration:
                for indicator in StatusIndicator.LISTENING:
                    remaining = max(0, duration - (time.time() - start_time))
                    sys.stdout.write(f"{indicator} Listening... ({remaining:.1f}s remaining)" + " " * 20 + end)
                    sys.stdout.flush()
                    time.sleep(0.2)
                    if time.time() - start_time >= duration:
                        break
        else:
            for indicator in StatusIndicator.LISTENING:
                sys.stdout.write(f"{indicator} Listening..." + " " * 20 + end)
                sys.stdout.flush()
                time.sleep(0.2)

    @staticmethod
    def show_speaking():
        """Display speaking indicator"""
        for indicator in StatusIndicator.SPEAKING:
            sys.stdout.write(f"{indicator} Speaking..." + " " * 20 + "\r")
            sys.stdout.flush()
            time.sleep(0.2)

    @staticmethod
    def show_error(message):
        """Display error message"""
        indicator = random.choice(StatusIndicator.ERROR)
        print(f"{indicator} Error: {message}" + " " * 20)

    @staticmethod
    def show_success(message):
        """Display success message"""
        indicator = random.choice(StatusIndicator.SUCCESS)
        print(f"{indicator} {message}" + " " * 20)

    @staticmethod
    def clear_line():
        """Clear the current line"""
        sys.stdout.write(" " * 50 + "\r")
        sys.stdout.flush()
