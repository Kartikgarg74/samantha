#!/usr/bin/env python3
"""Samantha - AI Voice Assistant with enhanced user experience and feedback."""

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

# Add console handler if enabled
if config_manager.get('logging.console_output', True):
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(logging_format))
    logger.addHandler(console_handler)

def main():
    """Main function to start the assistant with improved error handling"""
    start_time = datetime.now()
    logger.info(f"🚀 Starting Samantha Voice Assistant...")
    logger.info(f"Current Date and Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    logger.info(f"Current User: {os.getlogin()}")

    # Check if config file was specified as command line argument
    if len(sys.argv) > 1 and sys.argv[1].endswith('.json'):
        config_path = sys.argv[1]
        from assistant.config_manager import ConfigManager
        global config_manager
        config_manager = ConfigManager(config_path)
        logger.info(f"Using custom config file: {config_path}")

    # Print startup banner
    print("\n" + "=" * 50)
    print("🤖 SAMANTHA VOICE ASSISTANT")
    print(f"🚀 Starting up at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        # Initialization progress
        for i in range(3):
            sys.stdout.write("\rInitializing" + "." * (i + 1) + " " * 10)
            sys.stdout.flush()
            time.sleep(0.3)
        print()

        # Create and run the assistant
        assistant = SamanthaAssistant()
        assistant.run()
    except Exception as e:
        # Enhanced error handling with traceback
        logger.error(f"❌ Critical error: {e}")
        logger.error(traceback.format_exc())

        print("\n" + "=" * 50)
        print("❌ CRITICAL ERROR")
        print(f"The assistant failed to start: {str(e)}")
        print("\nTraceback (for debugging):")
        traceback.print_exc()
        print("=" * 50)
        sys.exit(1)

if __name__ == "__main__":
    main()
