"""Configuration manager for Samantha assistant."""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
import platform

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ConfigManager")

class ConfigManager:
    """Manages the configuration settings for the assistant."""

    DEFAULT_CONFIG_PATH = "config.json"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Path to the configuration file. If None, uses the default path.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> bool:
        """
        Load configuration from file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if config file exists
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found at {self.config_path}. Creating default config.")
                self._create_default_config()

            # Load config file
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            # Apply system-specific overrides
            self._apply_system_specific_config()

            logger.info(f"Configuration loaded successfully from {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            # Load fallback minimal configuration
            self.config = self._get_minimal_config()
            return False

    def _create_default_config(self) -> None:
        """Create a default configuration file."""
        default_config = self._get_default_config()

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Default configuration created at {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")

    def _get_minimal_config(self) -> Dict[str, Any]:
        """Return a minimal working configuration."""
        return {
            "assistant": {
                "name": "Samantha",
                "wake_words": ["samantha", "hey samantha"]
            },
            "speech_recognition": {
                "model_size": "tiny",
                "device": "cpu"
            },
            "tts": {
                "rate": 180,
                "volume": 0.8
            }
        }

    def _get_default_config(self) -> Dict[str, Any]:
        """Return a complete default configuration."""
        # This would normally be much more comprehensive,
        # but we'll use a simplified version here
        return {
            "assistant": {
                "name": "Samantha",
                "version": "1.0.0",
                "wake_words": ["samantha", "hey samantha", "hello samantha"],
                "language": "en-US"
            },
            "speech_recognition": {
                "model_size": "tiny",
                "device": "auto",
                "vad": {
                    "enabled": True,
                    "threshold": 0.5,
                    "sensitivity": 0.75
                }
            },
            "tts": {
                "engine": "system",
                "rate": 180,
                "volume": 0.8
            },
            "memory": {
                "max_conversations": 100,
                "file_path": "assistant_memory.json"
            },
            "models": {
                "intent_classifier": {
                    "device": "auto"
                }
            }
        }

    def _apply_system_specific_config(self) -> None:
        """Apply system-specific configuration overrides."""
        system = platform.system().lower()

        # Detect system capabilities
        if system == "darwin":  # macOS
            # Check for Apple Silicon
            if platform.processor() == "arm":
                # Set device to MPS for Apple Silicon if available
                try:
                    import torch
                    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                        self.set("models.intent_classifier.device", "mps")
                        logger.info("Using MPS (Metal Performance Shaders) for ML acceleration")
                except:
                    pass

        elif system == "linux":
            # Linux-specific settings
            pass

        elif system == "windows":
            # Windows-specific settings
            pass

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key_path: Path to the config value (e.g., "speech_recognition.vad.threshold")
            default: Default value to return if key not found

        Returns:
            Configuration value or default if not found
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.

        Args:
            key_path: Path to the config value (e.g., "speech_recognition.vad.threshold")
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config

        # Navigate to the parent of the key to set
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        config[keys[-1]] = value

    def save(self) -> bool:
        """
        Save the current configuration to file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.

        Args:
            section: Section name

        Returns:
            Dictionary containing the section configuration or empty dict if not found
        """
        return self.config.get(section, {})

    def update_section(self, section: str, values: Dict[str, Any]) -> None:
        """
        Update an entire configuration section.

        Args:
            section: Section name
            values: New values for the section
        """
        if section in self.config:
            # Update existing section
            self.config[section].update(values)
        else:
            # Create new section
            self.config[section] = values


# Create a singleton instance
config_manager = ConfigManager()

if __name__ == "__main__":
    # Test the configuration manager
    print(f"Assistant name: {config_manager.get('assistant.name')}")
    print(f"VAD threshold: {config_manager.get('speech_recognition.vad.threshold')}")

    # Test setting a value
    config_manager.set('speech_recognition.vad.threshold', 0.6)
    print(f"New VAD threshold: {config_manager.get('speech_recognition.vad.threshold')}")
