"""
Browser control module with integrated system prompts.

This module provides functions for controlling the web browser,
including opening websites, performing searches, and navigation.
"""

import webbrowser
import time
import re
from urllib.parse import quote_plus
from typing import Tuple, Optional

# Import system prompts
from assistant.system_prompts import prompt_manager


class BrowserControl:
    """Class for browser control operations with integrated system prompts."""

    def __init__(self):
        """Initialize the browser control with system prompts."""
        self.system_prompt = prompt_manager.get_prompt("browser.general")
        self.llm = None  # This would be initialized with an actual LLM interface

    def get_contextual_prompt(self, task_type=None):
        """
        Get a context-specific system prompt for browser tasks.

        Args:
            task_type: Specific browser task type (e.g., 'search', 'extract', 'navigate')

        Returns:
            Appropriate system prompt for the task
        """
        if task_type and f"browser.{task_type}" in prompt_manager.list_contexts():
            return prompt_manager.get_prompt(f"browser.{task_type}")

        # Fall back to general browser prompt
        return self.system_prompt

    def get_ai_response_for_browser_task(self, user_query, task_type=None, **kwargs):
        """
        Get AI response with the appropriate system prompt for a browser task.

        Args:
            user_query: User's request
            task_type: Type of browser task
            kwargs: Additional parameters for the LLM

        Returns:
            AI response using the appropriate system prompt
        """
        system_prompt = self.get_contextual_prompt(task_type)

        # Call LLM with the system prompt (implementation depends on your LLM interface)
        if self.llm:
            response = self.llm.get_response(
                system_prompt=system_prompt,
                user_query=user_query,
                **kwargs
            )
            return response
        else:
            return f"Would respond to '{user_query}' with prompt: {system_prompt[:30]}..."


def browser_action(command: str, system_prompt: Optional[str] = None) -> Tuple[str, str]:
    """
    Enhanced browser control function that can handle complex commands
    for any website and search query.

    Args:
        command: The user's voice command
        system_prompt: Optional system prompt to use for response generation

    Returns:
        Tuple of (response message, action type)
    """
    command = command.lower()
    action_type = "browser_unknown"

    try:
        # Handle opening specific browsers
        browser_match = re.search(r"open (brave|chrome|firefox|safari|edge|opera) browser", command)
        browser_type = browser_match.group(1) if browser_match else None

        # Extract website names with improved pattern to match test cases
        # Look for domains in various formats including with or without protocol
        website_pattern = r'(?:open|go to|visit|navigate to)\s+(?:the\s+)?([a-z0-9]+(?:\.[a-z0-9]+)+(?:/[^\s]*)?|(?:https?://)?[a-z0-9]+(?:\.[a-z0-9]+)+(?:/[^\s]*)?)(?:\s+|$|\.)'
        website_match = re.search(website_pattern, command)
        website = website_match.group(1) if website_match else None

        # Direct "open domain.com" pattern for test cases
        if not website and command.startswith("open "):
            simple_domain = command[5:].strip()  # Strip "open " prefix
            if re.match(r'^(?:https?://)?[a-z0-9]+(?:\.[a-z0-9]+)+(?:/[^\s]*)?$', simple_domain):
                website = simple_domain

        # Extract search terms
        search_terms = []
        if "search" in command:
            # Extract all search phrases following "search" or "search for"
            search_parts = re.findall(r'search(?:\s+for)?\s+([^.]+?)(?:\s+in\s+it|$|\s+and\s+|\s+then\s+)', command)
            search_terms = [term.strip() for term in search_parts if term.strip()]

        # Handle navigation commands
        if "back" in command and ("go" in command or "navigate" in command):
            # This would require browser automation beyond what webbrowser module offers
            # In a real implementation, this would use something like Selenium
            response = "Navigating back to the previous page."
            action_type = "browser_navigate"
            return response, action_type

        # Process command based on content
        if browser_type:
            # Map of browser names to their homepage URLs
            browser_urls = {
                "brave": "https://brave.com",
                "chrome": "https://www.google.com",
                "firefox": "https://www.mozilla.org/firefox",
                "safari": "https://www.apple.com/safari",
                "edge": "https://www.microsoft.com/edge",
                "opera": "https://www.opera.com"
            }

            # Open specified browser
            browser_url = browser_urls.get(browser_type, "https://www.google.com")
            webbrowser.open(browser_url)
            response = f"Opening {browser_type.capitalize()} browser."
            action_type = "browser_open"

            # If we have a website specified in the command, open it after browser launch
            if website:
                time.sleep(1.2)  # Give browser time to open
                if not website.startswith(('http://', 'https://')):
                    website_url = f"https://{website}"
                else:
                    website_url = website

                webbrowser.open(website_url)
                response += f" Navigating to {website}."

                # If search terms are also specified for the website
                if search_terms:
                    time.sleep(1)  # Give page time to load
                    search_query = search_terms[0]  # Use the first search term

                    # Try to construct a reasonable search URL for common sites
                    if "google" in website:
                        search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
                    elif "youtube" in website:
                        search_url = f"https://www.youtube.com/results?search_query={quote_plus(search_query)}"
                    elif "amazon" in website:
                        search_url = f"https://www.amazon.com/s?k={quote_plus(search_query)}"
                    elif "bing" in website:
                        search_url = f"https://www.bing.com/search?q={quote_plus(search_query)}"
                    elif "yahoo" in website:
                        search_url = f"https://search.yahoo.com/search?p={quote_plus(search_query)}"
                    else:
                        # Generic approach for other sites
                        search_url = f"https://www.google.com/search?q={quote_plus(search_query)}+site:{website}"

                    webbrowser.open(search_url)
                    response += f" Searching for '{search_query}'."
                    action_type = "browser_search"

            return response, action_type

        # Handle direct website opening without specifying browser
        elif website:
            if not website.startswith(('http://', 'https://')):
                website_url = f"https://{website}"
            else:
                website_url = website

            webbrowser.open(website_url)
            response = f"Opening {website}."
            action_type = "browser_open"
            return response, action_type

        # Handle direct searches without specifying a website
        elif "search" in command and search_terms:
            search_query = search_terms[0]  # Use the first search term
            url = f"https://www.google.com/search?q={quote_plus(search_query)}"
            webbrowser.open(url)
            response = f"Searching for '{search_query}' on Google."
            action_type = "browser_search"
            return response, action_type

        # Influence the response based on system prompt if provided
        response_prefix = ""
        if system_prompt:
            if "detailed" in system_prompt.lower():
                response_prefix = "I'm providing detailed information about this action: "
            elif "basic" in system_prompt.lower():
                response_prefix = "Basic info: "

        # Fallback for unrecognized commands
        response = f"{response_prefix}I couldn't understand that browser command. Try saying 'open brave browser', 'go to youtube.com', or 'search for cute cats'."
        action_type = "browser_unknown"
        return response, action_type

    except Exception as e:
        # Handle any errors that might occur
        error_message = f"Sorry, I encountered an error while trying to control the browser: {str(e)}"
        return error_message, "browser_error"


# Create an instance for easy importing
browser_controller = BrowserControl()

# For backward compatibility
perform_browser_action = browser_action


if __name__ == "__main__":
    # Simple test
    test_command = "open github.com"
    response, action = browser_action(test_command)
    print(f"Command: {test_command}")
    print(f"Response: {response}")
    print(f"Action: {action}")
