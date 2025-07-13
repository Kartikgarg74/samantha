#!/usr/bin/env python3
"""
Unit tests for the Memory Manager.
Tests conversation history, context management, and user preferences.
"""

import os
import sys
import unittest
import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from assistant.memory_manager import MemoryManager

class TestMemoryManager(unittest.TestCase):
    """Test cases for memory manager functionality."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.memory_file = os.path.join(self.test_dir, "test_memory.json")

        # Create a memory manager with test settings
        self.memory = MemoryManager(
            max_conversations=5,
            max_conversation_length=3,
            persist_user_preferences=True,
            file_path=self.memory_file
        )

    def tearDown(self):
        """Tear down test fixtures after each test."""
        # Remove temporary test directory
        shutil.rmtree(self.test_dir)

    def test_add_user_message(self):
        """Test adding user messages to memory."""
        # Add some test messages
        self.memory.add_user_message("Hello assistant")
        self.memory.add_user_message("How are you today?")

        # Check that messages were stored
        conversations = self.memory._conversations
        self.assertEqual(len(conversations), 2)
        self.assertEqual(conversations[0]["text"], "Hello assistant")
        self.assertEqual(conversations[0]["speaker"], "user")
        self.assertEqual(conversations[1]["text"], "How are you today?")

        # Verify timestamps were added
        self.assertTrue("timestamp" in conversations[0])
        timestamp = conversations[0]["timestamp"]
        self.assertTrue(isinstance(datetime.fromisoformat(timestamp), datetime))

    def test_add_assistant_message(self):
        """Test adding assistant messages to memory."""
        # Add test message with action
        self.memory.add_assistant_message("I can help you with that", action="general_response")

        # Check message and action were stored
        conversations = self.memory._conversations
        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0]["text"], "I can help you with that")
        self.assertEqual(conversations[0]["speaker"], "assistant")
        self.assertEqual(conversations[0]["action"], "general_response")

    def test_max_conversation_length(self):
        """Test that conversation length is limited as specified."""
        # Add more messages than the limit
        for i in range(5):  # Max is set to 3
            self.memory.add_user_message(f"Test message {i}")

        # Check that only the most recent messages are kept
        conversations = self.memory._conversations
        self.assertEqual(len(conversations), 3)  # Should be limited to 3
        self.assertEqual(conversations[0]["text"], "Test message 2")
        self.assertEqual(conversations[1]["text"], "Test message 3")
        self.assertEqual(conversations[2]["text"], "Test message 4")

    def test_get_conversation_context(self):
        """Test retrieving conversation context."""
        # Add some test conversation
        self.memory.add_user_message("What's the weather like?")
        self.memory.add_assistant_message("It's sunny today", action="weather_info")
        self.memory.add_user_message("Thank you")

        # Get the context
        context = self.memory.get_conversation_context()

        # Check that context contains the expected data
        self.assertIn("recent_exchanges", context)
        exchanges = context["recent_exchanges"]
        self.assertEqual(len(exchanges), 2)  # Should have 2 exchanges (3 messages)

        # Check the first exchange
        first_exchange = exchanges[0]
        self.assertEqual(first_exchange["user"], "What's the weather like?")
        self.assertEqual(first_exchange["assistant"], "It's sunny today")
        self.assertEqual(first_exchange["action"], "weather_info")

    def test_set_get_context(self):
        """Test setting and getting context variables."""
        # Set some context variables
        self.memory.set_context("current_app", "spotify")
        self.memory.set_context("playing_song", "Bohemian Rhapsody")

        # Get context variables
        app = self.memory.get_context("current_app")
        song = self.memory.get_context("playing_song")

        # Check values
        self.assertEqual(app, "spotify")
        self.assertEqual(song, "Bohemian Rhapsody")

        # Test default value for missing key
        missing = self.memory.get_context("nonexistent_key", default="not found")
        self.assertEqual(missing, "not found")

    def test_user_preferences(self):
        """Test storing and retrieving user preferences."""
        # Set some preferences
        self.memory.set_user_preference("personal", "name", "John")
        self.memory.set_user_preference("music", "favorite_genre", "Rock")
        self.memory.set_user_preference("music", "favorite_artist", "Queen")

        # Get all preferences
        prefs = self.memory.get_user_preferences()

        # Check values
        self.assertEqual(prefs["personal"]["name"], "John")
        self.assertEqual(prefs["music"]["favorite_genre"], "Rock")
        self.assertEqual(prefs["music"]["favorite_artist"], "Queen")

    def test_save_load_memory(self):
        """Test saving and loading memory from file."""
        # Add some data
        self.memory.add_user_message("Remember this message")
        self.memory.set_user_preference("personal", "name", "Alice")
        self.memory.set_context("favorite_color", "blue")

        # Save memory
        self.memory._save_to_file()

        # Create a new memory manager to load from the same file
        new_memory = MemoryManager(file_path=self.memory_file)

        # Check if loaded data matches
        self.assertEqual(new_memory._conversations[0]["text"], "Remember this message")
        self.assertEqual(new_memory._user_preferences["personal"]["name"], "Alice")
        self.assertEqual(new_memory._context["favorite_color"], "blue")

    def test_cleanup(self):
        """Test cleanup method saves data."""
        # Add some data
        self.memory.add_user_message("Save on cleanup")

        # Mock the save method to check if it's called
        with patch.object(self.memory, '_save_to_file') as mock_save:
            self.memory.cleanup()
            mock_save.assert_called_once()

    def test_create_system_prompt(self):
        """Test creation of system prompt with context."""
        # Setup context
        self.memory.add_user_message("Play some music")
        self.memory.add_assistant_message("Playing your playlist", action="spotify_playback")
        self.memory.set_user_preference("personal", "name", "Emma")
        self.memory.set_context("current_app", "spotify")

        # Create system prompt for specific intent
        prompt = self.memory.create_system_prompt("spotify")

        # Check that prompt contains required context
        self.assertIn("spotify", prompt)
        self.assertIn("Emma", prompt)  # User name should be included
        self.assertIn("Playing your playlist", prompt)  # Recent conversation

        # Check that prompt is formatted correctly
        self.assertTrue(prompt.startswith("You are an AI assistant"))
        self.assertIn("Recent conversation:", prompt)
        self.assertIn("User preferences:", prompt)


# Additional tests with pytest

@pytest.fixture
def temp_memory_file():
    """Create a temporary file for memory tests."""
    fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def memory_manager(temp_memory_file):
    """Create a memory manager for tests."""
    return MemoryManager(file_path=temp_memory_file, max_conversations=10)

def test_timestamp_format(memory_manager):
    """Test that timestamps are properly formatted."""
    memory_manager.add_user_message("Test timestamp")
    timestamp = memory_manager._conversations[0]["timestamp"]

    # Try to parse the timestamp - should not raise an exception
    dt = datetime.fromisoformat(timestamp)

    # Should be recent
    now = datetime.now()
    difference = now - dt
    assert difference.total_seconds() < 10  # Within 10 seconds

def test_memory_expiration(temp_memory_file):
    """Test that old memories expire based on configuration."""
    # Create memory manager with short expiration time
    memory = MemoryManager(
        file_path=temp_memory_file,
        max_conversations=10,
        context_expiration_days=1
    )

    # Add a memory with an old timestamp
    old_date = (datetime.now() - timedelta(days=2)).isoformat()
    memory._conversations.append({
        "speaker": "user",
        "text": "Old message",
        "timestamp": old_date
    })

    # Add a recent memory
    memory.add_user_message("New message")

    # Get context - should only include recent memory
    context = memory.get_conversation_context()
    exchanges = context["recent_exchanges"]

    # Should only have the recent message
    assert len(exchanges) == 0 or "New message" in exchanges[0]["user"]
    assert "Old message" not in json.dumps(exchanges)

def test_invalid_memory_file(temp_memory_file):
    """Test handling of corrupted memory file."""
    # Write invalid JSON to the memory file
    with open(temp_memory_file, 'w') as f:
        f.write("{ this is not valid JSON }")

    # Should not crash on invalid JSON
    memory = MemoryManager(file_path=temp_memory_file)

    # Should have initialized with empty data
    assert len(memory._conversations) == 0
    assert len(memory._user_preferences) == 0

def test_memory_concurrency():
    """Test memory operations from multiple threads."""
    import threading

    # Use in-memory storage for this test
    memory = MemoryManager(persist_user_preferences=False)

    # Function for threads to execute
    def add_messages(thread_id, count):
        for i in range(count):
            memory.add_user_message(f"Message {thread_id}-{i}")

    # Create and start multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=add_messages, args=(i, 20))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check that all messages were added (up to max_conversations limit)
    assert len(memory._conversations) == memory._max_conversations

if __name__ == '__main__':
    unittest.main()
