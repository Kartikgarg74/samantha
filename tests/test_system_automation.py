#!/usr/bin/env python3
"""
Unit tests for the System Automation module.
Tests system actions, app management, and system settings.
"""

import os
import sys
import unittest
import pytest
from unittest.mock import patch, MagicMock, call

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from assistant.system_automation import system_action

class TestSystemAutomation(unittest.TestCase):
    """Test cases for system automation functionality."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Mock any external dependencies if needed
        pass

    @patch('subprocess.Popen')
    def test_open_application(self, mock_popen):
        """Test opening an application."""
        # Test opening an app
        command = "open spotify"
        system_prompt = "You are a system automation assistant."

        # Execute the command
        response, action = system_action(command, system_prompt)

        # Check that subprocess.Popen was called
        mock_popen.assert_called_once()

        # Verify the response
        self.assertTrue("opening" in response.lower() and "spotify" in response.lower())
        self.assertEqual(action, "system_open_app")

    @patch('subprocess.run')
    def test_close_application(self, mock_run):
        """Test closing an application."""
        # Test closing an app
        command = "close spotify"
        system_prompt = "You are a system automation assistant."

        # Configure the mock to return success
        mock_run.return_value = MagicMock(returncode=0)

        # Execute the command
        response, action = system_action(command, system_prompt)

        # Check that subprocess.run was called
        mock_run.assert_called_once()

        # Verify the response
        self.assertTrue("closing" in response.lower() and "spotify" in response.lower())
        self.assertEqual(action, "system_close_app")

    @patch('subprocess.run')
    def test_system_volume_control(self, mock_run):
        """Test controlling system volume."""
        # Test volume control
        command = "set volume to 50 percent"
        system_prompt = "You are a system automation assistant."

        # Configure the mock to return success
        mock_run.return_value = MagicMock(returncode=0)

        # Execute the command
        response, action = system_action(command, system_prompt)

        # Verify the response
        self.assertTrue("volume" in response.lower())
        self.assertEqual(action, "system_volume")

    @patch('subprocess.run')
    def test_system_brightness_control(self, mock_run):
        """Test controlling screen brightness."""
        # Test brightness control
        command = "set brightness to 80 percent"
        system_prompt = "You are a system automation assistant."

        # Configure the mock to return success
        mock_run.return_value = MagicMock(returncode=0)

        # Execute the command
        response, action = system_action(command, system_prompt)

        # Verify the response
        self.assertTrue("brightness" in response.lower())
        self.assertEqual(action, "system_brightness")

    def test_invalid_system_command(self):
        """Test handling of invalid system commands."""
        # Test with invalid command
        command = "do something completely random with system"
        system_prompt = "You are a system automation assistant."

        # Execute the command
        response, action = system_action(command, system_prompt)

        # Should indicate the command wasn't understood
        self.assertTrue(
            "not recognized" in response.lower() or
            "don't understand" in response.lower() or
            "invalid" in response.lower() or
            "unclear" in response.lower()
        )
        self.assertEqual(action, "system_unknown")

    @patch('subprocess.run')
    def test_system_info(self, mock_run):
        """Test retrieving system information."""
        # Mock the subprocess output for system info
        mock_process = MagicMock()
        mock_process.stdout = "Memory: 16GB\nCPU: Intel i7\nDisk Space: 500GB"
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        # Test system info command
        command = "show system information"
        system_prompt = "You are a system automation assistant."

        # Execute the command
        response, action = system_action(command, system_prompt)

        # Verify the response contains system info
        self.assertTrue("system information" in response.lower())
        self.assertEqual(action, "system_info")


# Additional tests with pytest

@pytest.fixture
def mock_subprocess_popen():
    """Create a mock for subprocess.Popen."""
    with patch('subprocess.Popen') as mock_popen:
        yield mock_popen

@pytest.fixture
def mock_subprocess_run():
    """Create a mock for subprocess.run."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        yield mock_run

@pytest.mark.parametrize("app_name", [
    "spotify",
    "chrome",
    "firefox",
    "word"
])
def test_open_different_apps(mock_subprocess_popen, app_name):
    """Test opening various applications."""
    command = f"open {app_name}"
    system_prompt = "You are a system automation assistant."

    response, action = system_action(command, system_prompt)

    # Should contain the app name in the response
    assert app_name.lower() in response.lower()
    assert action == "system_open_app"
    assert mock_subprocess_popen.called

def test_system_sleep(mock_subprocess_run):
    """Test putting the system to sleep."""
    command = "put computer to sleep"
    system_prompt = "You are a system automation assistant."

    response, action = system_action(command, system_prompt)

    assert "sleep" in response.lower()
    assert action == "system_sleep"
    assert mock_subprocess_run.called

def test_system_restart(mock_subprocess_run):
    """Test restarting the system."""
    command = "restart computer"
    system_prompt = "You are a system automation assistant."

    response, action = system_action(command, system_prompt)

    assert "restart" in response.lower()
    assert action == "system_restart"
    assert mock_subprocess_run.called

def test_system_action_error_handling(mock_subprocess_run):
    """Test handling of system command errors."""
    # Configure the mock to return an error
    mock_subprocess_run.return_value = MagicMock(returncode=1)

    command = "open settings"
    system_prompt = "You are a system automation assistant."

    # Should handle the error gracefully
    response, action = system_action(command, system_prompt)

    assert "error" in response.lower() or "failed" in response.lower()
    assert action == "system_error"

if __name__ == '__main__':
    unittest.main()
