#!/usr/bin/env python3
"""
Unit tests for the Configuration Manager.
Tests configuration loading, saving, and accessing settings.
"""

import os
import sys
import json
import unittest
import tempfile
from unittest.mock import patch, mock_open, MagicMock

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to test
from assistant.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    """Test cases for the Configuration Manager."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()

        # Sample test configuration
        self.test_config = {
            "assistant": {
                "name": "Test Assistant",
                "wake_words": ["test", "hey test"]
            },
            "speech_recognition": {
                "model_size": "tiny",
                "device": "cpu"
            },
            "tts": {
                "rate": 150,
                "volume": 0.7
            }
        }

        # Write the test configuration to the temporary file
        with open(self.temp_file.name, 'w', encoding='utf-8') as f:
            json.dump(self.test_config, f)

    def tearDown(self):
        """Clean up test fixtures after each test."""
        # Remove the temporary file
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_init_with_valid_path(self):
        """Test initialization with a valid configuration file path."""
        config_manager = ConfigManager(self.temp_file.name)

        # Verify that the config was loaded correctly
        self.assertEqual(config_manager.config_path, self.temp_file.name)
        self.assertEqual(config_manager.get('assistant.name'), "Test Assistant")
        self.assertEqual(config_manager.get('speech_recognition.model_size'), "tiny")

    def test_init_with_nonexistent_path(self):
        """Test initialization with a non-existent file path."""
        # Use a file path that doesn't exist
        nonexistent_path = "nonexistent_config.json"

        # Prepare a valid default config for mocking
        default_config = {
            "assistant": {"name": "Samantha"},
            "speech_recognition": {"model_size": "tiny"},
            "tts": {"rate": 180, "volume": 0.8}
        }

        # Mock _get_default_config to return our simplified default config
        with patch('assistant.config_manager.ConfigManager._get_default_config',
                return_value=default_config), \
            patch('os.path.exists', return_value=False), \
            patch('builtins.open', mock_open()) as mock_file, \
            patch('json.dump') as mock_json_dump:

            # Create the config manager
            config_manager = ConfigManager(nonexistent_path)

            # Verify the minimal configuration was used
            self.assertEqual(config_manager.get('assistant.name'), "Samantha")

            # Verify that open was called for writing
            mock_file.assert_any_call(nonexistent_path, 'w', encoding='utf-8')

    def test_load_config_with_invalid_json(self):
        """Test loading an invalid JSON configuration file."""
        # Create a file with invalid JSON
        invalid_json_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        invalid_json_file.write(b'{ invalid json')
        invalid_json_file.close()

        # Initialize with the invalid file
        config_manager = ConfigManager(invalid_json_file.name)

        # Verify that the minimal config was used as a fallback
        self.assertEqual(config_manager.get('assistant.name'), "Samantha")

        # Clean up
        os.remove(invalid_json_file.name)

    def test_get_valid_keys(self):
        """Test getting valid configuration keys."""
        config_manager = ConfigManager(self.temp_file.name)

        # Test various get operations
        self.assertEqual(config_manager.get('assistant.name'), "Test Assistant")
        self.assertEqual(config_manager.get('tts.rate'), 150)
        self.assertEqual(config_manager.get('speech_recognition.device'), "cpu")

        # Test nested keys
        wake_words = config_manager.get('assistant.wake_words')
        self.assertIsInstance(wake_words, list)
        self.assertEqual(len(wake_words), 2)
        self.assertIn("test", wake_words)

    def test_get_invalid_keys(self):
        """Test getting invalid configuration keys."""
        config_manager = ConfigManager(self.temp_file.name)

        # Test with invalid keys
        self.assertIsNone(config_manager.get('invalid.key'))
        self.assertEqual(config_manager.get('nonexistent.path', 'default'), 'default')

        # Test with partially valid path
        self.assertIsNone(config_manager.get('assistant.nonexistent'))

    def test_set_and_get_values(self):
        """Test setting and getting configuration values."""
        config_manager = ConfigManager(self.temp_file.name)

        # Set some values
        config_manager.set('assistant.name', "New Name")
        config_manager.set('tts.rate', 200)

        # Verify the values were set correctly
        self.assertEqual(config_manager.get('assistant.name'), "New Name")
        self.assertEqual(config_manager.get('tts.rate'), 200)

        # Set a value with a new path
        config_manager.set('new_section.key', "value")
        self.assertEqual(config_manager.get('new_section.key'), "value")

        # Set a nested value with new intermediate paths
        config_manager.set('deep.nested.path.key', 42)
        self.assertEqual(config_manager.get('deep.nested.path.key'), 42)

    def test_save_config(self):
        """Test saving configuration to a file."""
        config_manager = ConfigManager(self.temp_file.name)

        # Modify the configuration
        config_manager.set('assistant.name', "Modified Name")

        # Save the configuration
        result = config_manager.save()
        self.assertTrue(result)

        # Load the saved configuration from the file
        with open(self.temp_file.name, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)

        # Verify the saved configuration
        self.assertEqual(saved_config['assistant']['name'], "Modified Name")
        self.assertEqual(saved_config['tts']['rate'], 150)  # Original value

    def test_save_with_file_error(self):
        """Test saving configuration with a file write error."""
        config_manager = ConfigManager(self.temp_file.name)

        # Mock the open function to raise an exception
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = config_manager.save()
            self.assertFalse(result)

    def test_get_section(self):
        """Test getting a complete configuration section."""
        config_manager = ConfigManager(self.temp_file.name)

        # Get a section
        tts_section = config_manager.get_section('tts')

        # Verify the section
        self.assertIsInstance(tts_section, dict)
        self.assertEqual(tts_section['rate'], 150)
        self.assertEqual(tts_section['volume'], 0.7)

        # Test with a non-existent section
        empty_section = config_manager.get_section('nonexistent')
        self.assertEqual(empty_section, {})

    def test_update_section(self):
        """Test updating a complete configuration section."""
        config_manager = ConfigManager(self.temp_file.name)

        # Update an existing section
        config_manager.update_section('tts', {'rate': 200, 'new_key': 'value'})

        # Verify the update
        tts_section = config_manager.get_section('tts')
        self.assertEqual(tts_section['rate'], 200)
        self.assertEqual(tts_section['volume'], 0.7)  # Original value preserved
        self.assertEqual(tts_section['new_key'], 'value')  # New value added

        # Update a new section
        config_manager.update_section('new_section', {'key': 'value'})

        # Verify the new section
        new_section = config_manager.get_section('new_section')
        self.assertEqual(new_section['key'], 'value')

    @patch('platform.system')
    @patch('platform.processor')
    def test_system_specific_config_macos(self, mock_processor, mock_system):
        """Test system-specific configuration for macOS."""
        # Mock platform detection for macOS with Apple Silicon
        mock_system.return_value = "Darwin"
        mock_processor.return_value = "arm"

        # Mock torch for MPS detection
        mock_torch = MagicMock()
        mock_torch.backends.mps.is_available.return_value = True

        with patch.dict('sys.modules', {'torch': mock_torch}):
            config_manager = ConfigManager(self.temp_file.name)

            # Verify the system-specific config was applied
            self.assertEqual(config_manager.get('models.intent_classifier.device'), "mps")

    def test_minimal_config(self):
        """Test the minimal configuration."""
        config_manager = ConfigManager(self.temp_file.name)

        # Get the minimal config
        minimal_config = config_manager._get_minimal_config()

        # Verify key elements
        self.assertEqual(minimal_config['assistant']['name'], "Samantha")
        self.assertIn("speech_recognition", minimal_config)
        self.assertIn("tts", minimal_config)

    def test_default_config(self):
        """Test the default configuration."""
        config_manager = ConfigManager(self.temp_file.name)

        # Get the default config
        default_config = config_manager._get_default_config()

        # Verify it has more sections than the minimal config
        self.assertIn("memory", default_config)
        self.assertIn("models", default_config)

        # Verify some specific values
        self.assertEqual(default_config['assistant']['name'], "Samantha")
        self.assertTrue(default_config['speech_recognition']['vad']['enabled'])
        self.assertEqual(default_config['memory']['max_conversations'], 100)


import pytest

@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file for testing."""
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
    temp_file.close()

    # Sample configuration
    test_config = {
        "assistant": {"name": "Test Assistant"},
        "settings": {"value": 42}
    }

    # Write the configuration to the file
    with open(temp_file.name, 'w', encoding='utf-8') as f:
        json.dump(test_config, f)

    yield temp_file.name

    # Cleanup after tests
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)

