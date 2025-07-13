#!/usr/bin/env python3
"""
Unit tests for the Text-to-Speech Service.
"""

import os
import sys
import unittest
import tempfile
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assistant.tts_service import TTSService

class TestTTSService(unittest.TestCase):
    """Basic tests for TTS Service."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the config manager
        self.config_patcher = patch('assistant.tts_service.config_manager')
        self.mock_config = self.config_patcher.start()
        self.mock_config.get_section.return_value = {
            "engine": "pyttsx3",
            "language": "en",
            "rate": 150,
            "volume": 1.0,
        }

    def tearDown(self):
        """Clean up after tests."""
        self.config_patcher.stop()

    @patch('assistant.tts_service.pyttsx3')
    @patch('assistant.tts_service.PYTTSX3_AVAILABLE', True)
    @patch('assistant.tts_service.GTTS_AVAILABLE', False)
    @patch('assistant.tts_service.TORCH_AVAILABLE', False)
    def test_basic_initialization(self, mock_pyttsx3):
        """Test basic initialization with mocked pyttsx3."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService()

        self.assertEqual(tts.engine_name, "pyttsx3")
        self.assertEqual(tts.language, "en")
        self.assertEqual(tts.rate, 150)
        self.assertEqual(tts.volume, 1.0)

        mock_pyttsx3.init.assert_called_once()
        mock_engine.setProperty.assert_any_call('rate', 150)
        mock_engine.setProperty.assert_any_call('volume', 1.0)

    @patch('assistant.tts_service.pyttsx3')
    @patch('assistant.tts_service.PYTTSX3_AVAILABLE', True)
    def test_set_voice(self, mock_pyttsx3):
        """Test setting voice."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService()
        tts.set_voice("test_voice")

        self.assertEqual(tts.voice_id, "test_voice")
        mock_engine.setProperty.assert_any_call('voice', "test_voice")

    @patch('assistant.tts_service.pyttsx3')
    @patch('assistant.tts_service.PYTTSX3_AVAILABLE', True)
    def test_set_rate(self, mock_pyttsx3):
        """Test setting speech rate."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService()
        tts.set_rate(200)

        self.assertEqual(tts.rate, 200)
        mock_engine.setProperty.assert_any_call('rate', 200)

    @patch('assistant.tts_service.pyttsx3')
    @patch('assistant.tts_service.PYTTSX3_AVAILABLE', True)
    def test_set_volume(self, mock_pyttsx3):
        """Test setting volume."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService()
        tts.set_volume(0.5)

        self.assertEqual(tts.volume, 0.5)
        mock_engine.setProperty.assert_any_call('volume', 0.5)

    @patch('assistant.tts_service.pyttsx3')
    @patch('assistant.tts_service.PYTTSX3_AVAILABLE', True)
    def test_set_language(self, mock_pyttsx3):
        """Test setting language."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService()
        tts.set_language("fr")

        self.assertEqual(tts.language, "fr")

    @patch('assistant.tts_service.pyttsx3')
    @patch('assistant.tts_service.PYTTSX3_AVAILABLE', True)
    def test_speak_with_pyttsx3(self, mock_pyttsx3):
        """Test speaking with pyttsx3."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService()
        tts.speak("Hello world")

        mock_engine.say.assert_called_once_with("Hello world")
        mock_engine.runAndWait.assert_called_once()

    @patch('assistant.tts_service.pyttsx3')
    @patch('assistant.tts_service.PYTTSX3_AVAILABLE', True)
    def test_speak_empty_text(self, mock_pyttsx3):
        """Test speaking empty text."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService()
        tts.speak("")

        mock_engine.say.assert_not_called()
        mock_engine.runAndWait.assert_not_called()


if __name__ == '__main__':
    unittest.main()
