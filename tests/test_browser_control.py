#!/usr/bin/env python3
"""
Unit tests for the Browser Control module.
Tests browser actions, navigation, and search functionality.
"""

import os
import sys
import unittest
import pytest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the modules to test
from assistant.browser_control import browser_action


class TestBrowserControl(unittest.TestCase):
    """Test cases for browser control functionality."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Mock any external dependencies if needed
        pass

    @patch('webbrowser.open')
    def test_open_website(self, mock_open):
        """Test opening a website."""
        # Test command to open a website
        command = "open github.com"
        system_prompt = "You are a browser assistant."

        # Execute the command
        response, action = browser_action(command, system_prompt)

        # Check that webbrowser.open was called with correct URL
        mock_open.assert_called_once()
        url_arg = mock_open.call_args[0][0]
        self.assertTrue("github.com" in url_arg)

        # Verify the response mentions the website
        self.assertTrue("github.com" in response.lower())
        self.assertEqual(action, "browser_open")

    @patch('webbrowser.open')
    def test_search_query(self, mock_open):
        """Test searching for information."""
        # Test command to search
        command = "search for python tutorials"
        system_prompt = "You are a browser assistant."

        # Execute the command
        response, action = browser_action(command, system_prompt)

        # Check that webbrowser.open was called for a search
        mock_open.assert_called_once()
        search_arg = mock_open.call_args[0][0]
        self.assertTrue("python" in search_arg.lower().replace('+', ' '))
        self.assertTrue("tutorials" in search_arg.lower().replace('+', ' '))

        # Verify the response mentions the search
        self.assertTrue("searching" in response.lower() or "search" in response.lower())
        self.assertTrue("python tutorials" in response.lower())
        self.assertEqual(action, "browser_search")

    @patch('webbrowser.open')
    def test_navigate_back(self, mock_open):
        """Test navigation commands."""
        # Test navigation command
        command = "go back to previous page"
        system_prompt = "You are a browser assistant."

        # Execute the command
        response, action = browser_action(command, system_prompt)

        # Verify the response for navigation
        self.assertTrue("previous page" in response.lower() or "back" in response.lower())
        self.assertEqual(action, "browser_navigate")

    def test_invalid_command(self):
        """Test handling of invalid browser commands."""
        # Test invalid command
        command = "do something completely random with browser"
        system_prompt = "You are a browser assistant."

        # Execute the command
        response, action = browser_action(command, system_prompt)

        # Should indicate the command wasn't understood
        self.assertTrue(
            "not recognized" in response.lower() or
            "don't understand" in response.lower() or
            "invalid" in response.lower() or
            "unclear" in response.lower() or
            "couldn't understand" in response.lower()
        )
        self.assertEqual(action, "browser_unknown")

    @patch('webbrowser.open')
    def test_system_prompt_influence(self, mock_open):
        """Test that the system prompt influences the response."""
        # Create two different system prompts
        basic_prompt = "You are a basic browser assistant."
        detailed_prompt = "You are a detailed browser assistant. Provide comprehensive information about what you're doing."

        # Same command with different prompts
        command = "open wikipedia"

        # Execute with basic prompt
        basic_response, _ = browser_action(command, basic_prompt)

        # Execute with detailed prompt
        detailed_response, _ = browser_action(command, detailed_prompt)

        # At least one of the responses should be different from the other
        # This is a more flexible test that doesn't rely on specific text
        self.assertTrue(
            basic_response != detailed_response or
            "basic" in basic_response.lower() or
            "detailed" in detailed_response.lower()
        )


# Additional tests with pytest

@pytest.fixture
def mock_webbrowser():
    """Create a mock for the webbrowser module."""
    with patch('webbrowser.open') as mock_open:
        yield mock_open


@pytest.mark.parametrize("domain", [
    "github.com",
    "www.python.org",
    "https://example.com",
    "http://test.io"
])
def test_open_with_domain_types(mock_webbrowser, domain):
    """Test opening different domain types."""
    system_prompt = "You are a browser assistant."

    # Reset the mock for each test case
    mock_webbrowser.reset_mock()

    command = f"open {domain}"
    response, action = browser_action(command, system_prompt)

    # Check that webbrowser.open was called
    assert mock_webbrowser.call_count > 0

    # Should have been called with the domain
    call_arg = mock_webbrowser.call_args[0][0]
    assert domain in call_arg
    assert action == "browser_open"


@pytest.mark.parametrize("search_query", [
    "python tutorials",
    "best AI assistants 2025",
    "how to make pasta carbonara"
])
def test_search_queries(mock_webbrowser, search_query):
    """Test various search queries."""
    # Reset the mock for each test case
    mock_webbrowser.reset_mock()

    command = f"search for {search_query}"
    system_prompt = "You are a browser assistant."

    response, action = browser_action(command, system_prompt)

    # Response should contain the search query
    assert search_query.lower() in response.lower()
    assert action == "browser_search"


def test_browser_error_handling():
    """Test handling of browser errors."""
    # Use a patch that raises an exception when called
    with patch('webbrowser.open', side_effect=Exception("Test browser error")):
        command = "open github.com"
        system_prompt = "You are a browser assistant."

        # Should handle the error gracefully
        response, action = browser_action(command, system_prompt)

        assert "error" in response.lower() or "sorry" in response.lower()
        assert action == "browser_error"


if __name__ == '__main__':
    unittest.main()
