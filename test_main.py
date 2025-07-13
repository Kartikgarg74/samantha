#!/usr/bin/env python3
"""Simple test module for Samantha Voice Assistant."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import logging

# Configure basic logging to help with debugging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestSamantha")

# Make sure we can import from assistant
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestSamantha(unittest.TestCase):
    """Basic tests for Samantha assistant."""

    def test_memory_manager_methods(self):
        """Test if memory_manager has the required methods."""
        from assistant.memory_manager import memory_manager

        # Check if memory_manager has add_conversation_entry method
        self.assertTrue(hasattr(memory_manager, 'add_conversation_entry'),
                       "Memory manager should have add_conversation_entry method")

        # Check if it has add_assistant_message method (it should NOT)
        has_assistant_message = hasattr(memory_manager, 'add_assistant_message')
        logger.info(f"Has add_assistant_message: {has_assistant_message}")

        # This is the issue - main.py is calling a method that doesn't exist
        # In production it should NOT have this method
        if has_assistant_message:
            logger.warning("Memory manager has add_assistant_message - this is unexpected")

    def test_command_processor(self):
        """Test if CommandProcessor has expected methods."""
        from assistant.command_processor import CommandProcessor

        processor = CommandProcessor()

        # Check if it has cancel_all method (it should NOT)
        has_cancel_all = hasattr(processor, 'cancel_all')
        logger.info(f"Has cancel_all: {has_cancel_all}")

        # This is the issue - main.py is calling a method that doesn't exist
        self.assertFalse(has_cancel_all, "CommandProcessor should NOT have cancel_all method")

    def test_speech_recognition_service(self):
        """Test speech recognition service structure."""
        from assistant.speech_recognition_service import speech_recognition_service

        # Check basic structure
        self.assertTrue(hasattr(speech_recognition_service, '_listen'),
                       "Speech service should have _listen method")
        self.assertTrue(hasattr(speech_recognition_service, 'recognize_speech'),
                       "Speech service should have recognize_speech method")

        # Check if recognize_speech accepts timeout parameter (check signature)
        import inspect
        params = inspect.signature(speech_recognition_service.recognize_speech).parameters
        logger.info(f"recognize_speech params: {list(params.keys())}")

        # The problem is passing timeout to recognize_speech but then not using it

def fix_main_file():
    """
    Function to directly modify main.py with the necessary fixes.
    This isn't a test but a utility function.
    """
    try:
        with open('main.py', 'r') as file:
            content = file.read()

        # Fix 1: Replace add_assistant_message with add_conversation_entry in _speak
        content = content.replace(
            'self.memory.add_assistant_message(text)',
            'self.memory.add_conversation_entry("assistant", text)'
        )

        # Fix 2: Replace add_assistant_message with add_conversation_entry in process_command
        content = content.replace(
            'self.memory.add_assistant_message(response, action)',
            'self.memory.add_conversation_entry("assistant", response)'
        )

        # Fix 3: Remove cancel_all call in cleanup
        content = content.replace(
            '            # Cancel any pending commands\n            if hasattr(self, \'command_processor\'):\n                print("❌ Cancelling pending commands...")\n                self.command_processor.cancel_all()\n',
            '            # Cancel any pending commands call removed - method doesn\'t exist\n'
        )

        # Fix 4: Remove timeout parameter in _listen method
        content = content.replace(
            'result = self.recognizer.recognize_speech(audio_data, timeout=timeout)',
            'result = self.recognizer.recognize_speech(audio_data)'
        )

        # Fix 5: Update _create_fallback_memory to match expected interface
        content = content.replace(
            '            def add_assistant_message(self, text, action=None):\n                self.assistant_messages.append(text)\n                if len(self.assistant_messages) > 10:\n                    self.assistant_messages.pop(0)',
            '            def add_assistant_message(self, text, action=None):\n                self.assistant_messages.append(text)\n                if len(self.assistant_messages) > 10:\n                    self.assistant_messages.pop(0)\n\n            def add_conversation_entry(self, speaker, text, timestamp=None):\n                if speaker == "user":\n                    self.add_user_message(text)\n                elif speaker == "assistant":\n                    self.add_assistant_message(text)'
        )

        # Write the fixed content back
        with open('main.py.fixed', 'w') as file:
            file.write(content)

        return True, "Fixed version saved as main.py.fixed"

    except Exception as e:
        return False, f"Error fixing main.py: {str(e)}"

if __name__ == "__main__":
    # First run tests
    print("Running tests...")
    unittest.main(exit=False)

    # Then fix the main file
    print("\n\nAttempting to fix main.py...")
    success, message = fix_main_file()
    print(message)

    if success:
        print("\nInstructions:")
        print("1. Review main.py.fixed to verify changes")
        print("2. If satisfied, rename it: mv main.py.fixed main.py")
        print("3. Run Samantha: python main.py")
    else:
        print("\nManual fixes required. Edit main.py to:")
        print("1. Replace self.memory.add_assistant_message(text) with self.memory.add_conversation_entry(\"assistant\", text)")
        print("2. Remove command_processor.cancel_all() call in cleanup method")
        print("3. Remove timeout parameter when calling recognize_speech")
