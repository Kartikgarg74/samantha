"""
Command Processor Module for handling multi-step operations.
Manages complex command sequences and transitions between command steps.
"""

import time
import uuid
from typing import List, Dict, Any, Callable, Optional, Tuple
from collections import deque
from enum import Enum
from datetime import datetime


class CommandState(Enum):
    """Command execution state enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Command:
    """Represents a single command in a sequence"""

    def __init__(self, text: str, intent: str = None, parameters: Dict[str, Any] = None):
        """
        Initialize a command

        Args:
            text: The raw command text
            intent: The detected intent (optional)
            parameters: Command parameters (optional)
        """
        self.id = str(uuid.uuid4())[:8]
        self.text = text
        self.intent = intent
        self.parameters = parameters or {}
        self.state = CommandState.PENDING
        self.result = None
        self.created_at = datetime.now()
        self.completed_at = None
        self.error = None


class CommandSequence:
    """Manages a sequence of related commands"""

    def __init__(self, name: str, description: str = "", require_confirmation: bool = True):
        """
        Initialize a command sequence

        Args:
            name: Name of the sequence
            description: Description of what the sequence does
            require_confirmation: Whether to require confirmation between steps
        """
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.description = description
        self.commands: List[Command] = []
        self.current_index = -1  # No command is active initially
        self.state = CommandState.PENDING
        self.created_at = datetime.now()
        self.completed_at = None
        self.require_confirmation = require_confirmation

    def add_command(self, command: Command) -> None:
        """Add a command to the sequence"""
        self.commands.append(command)

    def get_current_command(self) -> Optional[Command]:
        """Get the current command in the sequence"""
        if 0 <= self.current_index < len(self.commands):
            return self.commands[self.current_index]
        return None

    def get_next_command(self) -> Optional[Command]:
        """Get the next command in the sequence without advancing"""
        if self.current_index + 1 < len(self.commands):
            return self.commands[self.current_index + 1]
        return None

    def advance(self) -> Optional[Command]:
        """Advance to the next command and return it"""
        if self.current_index + 1 < len(self.commands):
            self.current_index += 1
            self.commands[self.current_index].state = CommandState.IN_PROGRESS
            return self.commands[self.current_index]
        else:
            self.state = CommandState.COMPLETED
            self.completed_at = datetime.now()
            return None

    def mark_current_complete(self, result: Any = None) -> None:
        """Mark the current command as completed with an optional result"""
        if 0 <= self.current_index < len(self.commands):
            self.commands[self.current_index].state = CommandState.COMPLETED
            self.commands[self.current_index].result = result
            self.commands[self.current_index].completed_at = datetime.now()

    def mark_current_failed(self, error: str) -> None:
        """Mark the current command as failed with an error message"""
        if 0 <= self.current_index < len(self.commands):
            self.commands[self.current_index].state = CommandState.FAILED
            self.commands[self.current_index].error = error
            self.state = CommandState.FAILED

    def is_complete(self) -> bool:
        """Check if the entire sequence is complete"""
        return (self.current_index == len(self.commands) - 1 and
                self.commands[self.current_index].state == CommandState.COMPLETED)

    def requires_confirmation(self) -> bool:
        """Check if the current step requires confirmation before proceeding"""
        return self.require_confirmation

    def summary(self) -> Dict[str, Any]:
        """Generate a summary of the command sequence"""
        completed = sum(1 for cmd in self.commands if cmd.state == CommandState.COMPLETED)

        return {
            "id": self.id,
            "name": self.name,
            "total_steps": len(self.commands),
            "completed_steps": completed,
            "current_step": self.current_index + 1 if self.current_index >= 0 else 0,
            "state": self.state.value,
            "require_confirmation": self.require_confirmation,
        }


class CommandProcessor:
    """Processes and manages command sequences"""

    def __init__(self, command_handlers: Dict[str, Callable] = None):
        """
        Initialize the command processor

        Args:
            command_handlers: Dictionary mapping intents to handler functions
        """
        self.command_handlers = command_handlers or {}
        self.active_sequence: Optional[CommandSequence] = None
        self.sequence_queue = deque()
        self.awaiting_confirmation = False
        self.command_history: List[CommandSequence] = []

    def register_handler(self, intent: str, handler: Callable) -> None:
        """Register a handler for a specific intent"""
        self.command_handlers[intent] = handler

    def create_sequence(self, name: str, commands: List[str],
                        require_confirmation: bool = True) -> CommandSequence:
        """
        Create a new command sequence

        Args:
            name: Name of the sequence
            commands: List of command strings
            require_confirmation: Whether to require confirmation between steps

        Returns:
            The created CommandSequence
        """
        sequence = CommandSequence(name, require_confirmation=require_confirmation)

        for cmd_text in commands:
            command = Command(cmd_text)
            sequence.add_command(command)

        return sequence

    def queue_sequence(self, sequence: CommandSequence) -> None:
        """Add a command sequence to the queue"""
        self.sequence_queue.append(sequence)

        # If no active sequence, start processing the queue
        if self.active_sequence is None:
            self._process_next_from_queue()

    def _process_next_from_queue(self) -> bool:
        """Process the next sequence from the queue"""
        if not self.sequence_queue:
            return False

        self.active_sequence = self.sequence_queue.popleft()
        self.active_sequence.state = CommandState.IN_PROGRESS

        # Start the first command
        first_command = self.active_sequence.advance()
        if first_command:
            return True

        return False

    def process_current_command(self) -> Tuple[str, Any]:
        """
        Process the current command in the active sequence

        Returns:
            Tuple of (response message, result data)
        """
        if not self.active_sequence:
            return "No active command sequence.", None

        current_command = self.active_sequence.get_current_command()
        if not current_command:
            return "No current command to process.", None

        # Determine the intent if not already set
        if not current_command.intent and current_command.text:
            # In a real implementation, this would use your intent classifier
            # For now, we'll assume a simple keyword-based intent detection
            text_lower = current_command.text.lower()
            if "spotify" in text_lower or "play" in text_lower or "music" in text_lower:
                current_command.intent = "spotify"
            elif "browser" in text_lower or "web" in text_lower or "search" in text_lower:
                current_command.intent = "browser"
            elif "whatsapp" in text_lower or "message" in text_lower or "send" in text_lower:
                current_command.intent = "whatsapp"
            else:
                current_command.intent = "general"

        # Execute the command handler for this intent
        handler = self.command_handlers.get(current_command.intent)
        if not handler:
            self.active_sequence.mark_current_failed(f"No handler found for intent: {current_command.intent}")
            return f"I don't know how to process '{current_command.text}'", None

        try:
            response, result = handler(current_command.text, current_command.parameters)
            self.active_sequence.mark_current_complete(result)
            return response, result
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            self.active_sequence.mark_current_failed(error_msg)
            return error_msg, None

    def advance_sequence(self) -> Tuple[bool, Optional[Command], str]:
        """
        Advance to the next command in the active sequence

        Returns:
            Tuple of (success, next_command, message)
        """
        if not self.active_sequence:
            return False, None, "No active command sequence."

        # Check if we're awaiting confirmation and handle it
        if self.awaiting_confirmation:
            self.awaiting_confirmation = False

        next_command = self.active_sequence.advance()
        if next_command:
            return True, next_command, f"Moving to next step: {next_command.text}"
        else:
            # Sequence is complete
            self.command_history.append(self.active_sequence)
            self.active_sequence = None

            # Process next sequence in queue if available
            if self._process_next_from_queue():
                return True, self.active_sequence.get_current_command(), "Started next command sequence."

            return True, None, "Command sequence completed."

    def handle_confirmation(self, confirmed: bool) -> Tuple[bool, str]:
        """
        Handle user confirmation to proceed with the next step

        Args:
            confirmed: Whether the user confirmed proceeding

        Returns:
            Tuple of (success, message)
        """
        if not self.awaiting_confirmation:
            return False, "No confirmation was requested."

        if not confirmed:
            # Cancel the current sequence
            if self.active_sequence:
                self.active_sequence.state = CommandState.CANCELLED
                self.command_history.append(self.active_sequence)
                self.active_sequence = None
                self.awaiting_confirmation = False

                # Process next sequence in queue if available
                if self._process_next_from_queue():
                    return True, "Command cancelled. Started next command sequence."

                return True, "Command sequence cancelled."

        # User confirmed, proceed with next step
        self.awaiting_confirmation = False
        success, next_command, message = self.advance_sequence()
        return success, message

    def request_confirmation(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Request confirmation before proceeding to the next step

        Returns:
            Tuple of (success, confirmation message, next step info)
        """
        if not self.active_sequence:
            return False, "No active command sequence.", {}

        next_command = self.active_sequence.get_next_command()
        if not next_command:
            return False, "No next step to confirm.", {}

        self.awaiting_confirmation = True

        current_progress = self.active_sequence.summary()
        next_step_info = {
            "text": next_command.text,
            "step_number": self.active_sequence.current_index + 2,  # 1-indexed for user display
            "total_steps": len(self.active_sequence.commands)
        }

        confirm_message = f"Ready for step {next_step_info['step_number']} of {next_step_info['total_steps']}: {next_command.text}. Should I proceed?"

        return True, confirm_message, next_step_info

    def is_awaiting_confirmation(self) -> bool:
        """Check if the processor is waiting for confirmation"""
        return self.awaiting_confirmation

    def cancel_all(self) -> str:
        """Cancel all command sequences"""
        if self.active_sequence:
            self.active_sequence.state = CommandState.CANCELLED
            self.command_history.append(self.active_sequence)

        self.active_sequence = None
        self.sequence_queue.clear()
        self.awaiting_confirmation = False

        return "All command sequences cancelled."

    def get_active_sequence_summary(self) -> Optional[Dict[str, Any]]:
        """Get a summary of the active sequence"""
        if self.active_sequence:
            return self.active_sequence.summary()
        return None


