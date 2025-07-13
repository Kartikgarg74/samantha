#!/usr/bin/env python3
"""
Memory Manager Module

This module handles conversation history, context management, and user preferences.
It provides persistence across sessions and supports context-aware responses.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from collections import deque
import threading

# Configure logger
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("MemoryManager")

class MemoryManager:
    """
    Manages conversation history, user preferences, and contextual information.
    Provides persistence across assistant sessions.
    """

    def __init__(self, file_path=None, max_conversations=50,
                 max_conversation_length=20, persist_user_preferences=True,
                 context_expiration_days=7):
        """
        Initialize the memory manager.

        Args:
            file_path (str): Path to the memory persistence file
            max_conversations (int): Maximum number of conversations to store
            max_conversation_length (int): Maximum number of messages in a conversation
            persist_user_preferences (bool): Whether to save user preferences to disk
            context_expiration_days (int): Number of days before conversation context expires
        """
        self._conversations = []
        self._context = {}
        self._user_preferences = {}
        self._max_conversations = max_conversations
        self._max_conversation_length = max_conversation_length
        self._persist_preferences = persist_user_preferences
        self._context_expiration_days = context_expiration_days
        self._lock = threading.RLock()

        # Set default file path if not provided
        if file_path is None:
            home_dir = os.path.expanduser("~")
            self._file_path = os.path.join(home_dir, ".samantha", "memory.json")
        else:
            self._file_path = file_path

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self._file_path), exist_ok=True)

        # Load memory from file if it exists
        self._load_from_file()

    def add_user_message(self, text):
        """
        Add a user message to conversation history.

        Args:
            text (str): The message text
        """
        with self._lock:
            self._add_message(text, "user")

    def add_assistant_message(self, text, action=None):
        """
        Add an assistant message to conversation history.

        Args:
            text (str): The message text
            action (str, optional): The action taken by the assistant
        """
        with self._lock:
            message = self._add_message(text, "assistant")
            if action:
                message["action"] = action

    def _add_message(self, text, speaker):
        """
        Add a message to the conversation history.

        Args:
            text (str): The message text
            speaker (str): Who is speaking ('user' or 'assistant')

        Returns:
            dict: The message that was added
        """
        message = {
            "text": text,
            "speaker": speaker,
            "timestamp": datetime.now().isoformat()
        }

        self._conversations.append(message)

        # Limit the number of messages
        if len(self._conversations) > self._max_conversation_length:
            self._conversations = self._conversations[-self._max_conversation_length:]

        return message

    def get_conversation_context(self):
        """
        Get recent conversation context for contextual understanding.

        Returns:
            dict: Context information including recent exchanges
        """
        with self._lock:
            context = {
                "recent_exchanges": []
            }

            if not self._conversations:
                return context

            # Filter out expired conversations
            cutoff_date = datetime.now() - timedelta(days=self._context_expiration_days)
            recent_conversations = []

            for message in self._conversations:
                try:
                    msg_time = datetime.fromisoformat(message["timestamp"])
                    if msg_time >= cutoff_date:
                        recent_conversations.append(message)
                except (ValueError, KeyError):
                    # If timestamp is invalid, keep the message anyway
                    recent_conversations.append(message)

            # Group into user-assistant exchanges
            exchanges = []
            current_exchange = {"user": None, "assistant": None}

            for message in recent_conversations:
                if message["speaker"] == "user":
                    if current_exchange["user"] is not None:
                        # Start a new exchange
                        if current_exchange["assistant"] is not None:
                            exchanges.append(current_exchange.copy())
                        current_exchange = {"user": None, "assistant": None}
                    current_exchange["user"] = message["text"]
                elif message["speaker"] == "assistant":
                    if current_exchange["user"] is not None:
                        current_exchange["assistant"] = message["text"]
                        if "action" in message:
                            current_exchange["action"] = message["action"]
                        exchanges.append(current_exchange.copy())
                        current_exchange = {"user": None, "assistant": None}

            # Add the last exchange if it's complete
            if current_exchange["user"] is not None and current_exchange["assistant"] is not None:
                exchanges.append(current_exchange)

            context["recent_exchanges"] = exchanges
            return context

    def set_context(self, key, value):
        """
        Set a context variable.

        Args:
            key (str): Context key
            value: Context value
        """
        with self._lock:
            self._context[key] = value

    def get_context(self, key, default=None):
        """
        Get a context variable.

        Args:
            key (str): Context key
            default: Default value if key doesn't exist

        Returns:
            The context value or default
        """
        with self._lock:
            return self._context.get(key, default)

    def set_user_preference(self, category, key, value):
        """
        Set a user preference.

        Args:
            category (str): Preference category
            key (str): Preference key
            value: Preference value
        """
        with self._lock:
            if category not in self._user_preferences:
                self._user_preferences[category] = {}
            self._user_preferences[category][key] = value

            if self._persist_preferences:
                self._save_to_file()

    def get_user_preference(self, category, key, default=None):
        """
        Get a user preference.

        Args:
            category (str): Preference category
            key (str): Preference key
            default: Default value if preference doesn't exist

        Returns:
            The preference value or default
        """
        with self._lock:
            if category in self._user_preferences and key in self._user_preferences[category]:
                return self._user_preferences[category][key]
            return default

    def get_user_preferences(self):
        """
        Get all user preferences.

        Returns:
            dict: All user preferences
        """
        with self._lock:
            return self._user_preferences.copy()

    def _load_from_file(self):
        """Load memory from persistent storage."""
        if not os.path.exists(self._file_path):
            return

        try:
            with open(self._file_path, 'r') as f:
                data = json.load(f)

            if "conversations" in data and isinstance(data["conversations"], list):
                self._conversations = data["conversations"]
                # Limit to max size
                if len(self._conversations) > self._max_conversations:
                    self._conversations = self._conversations[-self._max_conversations:]

            if "context" in data and isinstance(data["context"], dict):
                self._context = data["context"]

            if "user_preferences" in data and isinstance(data["user_preferences"], dict):
                self._user_preferences = data["user_preferences"]

            logger.info(f"Memory loaded from {self._file_path}")
        except Exception as e:
            logger.error(f"Error loading memory: {str(e)}")

    def _save_to_file(self):
        """Save memory to persistent storage."""
        try:
            data = {
                "conversations": self._conversations,
                "context": self._context,
                "user_preferences": self._user_preferences
            }

            # Ensure directory exists
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)

            with open(self._file_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Memory saved to {self._file_path}")
        except Exception as e:
            logger.error(f"Error saving memory: {str(e)}")

    def cleanup(self):
        """Clean up resources before shutting down."""
        with self._lock:
            self._save_to_file()

    def create_system_prompt(self, intent=None):
        """
        Create a system prompt with relevant context for a specific intent.

        Args:
            intent (str, optional): The intent for which to create the prompt

        Returns:
            str: A system prompt with context
        """
        with self._lock:
            # Base system prompt
            prompt = "You are an AI assistant named Samantha. "
            prompt += "You are helpful, concise, and friendly. "

            # Add user preference context
            user_prefs = self.get_user_preferences()
            if user_prefs:
                prompt += "\n\nUser preferences:\n"
                for category, prefs in user_prefs.items():
                    for key, value in prefs.items():
                        prompt += f"- {category} {key}: {value}\n"

            # Add conversation context
            context = self.get_conversation_context()
            recent_exchanges = context.get("recent_exchanges", [])

            if recent_exchanges:
                prompt += "\n\nRecent conversation:\n"
                for exchange in recent_exchanges[-3:]:  # Last 3 exchanges
                    prompt += f"User: {exchange.get('user', '')}\n"
                    prompt += f"You: {exchange.get('assistant', '')}\n"

            # Add intent-specific context
            if intent:
                intent_context = self.get_context(f"intent_{intent}")
                if intent_context:
                    prompt += f"\n\nContext for {intent}:\n{intent_context}\n"

                if intent == "spotify":
                    current_song = self.get_context("current_song")
                    if current_song:
                        prompt += f"\nCurrently playing: {current_song}\n"

            return prompt

# Default memory manager instance
memory_manager = MemoryManager()

if __name__ == "__main__":
    # Test code for direct execution
    memory = MemoryManager()
    memory.add_user_message("Hello Samantha!")
    memory.add_assistant_message("Hello! How can I help you today?")
    memory.set_user_preference("personal", "name", "Alex")

    print("Context:", memory.get_conversation_context())
    memory.cleanup()
