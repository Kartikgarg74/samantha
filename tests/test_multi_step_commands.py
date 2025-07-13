#!/usr/bin/env python3
"""
Unit tests for Multi-step Command Processing.
Tests command sequence handling, confirmations, and error recovery.
"""

import os
import sys
import unittest
import pytest
import json
import tempfile
from unittest.mock import patch, MagicMock, call

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from assistant.command_processor import (
    CommandProcessor, Command, CommandSequence,
    CommandState, extract_steps_from_text, is_confirmation
)

class TestMultiStepCommands(unittest.TestCase):
    """Test cases for multi-step command processing."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Create handlers for different intents
        self.handlers = {
            "browser": lambda text, params: (f"Browsing: {text}", {"url": "example.com"}),
            "spotify": lambda text, params: (f"Playing: {text}", {"status": "playing"}),
            "general": lambda text, params: (f"General: {text}", None),
        }

        # Create command processor
        self.processor = CommandProcessor(self.handlers)

        # Register handlers
        for intent, handler in self.handlers.items():
            self.processor.register_handler(intent, handler)

    def test_create_command_sequence(self):
        """Test creating a command sequence."""
        # Create a sequence
        commands = ["play some jazz", "open github"]
        sequence = self.processor.create_sequence("Test Sequence", commands)

        # Check sequence properties
        self.assertEqual(sequence.name, "Test Sequence")
        self.assertEqual(len(sequence.commands), 2)
        self.assertEqual(sequence.commands[0].text, "play some jazz")
        self.assertEqual(sequence.commands[1].text, "open github")
        self.assertEqual(sequence.state, CommandState.PENDING)

    def test_command_execution(self):
        """Test executing commands in a sequence."""
        # Create and queue a sequence
        commands = ["play some jazz", "open github"]
        sequence = self.processor.create_sequence("Test Sequence", commands)
        self.processor.queue_sequence(sequence)

        # Process first command
        response1, result1 = self.processor.process_current_command()

        # Check first command results
        self.assertEqual(response1, "Playing: play some jazz")
        self.assertEqual(result1, {"status": "playing"})

        # Advance to next command
        success, next_cmd, message = self.processor.advance_sequence()
        self.assertTrue(success)
        self.assertEqual(next_cmd.text, "open github")

        # Process second command
        response2, result2 = self.processor.process_current_command()

        # Check second command results
        self.assertEqual(response2, "Browsing: open github")
        self.assertEqual(result2, {"url": "example.com"})

        # Advance again - should complete the sequence
        success, next_cmd, message = self.processor.advance_sequence()
        self.assertTrue(success)
        self.assertIsNone(next_cmd)
        self.assertTrue("completed" in message.lower())

    def test_confirmation_handling(self):
        """Test handling of user confirmations."""
        # Create a sequence requiring confirmation
        commands = ["play some jazz", "open github"]
        sequence = self.processor.create_sequence("Test Sequence", commands, require_confirmation=True)
        self.processor.queue_sequence(sequence)

        # Process first command
        self.processor.process_current_command()

        # Request confirmation
        success, message, next_info = self.processor.request_confirmation()
        self.assertTrue(success)
        self.assertTrue("open github" in message)
        self.assertTrue(self.processor.is_awaiting_confirmation())

        # Test confirmation handling - positive case
        success, message = self.processor.handle_confirmation(True)
        self.assertTrue(success)
        self.assertFalse(self.processor.is_awaiting_confirmation())

        # Sequence should have advanced
        current = self.processor.active_sequence.get_current_command()
        self.assertEqual(current.text, "open github")

    def test_confirmation_rejection(self):
        """Test handling of confirmation rejection."""
        # Create a sequence requiring confirmation
        commands = ["play some jazz", "open github"]
        sequence = self.processor.create_sequence("Test Sequence", commands, require_confirmation=True)
        self.processor.queue_sequence(sequence)

        # Process first command
        self.processor.process_current_command()

        # Request confirmation
        self.processor.request_confirmation()

        # Test confirmation handling - negative case
        success, message = self.processor.handle_confirmation(False)
        self.assertTrue(success)
        self.assertFalse(self.processor.is_awaiting_confirmation())

        # Sequence should be cancelled
        self.assertIsNone(self.processor.active_sequence)
        self.assertTrue("cancelled" in message.lower())

    def test_command_failure(self):
        """Test handling of command execution failures."""
        # Create a failing handler
        def failing_handler(text, params):
            raise ValueError("Test failure")

        # Register failing handler
        self.processor.register_handler("failing", failing_handler)

        # Create sequence with failing command
        sequence = CommandSequence("Failing Sequence")
        command = Command("do something that fails", intent="failing")
        sequence.add_command(command)

        # Queue the sequence
        self.processor.queue_sequence(sequence)

        # Process the command - should handle the failure
        response, result = self.processor.process_current_command()

        # Check response and state
        self.assertTrue("error" in response.lower())
        self.assertEqual(sequence.state, CommandState.FAILED)

    def test_command_queue(self):
        """Test queuing multiple command sequences."""
        # Create two sequences
        sequence1 = self.processor.create_sequence("First Sequence", ["command one"])
        sequence2 = self.processor.create_sequence("Second Sequence", ["command two"])

        # Queue both
        self.processor.queue_sequence(sequence1)
        self.processor.queue_sequence(sequence2)

        # Check active sequence
        self.assertEqual(self.processor.active_sequence.name, "First Sequence")

        # Process and complete first sequence
        self.processor.process_current_command()
        self.processor.advance_sequence()

        # Second sequence should now be active
        self.assertEqual(self.processor.active_sequence.name, "Second Sequence")

    def test_cancel_all(self):
        """Test cancelling all command sequences."""
        # Queue multiple sequences
        self.processor.queue_sequence(self.processor.create_sequence("Seq 1", ["command 1"]))
        self.processor.queue_sequence(self.processor.create_sequence("Seq 2", ["command 2"]))

        # Cancel all
        message = self.processor.cancel_all()

        # Check results
        self.assertIsNone(self.processor.active_sequence)
        self.assertEqual(len(self.processor.sequence_queue), 0)
        self.assertTrue("cancelled" in message.lower())

    def test_extract_steps_from_text(self):
        """Test extracting steps from different text formats."""
        # Test numbered list format
        text1 = "1. Play some jazz 2. Open GitHub 3. Send a message"
        steps1 = extract_steps_from_text(text1)
        self.assertEqual(len(steps1), 3)
        self.assertEqual(steps1[0], "Play some jazz")

        # Test conjunction format
        text2 = "Play some jazz and then open GitHub"
        steps2 = extract_steps_from_text(text2)
        self.assertEqual(len(steps2), 2)
        self.assertTrue("play some jazz" in steps2[0].lower())
        self.assertTrue("open github" in steps2[1].lower())

        # Test single command (no multi-step)
        text3 = "Play some jazz"
        steps3 = extract_steps_from_text(text3)
        self.assertEqual(len(steps3), 1)
        self.assertEqual(steps3[0], "Play some jazz")

    def test_is_confirmation(self):
        """Test detection of confirmation and rejection responses."""
        # Positive confirmations
        self.assertEqual(is_confirmation("yes"), (True, True))
        self.assertEqual(is_confirmation("sure, go ahead"), (True, True))
        self.assertEqual(is_confirmation("ok do it"), (True, True))

        # Negative confirmations (rejections)
        self.assertEqual(is_confirmation("no"), (True, False))
        self.assertEqual(is_confirmation("stop, don't do that"), (True, False))
        self.assertEqual(is_confirmation("wait, cancel"), (True, False))

        # Non-confirmation responses
        self.assertEqual(is_confirmation("what time is it"), (False, False))
        self.assertEqual(is_confirmation("tell me about the weather"), (False, False))


# Additional tests with pytest

@pytest.fixture
def command_processor():
    """Create a command processor for testing."""
    processor = CommandProcessor()

    # Register some mock handlers
    processor.register_handler("browser", lambda text, params: (f"Browser: {text}", {"success": True}))
    processor.register_handler("spotify", lambda text, params: (f"Spotify: {text}", {"success": True}))

    return processor

@pytest.fixture
def test_sequence(command_processor):
    """Create a test sequence with multiple commands."""
    sequence = command_processor.create_sequence(
        "Test Sequence",
        ["play rock music", "open twitter", "check weather"],
        require_confirmation=True
    )
    return sequence

def test_sequence_summary(test_sequence):
    """Test generation of sequence summary."""
    # Initially all pending
    summary = test_sequence.summary()
    assert summary["total_steps"] == 3
    assert summary["completed_steps"] == 0
    assert summary["current_step"] == 0
    assert summary["state"] == "pending"

    # Start the sequence
    test_sequence.advance()
    test_sequence.mark_current_complete({"result": "success"})

    # Check updated summary
    summary = test_sequence.summary()
    assert summary["completed_steps"] == 1
    assert summary["current_step"] == 1

def test_command_parameters():
    """Test command with parameters."""
    command = Command("play jazz", intent="spotify", parameters={"volume": 80})

    assert command.text == "play jazz"
    assert command.intent == "spotify"
    assert command.parameters["volume"] == 80

@pytest.mark.parametrize("text,expected_count", [
    ("First do this, then do that, finally do something else", 3),
    ("1. Step one 2. Step two", 2),
    ("Do this and then do that", 2),
    ("Single command only", 1),
])
def test_step_extraction_variations(text, expected_count):
    """Test extraction of steps from various text formats."""
    steps = extract_steps_from_text(text)
    assert len(steps) == expected_count

def test_sequence_state_transitions(command_processor, test_sequence):
    """Test state transitions through a sequence lifecycle."""
    # Initial state
    assert test_sequence.state == CommandState.PENDING

    # Queue the sequence
    command_processor.queue_sequence(test_sequence)

    # First command in progress
    assert test_sequence.state == CommandState.IN_PROGRESS

    # Complete all commands
    while test_sequence.state != CommandState.COMPLETED:
        if command_processor.is_awaiting_confirmation():
            command_processor.handle_confirmation(True)

        if test_sequence.get_current_command():
            command_processor.process_current_command()
            command_processor.advance_sequence()

    # Final state
    assert test_sequence.state == CommandState.COMPLETED
    assert test_sequence.completed_at is not None

def test_error_recovery(command_processor):
    """Test recovery from errors in command processing."""
    # Create a sequence with a command that will fail
    error_sequence = CommandSequence("Error Test")
    good_command = Command("play music", intent="spotify")
    error_command = Command("cause error", intent="nonexistent")  # No handler for this intent
    recovery_command = Command("open browser", intent="browser")

    error_sequence.add_command(good_command)
    error_sequence.add_command(error_command)
    error_sequence.add_command(recovery_command)

    # Queue the sequence
    command_processor.queue_sequence(error_sequence)

    # Process first command - should succeed
    response1, _ = command_processor.process_current_command()
    assert "Spotify" in response1
    command_processor.advance_sequence()

    # Process second command - should fail
    response2, _ = command_processor.process_current_command()
    assert "error" in response2.lower()

    # Sequence should be marked as failed
    assert error_sequence.state == CommandState.FAILED

if __name__ == '__main__':
    unittest.main()
