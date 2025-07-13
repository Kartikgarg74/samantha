"""
Memory Manager Module

This module manages user interactions history, preferences, and session data.
It provides persistence and recall capabilities for the assistant.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union


class MemoryManager:
    """
    Manages conversation history, user preferences, and session data.
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize the memory manager with a data directory.

        Args:
            data_dir: Directory to store memory data. If None, uses a default location.
        """
        if data_dir is None:
            # Use a sensible default if no directory is specified
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_dir = os.path.join(base_dir, "data", "memory")
        else:
            self.data_dir = data_dir

        # Ensure the directory exists
        os.makedirs(self.data_dir, exist_ok=True)

        # Define paths for different types of memory
        self.history_path = os.path.join(self.data_dir, "conversation_history.json")
        self.preferences_path = os.path.join(self.data_dir, "user_preferences.json")
        self.context_path = os.path.join(self.data_dir, "context_data.json")

        # Initialize memory structures
        self.conversation_history: List[Dict[str, Any]] = []
        self.user_preferences: Dict[str, Any] = {}
        self.context_data: Dict[str, Any] = {}

        # Load existing data if available
        self._load_memory()

    def _load_memory(self) -> None:
        """Load all memory data from disk."""
        self._load_conversation_history()
        self._load_user_preferences()
        self._load_context_data()

    def _load_conversation_history(self) -> None:
        """Load conversation history from disk."""
        try:
            if os.path.exists(self.history_path) and os.path.getsize(self.history_path) > 0:
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    self.conversation_history = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading conversation history: {e}")
            self.conversation_history = []

    def _load_user_preferences(self) -> None:
        """Load user preferences from disk."""
        try:
            if os.path.exists(self.preferences_path) and os.path.getsize(self.preferences_path) > 0:
                with open(self.preferences_path, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading user preferences: {e}")
            self.user_preferences = {}

    def _load_context_data(self) -> None:
        """Load context data from disk."""
        try:
            if os.path.exists(self.context_path) and os.path.getsize(self.context_path) > 0:
                with open(self.context_path, 'r', encoding='utf-8') as f:
                    self.context_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading context data: {e}")
            self.context_data = {}

    def _save_conversation_history(self) -> None:
        """Save conversation history to disk."""
        try:
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, indent=2)
        except Exception as e:
            print(f"Error saving conversation history: {e}")

    def _save_user_preferences(self) -> None:
        """Save user preferences to disk."""
        try:
            with open(self.preferences_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, indent=2)
        except Exception as e:
            print(f"Error saving user preferences: {e}")

    def _save_context_data(self) -> None:
        """Save context data to disk."""
        try:
            with open(self.context_path, 'w', encoding='utf-8') as f:
                json.dump(self.context_data, f, indent=2)
        except Exception as e:
            print(f"Error saving context data: {e}")

    def add_conversation_entry(self, speaker: str, text: str,
                              timestamp: Optional[datetime] = None) -> None:
        """
        Add a new entry to the conversation history.

        Args:
            speaker: Who spoke (user, assistant, system)
            text: What was said
            timestamp: When it was said (defaults to current time)
        """
        if timestamp is None:
            timestamp = datetime.now()

        entry = {
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp.isoformat()
        }

        self.conversation_history.append(entry)
        self._save_conversation_history()

    def get_conversation_history(self, n_recent: int = None) -> List[Dict[str, Any]]:
        """
        Get conversation history, optionally limited to recent entries.

        Args:
            n_recent: Number of most recent entries to return. If None, returns all.

        Returns:
            List of conversation entries
        """
        if n_recent is None:
            return self.conversation_history
        return self.conversation_history[-n_recent:]

    def set_user_preference(self, key: str, value: Any) -> None:
        """
        Set a user preference.

        Args:
            key: Preference key
            value: Preference value
        """
        self.user_preferences[key] = value
        self._save_user_preferences()

    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """
        Get a user preference.

        Args:
            key: Preference key
            default: Default value if preference doesn't exist

        Returns:
            Preference value or default
        """
        return self.user_preferences.get(key, default)

    def set_context_data(self, key: str, value: Any) -> None:
        """
        Set context data.

        Args:
            key: Context key
            value: Context value
        """
        self.context_data[key] = value
        self._save_context_data()

    def get_context_data(self, key: str, default: Any = None) -> Any:
        """
        Get context data.

        Args:
            key: Context key
            default: Default value if context doesn't exist

        Returns:
            Context value or default
        """
        return self.context_data.get(key, default)

    def clear_conversation_history(self) -> None:
        """Clear all conversation history."""
        self.conversation_history = []
        self._save_conversation_history()

    def export_memory(self, filepath: str) -> bool:
        """
        Export all memory data to a file.

        Args:
            filepath: Path to export file

        Returns:
            True if successful, False otherwise
        """
        try:
            memory_data = {
                "conversation_history": self.conversation_history,
                "user_preferences": self.user_preferences,
                "context_data": self.context_data,
                "exported_at": datetime.now().isoformat()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting memory: {e}")
            return False

    def import_memory(self, filepath: str) -> bool:
        """
        Import memory data from a file.

        Args:
            filepath: Path to import file

        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(filepath):
                print(f"Import file not found: {filepath}")
                return False

            with open(filepath, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)

            if "conversation_history" in memory_data:
                self.conversation_history = memory_data["conversation_history"]
                self._save_conversation_history()

            if "user_preferences" in memory_data:
                self.user_preferences = memory_data["user_preferences"]
                self._save_user_preferences()

            if "context_data" in memory_data:
                self.context_data = memory_data["context_data"]
                self._save_context_data()

            return True
        except Exception as e:
            print(f"Error importing memory: {e}")
            return False


# Create an instance for easy importing
memory_manager = MemoryManager()


if __name__ == "__main__":
    # Example usage
    mm = MemoryManager()
    mm.add_conversation_entry("user", "Hello, how are you?")
    mm.add_conversation_entry("assistant", "I'm doing well, thank you! How can I help you today?")
    mm.set_user_preference("theme", "dark")

    print(f"Conversation history: {mm.get_conversation_history()}")
    print(f"User preferences: {mm.user_preferences}")