def test_config_singleton():
    """Test that the config_manager is a singleton instance."""
    from assistant.config_manager import config_manager

    # The singleton should be an instance of ConfigManager
    assert isinstance(config_manager, ConfigManager)

    # Multiple imports should return the same instance
    from assistant.config_manager import config_manager as cm2
    assert config_manager is cm2

def test_load_and_get(temp_config_file):
    """Test loading a configuration and getting values."""
    config_manager = ConfigManager(temp_config_file)

    # Test getting values
    assert config_manager.get('assistant.name') == "Test Assistant"
    assert config_manager.get('settings.value') == 42

    # Test default value for missing keys
    assert config_manager.get('missing.key', 'default') == 'default'

def test_set_and_save(temp_config_file):
    """Test setting values and saving the configuration."""
    config_manager = ConfigManager(temp_config_file)

    # Set some values
    config_manager.set('assistant.name', "New Name")
    config_manager.set('new_section.key', "value")

    # Save the configuration
    config_manager.save()

    # Create a new instance to load from the saved file
    new_config = ConfigManager(temp_config_file)

    # Verify the values were saved
    assert new_config.get('assistant.name') == "New Name"
    assert new_config.get('new_section.key') == "value"
    assert new_config.get('settings.value') == 42  # Original value preserved

@pytest.mark.parametrize("key_path,value,expected", [
    ("simple.key", 42, 42),
    ("nested.deep.path", "test", "test"),
    ("very.deep.nested.path.key", [1, 2, 3], [1, 2, 3]),
    ("existing.with.new.key", {"a": 1}, {"a": 1})
])
def test_set_various_paths(temp_config_file, key_path, value, expected):
    """Test setting values with various path structures."""
    config_manager = ConfigManager(temp_config_file)

    # Set the value
    config_manager.set(key_path, value)

    # Verify it was set correctly
    assert config_manager.get(key_path) == expected

if __name__ == '__main__':
    unittest.main()
