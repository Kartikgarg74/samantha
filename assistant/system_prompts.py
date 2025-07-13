"""
System Prompts Module

This module manages system prompts for different contexts,
allowing context-specific prompt selection and customization.
"""

from typing import Dict, Optional, List, Any
import json
import os
from pathlib import Path


class SystemPromptManager:
    """
    Manages system prompts for different contexts and provides
    customization capabilities.
    """

    def __init__(self, prompts_dir: str = None):
        """
        Initialize the SystemPromptManager.

        Args:
            prompts_dir: Directory containing prompt files.
                         Defaults to a 'prompts' directory in the same folder as this module.
        """
        if prompts_dir is None:
            # Use os.path.join instead of / operator to avoid the str/str error
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.prompts_dir = Path(os.path.join(base_dir, "prompts"))
        else:
            self.prompts_dir = Path(prompts_dir)

        # Ensure prompts directory exists
        os.makedirs(self.prompts_dir, exist_ok=True)

        # Core prompts dictionary
        self.prompts: Dict[str, str] = {}

        # Load prompts from files
        self._load_prompts()

    def _load_prompts(self) -> None:
        """Load prompts from JSON files in the prompts directory."""
        try:
            for prompt_file in self.prompts_dir.glob("*.json"):
                with open(prompt_file, "r", encoding="utf-8") as f:
                    prompts_data = json.load(f)
                    for key, value in prompts_data.items():
                        self.prompts[key] = value
        except Exception as e:
            print(f"Error loading prompts: {e}")

    def get_prompt(self, context: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Get a system prompt for a specific context with optional parameters.

        Args:
            context: The context identifier (e.g., 'browser', 'spotify', 'general')
            parameters: Optional parameters to customize the prompt

        Returns:
            Formatted system prompt string
        """
        if context not in self.prompts:
            return self.prompts.get("default", "You are a helpful AI assistant.")

        prompt_template = self.prompts[context]

        # If parameters provided, format the prompt
        if parameters:
            try:
                return prompt_template.format(**parameters)
            except KeyError as e:
                print(f"Missing parameter in prompt: {e}")
                return prompt_template

        return prompt_template

    def add_prompt(self, context: str, prompt_text: str, save: bool = True) -> None:
        """
        Add or update a system prompt.

        Args:
            context: The context identifier
            prompt_text: The system prompt text
            save: Whether to save to disk
        """
        self.prompts[context] = prompt_text

        if save:
            self._save_prompt(context, prompt_text)

    def _save_prompt(self, context: str, prompt_text: str) -> None:
        """Save a prompt to its appropriate file based on category."""
        # Determine which file this prompt belongs to
        category = context.split('.')[0] if '.' in context else "general"

        # Use os.path.join instead of / operator for file path construction
        file_path = os.path.join(self.prompts_dir, f"{category}_prompts.json")
        file_path = Path(file_path)

        # Load existing file or create new
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                prompts_data = json.load(f)
        else:
            prompts_data = {}

        # Update and save
        prompts_data[context] = prompt_text
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(prompts_data, f, indent=2)

    def list_contexts(self) -> List[str]:
        """List all available prompt contexts."""
        return list(self.prompts.keys())


# Create some default prompt templates
DEFAULT_PROMPTS = {
    "default": "You are a helpful AI assistant that provides clear and concise responses.",

    "browser.general": """You are a browser control assistant.
You help users navigate web pages, extract information, and perform actions in the browser.
Always be precise with your instructions and confirm successful operations.""",

    "spotify.general": """You are a Spotify control assistant.
You can search for songs, artists, and playlists, and control playback.
Provide helpful music recommendations when appropriate.""",

    "coding.general": """You are a coding assistant.
Provide clear, well-documented code examples and explanations.
Follow best practices and consider performance, security, and readability.""",

    "email.general": """You are an email assistant.
Help draft professional emails that are clear, concise, and appropriate for the context.
Suggest improvements to existing drafts when asked."""
}


def create_default_prompts():
    """Create default prompt files if they don't exist."""
    manager = SystemPromptManager()

    # Group prompts by category
    categorized_prompts = {}
    for key, value in DEFAULT_PROMPTS.items():
        category = key.split('.')[0] if '.' in key else "general"
        if category not in categorized_prompts:
            categorized_prompts[category] = {}
        categorized_prompts[category][key] = value

    # Save each category to its own file
    for category, prompts in categorized_prompts.items():
        # Use os.path.join instead of / operator
        file_path = os.path.join(manager.prompts_dir, f"{category}_prompts.json")
        file_path = Path(file_path)

        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(prompts, f, indent=2)


# Create an instance for easy importing
prompt_manager = SystemPromptManager()

# Create default prompts if they don't exist
create_default_prompts()


if __name__ == "__main__":
    # Example usage
    print(prompt_manager.get_prompt("default"))
    print(prompt_manager.get_prompt("browser.general"))

    # Example with parameters
    custom_prompt = "Hello {name}, I'll help you with {task}."
    prompt_manager.add_prompt("custom", custom_prompt, save=False)
    print(prompt_manager.get_prompt("custom", {"name": "User", "task": "coding"}))
