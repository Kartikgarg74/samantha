#!/usr/bin/env python3
"""
Unit tests for the Memory Manager module.
Tests memory storage, retrieval, context management, and persistence.
"""

import os
import sys
import json
import unittest
import tempfile
import time
from unittest.mock import patch, MagicMock, mock_open
import pytest
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the module to test
from assistant.memory_manager import MemoryManager


class TestMemoryManager(unittest.TestCase):
    """Test cases for the MemoryManager class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for memory storage
        self.temp_dir = tempfile.TemporaryDirectory()

        # Initialize with the test directory
        self.memory_manager = MemoryManager(data_dir=self.temp_dir.name)

    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        self.temp_dir.cleanup()

    def test_initialization(self):
        """Test memory manager initialization."""
        # Check if memory structures were initialized
        self.assertIsNotNone(self.memory_manager.conversation_history)
        self.assertIsInstance(self.memory_manager.conversation_history, list)
        self.assertIsNotNone(self.memory_manager.user_preferences)
        self.assertIsInstance(self.memory_manager.user_preferences, dict)
        self.assertIsNotNone(self.memory_manager.context_data)
        self.assertIsInstance(self.memory_manager.context_data, dict)

        # Check paths
        self.assertTrue(os.path.exists(self.memory_manager.data_dir))
        self.assertEqual(self.memory_manager.history_path,
                         os.path.join(self.temp_dir.name, "conversation_history.json"))
        self.assertEqual(self.memory_manager.preferences_path,
                         os.path.join(self.temp_dir.name, "user_preferences.json"))
        self.assertEqual(self.memory_manager.context_path,
                         os.path.join(self.temp_dir.name, "context_data.json"))

    def test_add_conversation_entry(self):
        """Test adding entries to conversation history."""
        # Add user message
        self.memory_manager.add_conversation_entry("user", "Hello, how are you?")

        # Add assistant message
        self.memory_manager.add_conversation_entry("assistant", "I'm doing well, thank you!")

        # Verify messages were added
        self.assertEqual(len(self.memory_manager.conversation_history), 2)

        # Verify content
        self.assertEqual(self.memory_manager.conversation_history[0]["text"], "Hello, how are you?")
        self.assertEqual(self.memory_manager.conversation_history[0]["speaker"], "user")
        self.assertEqual(self.memory_manager.conversation_history[1]["text"], "I'm doing well, thank you!")
        self.assertEqual(self.memory_manager.conversation_history[1]["speaker"], "assistant")

    def test_get_conversation_history(self):
        """Test retrieving conversation history."""
        # Add several conversation entries
        for i in range(5):
            self.memory_manager.add_conversation_entry("user" if i % 2 == 0 else "assistant", f"Message {i}")

        # Get all history
        history = self.memory_manager.get_conversation_history()
        self.assertEqual(len(history), 5)

        # Get limited history
        limited_history = self.memory_manager.get_conversation_history(n_recent=3)
        self.assertEqual(len(limited_history), 3)

        # Check order (should be chronological)
        self.assertEqual(limited_history[0]["text"], "Message 2")
        self.assertEqual(limited_history[1]["text"], "Message 3")
        self.assertEqual(limited_history[2]["text"], "Message 4")

    def test_user_preferences(self):
        """Test setting and getting user preferences."""
        # Test setting a preference
        self.memory_manager.set_user_preference("preferred_voice", "female")

        # Verify preference was set
        self.assertEqual(self.memory_manager.user_preferences["preferred_voice"], "female")

        # Test getting the preference
        voice = self.memory_manager.get_user_preference("preferred_voice")
        self.assertEqual(voice, "female")

        # Test default value for non-existent preference
        unknown = self.memory_manager.get_user_preference("unknown", default="default_value")
        self.assertEqual(unknown, "default_value")

        # Test updating a preference
        self.memory_manager.set_user_preference("preferred_voice", "male")
        self.assertEqual(self.memory_manager.get_user_preference("preferred_voice"), "male")

    def test_context_data(self):
        """Test setting and getting context data."""
        # Test setting context data
        self.memory_manager.set_context_data("last_action", "play_music")

        # Verify context was set
        self.assertEqual(self.memory_manager.context_data["last_action"], "play_music")

        # Test getting context data
        action = self.memory_manager.get_context_data("last_action")
        self.assertEqual(action, "play_music")

        # Test default value
        unknown = self.memory_manager.get_context_data("unknown", default="none")
        self.assertEqual(unknown, "none")

    def test_clear_conversation_history(self):
        """Test clearing conversation history."""
        # Add some messages
        self.memory_manager.add_conversation_entry("user", "Test message")
        self.memory_manager.add_conversation_entry("assistant", "Test reply")

        # Clear history
        self.memory_manager.clear_conversation_history()

        # Verify conversations were cleared
        self.assertEqual(len(self.memory_manager.conversation_history), 0)

        # Verify preferences were not affected
        self.memory_manager.set_user_preference("test", "value")
        self.memory_manager.clear_conversation_history()
        self.assertEqual(self.memory_manager.get_user_preference("test"), "value")

    def test_persistence(self):
        """Test that memory is persisted to disk."""
        # Add data
        self.memory_manager.add_conversation_entry("user", "Test persistence")
        self.memory_manager.set_user_preference("theme", "dark")
        self.memory_manager.set_context_data("session_id", "123456")

        # Create a new memory manager with the same data directory
        # This should load the data we just saved
        new_manager = MemoryManager(data_dir=self.temp_dir.name)

        # Verify data was loaded
        self.assertEqual(len(new_manager.conversation_history), 1)
        self.assertEqual(new_manager.conversation_history[0]["text"], "Test persistence")
        self.assertEqual(new_manager.user_preferences["theme"], "dark")
        self.assertEqual(new_manager.context_data["session_id"], "123456")

    def test_export_and_import(self):
        """Test exporting and importing memory data."""
        # Add data to export
        self.memory_manager.add_conversation_entry("user", "Test export")
        self.memory_manager.set_user_preference("language", "en-US")
        self.memory_manager.set_context_data("last_query", "weather")

        # Export to a temporary file
        export_file = os.path.join(self.temp_dir.name, "export.json")
        success = self.memory_manager.export_memory(export_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_file))

        # Clear data
        self.memory_manager.clear_conversation_history()
        self.memory_manager.user_preferences = {}
        self.memory_manager.context_data = {}
        self._save_all(self.memory_manager)

        # Import from the file
        success = self.memory_manager.import_memory(export_file)
        self.assertTrue(success)

        # Verify data was imported
        self.assertEqual(len(self.memory_manager.conversation_history), 1)
        self.assertEqual(self.memory_manager.conversation_history[0]["text"], "Test export")
        self.assertEqual(self.memory_manager.user_preferences["language"], "en-US")
        self.assertEqual(self.memory_manager.context_data["last_query"], "weather")

    def _save_all(self, manager):
        """Helper to save all memory structures."""
        manager._save_conversation_history()
        manager._save_user_preferences()
        manager._save_context_data()


# Additional tests with pytest

@pytest.fixture
def memory_manager():
    """Fixture for creating a MemoryManager instance."""
    # Use a temporary directory for memory storage
    with tempfile.TemporaryDirectory() as temp_dir:
        yield MemoryManager(data_dir=temp_dir)


def test_conversation_timestamps(memory_manager):
    """Test that conversation entries have timestamps."""
    memory_manager.add_conversation_entry("user", "Test timestamp message")

    # Check if timestamp was added
    assert "timestamp" in memory_manager.conversation_history[0]
    # Check that timestamp is in ISO format
    try:
        datetime.fromisoformat(memory_manager.conversation_history[0]["timestamp"])
        is_valid = True
    except ValueError:
        is_valid = False
    assert is_valid


@pytest.mark.parametrize("speaker,message", [
    ("user", "Hello there!"),
    ("assistant", "Hi, how can I help?"),
    ("system", "Processing request...")
])
def test_parameterized_conversation_add(memory_manager, speaker, message):
    """Test adding different types of conversation entries."""
    memory_manager.add_conversation_entry(speaker, message)

    # Check if entry was added correctly
    assert len(memory_manager.conversation_history) == 1
    assert memory_manager.conversation_history[0]["text"] == message
    assert memory_manager.conversation_history[0]["speaker"] == speaker


def test_persistence_error_handling():
    """Test error handling when saving to an invalid location."""
    # Create a memory manager with a problematic directory path
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file where we want a directory to be (to cause a failure)
        invalid_dir = os.path.join(temp_dir, "invalid")
        with open(invalid_dir, 'w') as f:
            f.write("This is a file, not a directory")

        # Create memory manager with the parent directory so initialization works
        memory_manager = MemoryManager(data_dir=temp_dir)

        # Replace the data_dir with the invalid path
        memory_manager.data_dir = invalid_dir

        # Add a message (should not raise an exception despite the invalid path)
        try:
            memory_manager.add_conversation_entry("user", "Test error handling")
            # If we get here without an exception, the test passes
            assert True
        except Exception:
            # Should not reach here
            assert False, "add_conversation_entry should handle file errors gracefully"


if __name__ == "__main__":
    unittest.main()
