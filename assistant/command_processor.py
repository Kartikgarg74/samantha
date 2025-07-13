"""
Command Processor Module

This module processes user commands, extracts multi-step instructions,
and handles command execution.
"""

import re
import logging
from typing import List, Dict, Any, Tuple, Optional, Callable, Union
import datetime

from assistant.config_manager import config_manager
from assistant.intent_classifier import intent_classifier

logger = logging.getLogger(__name__)


class CommandProcessor:
    """
    Processes user commands and extracts multi-step instructions.
    """

    def __init__(self):
        """Initialize the command processor."""
        self.config = config_manager.get_section("command_processor")

        # Command categories and their keywords
        self.command_categories = {
            "Browsing": ["open", "browse", "search", "visit", "website", "google", "bing",
                         "chrome", "firefox", "internet", "github", "youtube", "facebook",
                         "twitter", "instagram", "linkedin", "reddit"],

            "Media": ["play", "pause", "stop", "next", "previous", "volume", "music",
                     "video", "audio", "spotify", "netflix", "youtube", "movie", "song"],

            "System": ["shutdown", "restart", "sleep", "hibernate", "lock", "settings",
                      "preferences", "control panel", "task manager", "performance"],

            "Files": ["open", "save", "delete", "rename", "copy", "move", "document",
                     "file", "folder", "directory", "create", "text file"],

            "Weather": ["weather", "temperature", "forecast", "humidity", "rain",
                       "snow", "sunny", "cloudy", "windy"],

            "Calendar": ["meeting", "appointment", "schedule", "event", "reminder",
                        "calendar", "date", "time", "day", "month", "year"],

            "Communication": ["email", "message", "call", "contact", "send", "gmail",
                            "outlook", "whatsapp", "telegram", "slack", "discord"],

            "Timer": ["timer", "alarm", "countdown", "stopwatch", "minutes", "seconds",
                     "hours", "set timer", "remind me"]
        }

        # Initialize command handlers
        self.command_handlers = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default command handlers."""
        # This would be expanded with actual handlers in a full implementation
        self.command_handlers = {
            "Browsing": self._handle_browsing_command,
            "Media": self._handle_media_command,
            "System": self._handle_system_command,
            "Files": self._handle_files_command,
            "Weather": self._handle_weather_command,
            "Calendar": self._handle_calendar_command,
            "Communication": self._handle_communication_command,
            "Timer": self._handle_timer_command,
            "General": self._handle_general_command
        }

    def process_command(self, command_text: str) -> Tuple[str, str]:
        """
        Process a command and determine the appropriate action.

        Args:
            command_text: User's command text

        Returns:
            Tuple of (category, response)
        """
        # Classify the command category
        category = self.classify_command(command_text)

        # Get handler for this category
        handler = self.command_handlers.get(category, self._handle_general_command)

        # Execute handler
        response = handler(command_text)

        return category, response

    def classify_command(self, command_text: str) -> str:
        """
        Classify a command into a category.

        Args:
            command_text: User's command text

        Returns:
            Command category
        """
        command_text = command_text.lower()

        # Check each category for keywords
        for category, keywords in self.command_categories.items():
            for keyword in keywords:
                # Look for whole words that match the keyword
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, command_text):
                    return category

        # Special handling for browser/github commands
        if "open github" in command_text or "go to github" in command_text:
            return "Browsing"

        # Use intent classifier as fallback
        intent, _ = intent_classifier.classify(command_text)

        # Map intent to category (simplified mapping)
        intent_to_category = {
            "browse": "Browsing",
            "play_media": "Media",
            "system_control": "System",
            "file_operation": "Files",
            "weather_query": "Weather",
            "calendar_query": "Calendar",
            "communication": "Communication",
            "timer": "Timer"
        }

        return intent_to_category.get(intent, "General")

    def extract_steps_from_text(self, text: str) -> List[str]:
        """
        Extract multiple steps or commands from a text.

        Args:
            text: Text containing multiple steps

        Returns:
            List of individual command steps
        """
        # Check for numbered list format (e.g., "1. Do this\n2. Do that")
        numbered_pattern = r'\d+\.\s*(.*?)(?=\d+\.|$)'
        numbered_matches = re.findall(numbered_pattern, text)
        if numbered_matches:
            # Clean up the matches
            return [step.strip() for step in numbered_matches if step.strip()]

        # Check for bullet points
        bullet_pattern = r'[•\-*]\s*(.*?)(?=[•\-*]|$)'
        bullet_matches = re.findall(bullet_pattern, text)
        if bullet_matches:
            return [step.strip() for step in bullet_matches if step.strip()]

        # Check for comma-separated or semicolon-separated commands
        if ';' in text:
            # Split by semicolons
            return [step.strip() for step in text.split(';') if step.strip()]
        elif ',' in text and 'and' not in text.lower():
            # If it's a simple comma-separated list (no "and")
            return [step.strip() for step in text.split(',') if step.strip()]

        # Check for "and" or "then" separators
        and_then_pattern = r'(.*?)(?:(?:\s+and\s+|\s+then\s+)(?=\w)|\s*$)'
        and_then_matches = re.findall(and_then_pattern, text)
        if len(and_then_matches) > 1:
            return [step.strip() for step in and_then_matches if step.strip()]

        # If we couldn't identify multiple steps, return the whole text as a single step
        return [text]

    def _handle_browsing_command(self, command: str) -> str:
        """Handle a browsing-related command."""
        # Extract URL or search term
        if "open" in command.lower():
            # Extract what to open
            match = re.search(r"open\s+(.*?)(?:\s+in\s+|\s*$)", command.lower())
            if match:
                site = match.group(1).strip()
                return f"Opening {site} in your browser."

        # Handle search
        if "search" in command.lower():
            match = re.search(r"search(?:\s+for)?\s+(.*?)(?:\s+on\s+|\s*$)", command.lower())
            if match:
                query = match.group(1).strip()
                return f"Searching for '{query}'"

        # Default response
        return "I'll help you browse the web."

    def _handle_media_command(self, command: str) -> str:
        """Handle a media-related command."""
        if "play" in command.lower():
            match = re.search(r"play\s+(.*?)(?:\s+on\s+|\s*$)", command.lower())
            if match:
                media = match.group(1).strip()
                return f"Playing {media} now."

        if "pause" in command.lower() or "stop" in command.lower():
            return "Pausing media playback."

        if "volume" in command.lower():
            if "up" in command.lower() or "increase" in command.lower():
                return "Increasing the volume."
            elif "down" in command.lower() or "decrease" in command.lower():
                return "Decreasing the volume."

        return "I'll help you with media controls."

    def _handle_system_command(self, command: str) -> str:
        """Handle a system-related command."""
        # For safety, we just simulate these commands
        if "shutdown" in command.lower() or "turn off" in command.lower():
            return "I would shut down your system (but I'm just simulating it)."

        if "restart" in command.lower():
            return "I would restart your system (but I'm just simulating it)."

        if "sleep" in command.lower():
            return "I would put your system to sleep (but I'm just simulating it)."

        return "I'll help you with system controls."

    def _handle_files_command(self, command: str) -> str:
        """Handle a file-related command."""
        if "open" in command.lower():
            match = re.search(r"open\s+(.*?)(?:\s+in\s+|\s*$)", command.lower())
            if match:
                file = match.group(1).strip()
                return f"Opening file: {file}"

        if "create" in command.lower():
            match = re.search(r"create\s+(.*?)(?:\s+in\s+|\s*$)", command.lower())
            if match:
                file = match.group(1).strip()
                return f"Creating file: {file}"

        return "I'll help you with file operations."

    def _handle_weather_command(self, command: str) -> str:
        """Handle a weather-related command."""
        # Extract location if specified
        location = "your area"
        match = re.search(r"weather(?:\s+in\s+|\s+for\s+)(.*?)(?:\s+on\s+|\s*$)", command.lower())
        if match:
            location = match.group(1).strip()

        return f"I'll check the weather in {location} for you."

    def _handle_calendar_command(self, command: str) -> str:
        """Handle a calendar-related command."""
        # Get current date for context
        today = datetime.datetime.now()

        if "schedule" in command.lower() or "create" in command.lower():
            return "I'll help you schedule a new event."

        if "what" in command.lower() and ("today" in command.lower() or "have" in command.lower()):
            return f"Let me check your schedule for {today.strftime('%A, %B %d')}."

        return "I'll help you with your calendar."

    def _handle_communication_command(self, command: str) -> str:
        """Handle a communication-related command."""
        if "email" in command.lower() or "send email" in command.lower():
            # Extract recipient if available
            match = re.search(r"email(?:\s+to)?\s+(.*?)(?:\s+about|\s*$)", command.lower())
            if match:
                recipient = match.group(1).strip()
                return f"I'll help you draft an email to {recipient}."

        return "I'll help you with communication."

    def _handle_timer_command(self, command: str) -> str:
        """Handle a timer-related command."""
        # Extract time if specified
        duration = "some time"
        match = re.search(r"(\d+)\s*(minute|second|hour|min|sec|hr)s?", command.lower())
        if match:
            amount = match.group(1)
            unit = match.group(2)
            duration = f"{amount} {unit}"

        if "set" in command.lower() or "start" in command.lower():
            return f"Setting a timer for {duration}."

        if "stop" in command.lower() or "cancel" in command.lower():
            return "Stopping all timers."

        return "I'll help you with timer operations."

    def _handle_general_command(self, command: str) -> str:
        """Handle a general command."""
        return "I'll try to help with your request."

    def register_command_handler(self, category: str, handler: Callable[[str], str]) -> None:
        """
        Register a command handler for a category.

        Args:
            category: Command category
            handler: Function that takes a command string and returns a response string
        """
        self.command_handlers[category] = handler

    def process_multi_step_command(self, command_text: str) -> List[Tuple[str, str]]:
        """
        Process a multi-step command.

        Args:
            command_text: Command text potentially containing multiple steps

        Returns:
            List of (category, response) tuples for each step
        """
        steps = self.extract_steps_from_text(command_text)
        results = []

        for step in steps:
            category, response = self.process_command(step)
            results.append((category, response))

        return results


# Create an instance for easy importing
command_processor = CommandProcessor()


if __name__ == "__main__":
    # Test the command processor
    processor = CommandProcessor()

    # Test single commands
    test_commands = [
        "Open GitHub",
        "Play some music",
        "What's the weather like today?",
        "Send an email to John",
        "Set a timer for 5 minutes"
    ]

    print("Single Command Tests:")
    for cmd in test_commands:
        category, response = processor.process_command(cmd)
        print(f"Command: {cmd}")
        print(f"Category: {category}")
        print(f"Response: {response}")
        print("---")

    # Test multi-step commands
    test_multi_commands = [
        "First, open GitHub, then check my emails",
        "1. Play some relaxing music 2. Set a timer for 20 minutes 3. Open my notes",
        "Check the weather, send an email to Jane, and set a reminder for tomorrow"
    ]

    print("\nMulti-Step Command Tests:")
    for cmd in test_multi_commands:
        steps = processor.extract_steps_from_text(cmd)
        print(f"Command: {cmd}")
        print(f"Extracted steps: {steps}")

        results = processor.process_multi_step_command(cmd)
        for i, (category, response) in enumerate(results):
            print(f"Step {i+1}: {category} - {response}")
        print("---")
