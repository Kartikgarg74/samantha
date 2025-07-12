"""
Browser command handlers for Samantha Voice Assistant.

This module processes voice commands related to web browsers and search functionality,
interfacing with the browser_control module to execute the actual browser actions.
"""

import re
from assistant.browser_control import browser_action

def handle_browser_command(command_text):
    """
    Process browser-related voice commands.

    Args:
        command_text (str): The transcribed user command

    Returns:
        str: Response message to be spoken to the user
    """
    # Clean and normalize the command text
    command_text = command_text.lower().strip()

    # Check if this is actually a browser command
    browser_indicators = [
        "open browser", "search for", "look up", "google", "brave", "firefox",
        "chrome", "safari", "edge", "internet explorer", "web browser",
        "find online", "search on", "go to website", "visit", "navigate to",
        "open tab", "new tab", "browse"
    ]

    is_browser_command = any(indicator in command_text for indicator in browser_indicators)

    if not is_browser_command:
        return None  # Not a browser command, let other handlers process it

    # Direct the command to the browser_control module
    return browser_action(command_text)

def detect_browser_command(text):
    """
    Detect if text contains a browser-related command

    Args:
        text (str): The text to analyze

    Returns:
        bool: True if this is likely a browser command, False otherwise
    """
    browser_keywords = [
        "browser", "search", "google", "brave", "firefox", "chrome",
        "safari", "edge", "internet", "web", "online", "website",
        "visit", "navigate", "open", "tab", "browse"
    ]

    # Also check for common website TLDs
    website_pattern = r'[a-z0-9]+\.(com|org|net|edu|gov|io|co|me)'

    return any(keyword in text.lower() for keyword in browser_keywords) or re.search(website_pattern, text.lower()) is not None
