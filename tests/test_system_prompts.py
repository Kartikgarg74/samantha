"""
Test module for the SystemPromptManager class.
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Now import the module to test
from assistant.system_prompts import SystemPromptManager, create_default_prompts


class TestSystemPromptManager(unittest.TestCase):
    """Test cases for SystemPromptManager."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test prompts
        self.temp_dir = tempfile.mkdtemp()
        self.prompt_manager = SystemPromptManager(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def test_init(self):
        """Test initialization."""
        # Verify the prompts directory was created
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertEqual(self.prompt_manager.prompts_dir, Path(self.temp_dir))

    def test_get_prompt_default(self):
        """Test getting default prompt."""
        # Add a default prompt
        self.prompt_manager.add_prompt("default", "Default prompt text")

        # Get a non-existent prompt - should return default
        prompt = self.prompt_manager.get_prompt("nonexistent")
        self.assertEqual(prompt, "Default prompt text")

    def test_add_and_get_prompt(self):
        """Test adding and retrieving prompts."""
        # Add a prompt
        self.prompt_manager.add_prompt("test", "Test prompt")

        # Verify prompt was added to memory
        self.assertIn("test", self.prompt_manager.prompts)
        self.assertEqual(self.prompt_manager.prompts["test"], "Test prompt")

        # Verify prompt can be retrieved
        self.assertEqual(self.prompt_manager.get_prompt("test"), "Test prompt")

    def test_prompt_with_parameters(self):
        """Test prompt with parameters."""
        # Add a prompt with placeholders
        self.prompt_manager.add_prompt("greeting", "Hello {name}, welcome to {service}!")

        # Get prompt with parameters
        prompt = self.prompt_manager.get_prompt("greeting", {
            "name": "User",
            "service": "Samantha"
        })

        self.assertEqual(prompt, "Hello User, welcome to Samantha!")

    def test_save_and_load_prompt(self):
        """Test saving and loading prompts to/from disk."""
        # Add and save a prompt
        self.prompt_manager.add_prompt("test", "Test prompt", save=True)

        # Check that the file was created (any file, since category might differ)
        files_created = os.listdir(self.temp_dir)
        self.assertTrue(len(files_created) > 0)

        # Create a new manager instance to test loading
        new_manager = SystemPromptManager(self.temp_dir)

        # Verify prompt was loaded
        self.assertIn("test", new_manager.prompts)
        self.assertEqual(new_manager.get_prompt("test"), "Test prompt")

    def test_list_contexts(self):
        """Test listing available prompt contexts."""
        # Add prompts
        self.prompt_manager.add_prompt("test1", "Test prompt 1")
        self.prompt_manager.add_prompt("test2", "Test prompt 2")

        # List contexts
        contexts = self.prompt_manager.list_contexts()

        # Verify both prompts are listed
        self.assertIn("test1", contexts)
        self.assertIn("test2", contexts)

    def test_create_default_prompts(self):
        """Test creating default prompts."""
        # Create a temporary directory for default prompts
        temp_default_dir = tempfile.mkdtemp()

        # Create a manager that points to our temp directory
        temp_manager = SystemPromptManager(temp_default_dir)

        try:
            # Create default prompts in the temp directory
            # We need to monkey patch the function temporarily to use our test directory
            original_init = SystemPromptManager.__init__

            def temp_init(self):
                return original_init(self, temp_default_dir)

            # Apply the monkey patch
            SystemPromptManager.__init__ = temp_init

            # Now call create_default_prompts
            create_default_prompts()

            # Restore the original function
            SystemPromptManager.__init__ = original_init

            # Verify some default prompt files were created
            files = os.listdir(temp_default_dir)
            self.assertTrue(any(file.endswith("_prompts.json") for file in files))

            # Load the new manager's prompts
            temp_manager._load_prompts()

            # Verify some default prompts exist
            self.assertIn("default", temp_manager.prompts)
        finally:
            # Clean up temp directory
            for file in os.listdir(temp_default_dir):
                os.remove(os.path.join(temp_default_dir, file))
            os.rmdir(temp_default_dir)

    def test_path_construction(self):
        """Test path construction works correctly."""
        # This test specifically checks our fix for the '/' operator issue

        # Add a prompt that will trigger path construction
        category = "test_category"
        self.prompt_manager.add_prompt(f"{category}.prompt", "Test path construction", save=True)

        # Check that the expected file was created
        expected_file = f"{category}_prompts.json"
        files = os.listdir(self.temp_dir)
        self.assertIn(expected_file, files)

        # Verify the file content
        with open(os.path.join(self.temp_dir, expected_file), 'r') as f:
            content = json.load(f)
            self.assertIn(f"{category}.prompt", content)
            self.assertEqual(content[f"{category}.prompt"], "Test path construction")


if __name__ == "__main__":
    unittest.main()
