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

class SessionManager:
    """Manages assistant session data and persistence"""

    def __init__(self, session_file=None):
        """
        Initialize session manager

        Args:
            session_file: Path to session file (default: based on config)
        """
        self.session_file = session_file or config_manager.get('session.file_path', 'assistant_session.json')
        self.session_id = str(uuid.uuid4())
        self.start_time = datetime.now()
        self.last_activity_time = self.start_time
        self.command_count = 0
        self.session_data = {
            'settings': {},
            'state': {},
            'metrics': {
                'commands_processed': 0,
                'errors': 0,
                'successful_commands': 0
            }
        }

        # Try to load previous session
        self._load_session()

    def _load_session(self):
        """Load session data from file if available"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    saved_session = json.load(f)

                # Check if we should restore the session
                if config_manager.get('session.restore_on_start', True):
                    # Only restore settings and certain state elements
                    if 'settings' in saved_session:
                        self.session_data['settings'] = saved_session['settings']

                    logger.info(f"Restored settings from previous session")
        except Exception as e:
            logger.error(f"Failed to load session data: {e}")

    def save(self):
        """Save current session data to file"""
        try:
            # Update session metrics
            self.session_data['metrics']['session_duration'] = str(datetime.now() - self.start_time)
            self.session_data['metrics']['last_activity'] = self.last_activity_time.isoformat()
            self.session_data['id'] = self.session_id

            with open(self.session_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)

            logger.debug("Session data saved successfully")
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")

    def update_activity(self):
        """Update last activity time"""
        self.last_activity_time = datetime.now()

    def increment_command_count(self, success=True):
        """
        Increment command counter

        Args:
            success: Whether the command was successful
        """
        self.command_count += 1
        self.session_data['metrics']['commands_processed'] += 1

        if success:
            self.session_data['metrics']['successful_commands'] += 1
        else:
            self.session_data['metrics']['errors'] += 1

    def get_setting(self, key, default=None):
        """Get a session setting"""
        return self.session_data['settings'].get(key, default)

    def set_setting(self, key, value):
        """Set a session setting"""
        self.session_data['settings'][key] = value

    def get_state(self, key, default=None):
        """Get a state value"""
        return self.session_data['state'].get(key, default)

    def set_state(self, key, value):
        """Set a state value"""
        self.session_data['state'][key] = value