# Utility functions for working with the command processor

def extract_steps_from_text(text: str) -> List[str]:
    """
    Extract command steps from text

    Args:
        text: Text containing multiple commands

    Returns:
        List of individual command strings
    """
    # This is a simple implementation - in practice, you would use NLP or LLMs
    # to identify steps in a more sophisticated way

    # Look for numbered lists (1. Do this, 2. Do that)
    if any(f"{i}." in text for i in range(1, 10)):
        steps = []
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        for line in lines:
            # Try to match numbered steps
            for i in range(1, 10):
                prefix = f"{i}."
                if line.startswith(prefix):
                    steps.append(line[len(prefix):].strip())

        if steps:
            return steps

    # Look for "and" or "then" sequences
    connectors = [" and ", " then ", " after that ", " next ", " finally "]
    for connector in connectors:
        if connector in text.lower():
            return [step.strip() for step in text.split(connector) if step.strip()]

    # No multi-step command detected
    return [text]

def is_confirmation(text: str) -> Tuple[bool, bool]:
    """
    Check if text is a confirmation or rejection

    Args:
        text: User's response text

    Returns:
        Tuple of (is_confirmation_response, confirmed)
    """
    text = text.lower().strip()

    confirmation_terms = ["yes", "yeah", "yep", "sure", "ok", "okay", "proceed",
                          "continue", "go ahead", "do it", "confirm"]
    rejection_terms = ["no", "nope", "don't", "stop", "cancel", "wait", "hold on", "abort"]

    # Check if this is a confirmation response at all
    is_confirmation_response = any(term in text for term in confirmation_terms + rejection_terms)

    # Check if it's a positive confirmation
    confirmed = any(term in text for term in confirmation_terms)

    return is_confirmation_response, confirmed


# Example usage
if __name__ == "__main__":
    # Define some example handlers
    def handle_spotify(text, params):
        return f"Handling Spotify command: {text}", {"status": "played"}

    def handle_browser(text, params):
        return f"Handling browser command: {text}", {"url": "https://example.com"}

    # Create and set up processor
    processor = CommandProcessor()
    processor.register_handler("spotify", handle_spotify)
    processor.register_handler("browser", handle_browser)

    # Create a sequence
    sequence = processor.create_sequence(
        "Music and Web",
        ["Play my workout playlist", "Open GitHub in browser"],
        require_confirmation=True
    )

    # Queue and process
    processor.queue_sequence(sequence)

    # Process first command
    response, result = processor.process_current_command()
    print(f"Command response: {response}")

    # Request confirmation for next step
    success, message, next_info = processor.request_confirmation()
    print(f"Confirmation request: {message}")

    # Simulate user confirming
    processor.handle_confirmation(True)

    # Process next command
    response, result = processor.process_current_command()
    print(f"Command response: {response}")
