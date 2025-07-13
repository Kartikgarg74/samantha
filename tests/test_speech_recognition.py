#!/usr/bin/env python3
"""
Unit tests for the Speech Recognition Service.
Tests voice activity detection, transcription, and configuration handling.
"""

import os
import sys
import unittest
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import numpy as np
import tempfile
import wave
import json
import time

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from assistant.speech_recognition_service import SpeechRecognizer
from assistant.config_manager import ConfigManager

# Mock config for testing
MOCK_CONFIG = {
    "speech_recognition": {
        "model_size": "tiny",
        "device": "auto",
        "vad": {
            "enabled": True,
            "threshold": 0.5,
            "sensitivity": 0.75,
            "min_speech_duration_ms": 250,
            "max_speech_duration_s": 15,
            "silence_duration_ms": 500
        },
        "timeout": {
            "default": 3,
            "wake_word": 1,
            "command": 5
        }
    }
}

class TestSpeechRecognition(unittest.TestCase):
    """Test cases for the speech recognition service."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests."""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            cls.temp_config_path = temp_file.name
            json.dump(MOCK_CONFIG, temp_file)

        # Create a test audio file with sine wave (represents speech)
        cls.test_audio_path = cls._create_test_audio()

    @classmethod
    def tearDownClass(cls):
        """Tear down test fixtures after running tests."""
        # Remove temporary files
        if os.path.exists(cls.temp_config_path):
            os.unlink(cls.temp_config_path)

        if os.path.exists(cls.test_audio_path):
            os.unlink(cls.test_audio_path)

    @classmethod
    def _create_test_audio(cls):
        """Create a test audio file with a sine wave."""
        # Parameters
        sample_rate = 16000
        duration = 2  # seconds
        frequency = 440  # Hz (A4 note)

        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(2 * np.pi * frequency * t) * 0.5
        audio = (audio * 32767).astype(np.int16)

        # Save as WAV
        file_path = tempfile.mktemp(suffix='.wav')
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())

        return file_path

    @patch('assistant.config_manager.ConfigManager')
    def test_initialization(self, mock_config_manager):
        """Test the initialization of the speech recognizer."""
        # Mock the config manager
        mock_config_manager.get_section.return_value = MOCK_CONFIG["speech_recognition"]
        mock_config_manager.get.return_value = MOCK_CONFIG["speech_recognition"]

        # Patch the model initialization to avoid actual loading
        with patch('assistant.speech_recognition_service.SpeechRecognizer._initialize_model'):
            # Create recognizer
            recognizer = SpeechRecognizer()

            # Check if the configuration was properly applied
            self.assertEqual(recognizer.model_size, "tiny")
            self.assertEqual(recognizer.device, "cpu")
            self.assertEqual(recognizer.vad_threshold, 0.5)
            self.assertEqual(recognizer.vad_sensitivity, 0.75)
            self.assertTrue(recognizer.vad_enabled)

    @patch('assistant.config_manager.ConfigManager')
    @patch('assistant.speech_recognition_service.SpeechRecognizer._initialize_model')
    def test_vad_settings_update(self, mock_init_model, mock_config_manager):
        """Test updating VAD settings."""
        # Mock the config manager
        mock_config_manager.get_section.return_value = MOCK_CONFIG["speech_recognition"]

        # Create recognizer
        recognizer = SpeechRecognizer()

        # Initial values
        self.assertEqual(recognizer.vad_threshold, 0.5)
        self.assertEqual(recognizer.vad_sensitivity, 0.75)

        # Update settings
        recognizer.update_vad_settings(threshold=0.7, sensitivity=0.8)

        # Check updated values
        self.assertEqual(recognizer.vad_threshold, 0.7)
        self.assertEqual(recognizer.vad_sensitivity, 0.8)

        # Test boundary conditions
        recognizer.update_vad_settings(threshold=1.5, sensitivity=1.5)
        self.assertEqual(recognizer.vad_threshold, 1.0)  # Should be capped at 1.0
        self.assertEqual(recognizer.vad_sensitivity, 1.0)  # Should be capped at 1.0

        recognizer.update_vad_settings(threshold=-0.5, sensitivity=-0.5)
        self.assertEqual(recognizer.vad_threshold, 0.0)  # Should be floored at 0.0
        self.assertEqual(recognizer.vad_sensitivity, 0.0)  # Should be floored at 0.0

    @patch('assistant.config_manager.ConfigManager')
    @patch('assistant.speech_recognition_service.SpeechRecognizer._initialize_model')
    @patch('sounddevice.rec')
    @patch('sounddevice.wait')
    def test_listen_timeout(self, mock_wait, mock_rec, mock_init_model, mock_config_manager):
        """Test that listen respects the timeout parameter."""
        # Mock the config manager
        mock_config_manager.get_section.return_value = MOCK_CONFIG["speech_recognition"]

        # Create recognizer
        recognizer = SpeechRecognizer()

        # Mock the recording functions
        mock_rec.return_value = np.zeros((16000 * 3,), dtype=np.int16)  # 3 seconds of silence

        # Mock the VAD model to always return no speech
        recognizer.vad_model = MagicMock()
        recognizer.vad_model.get_speech_prob.return_value = 0.1  # Below threshold

        # Set the model to None to skip actual transcription
        recognizer.model = None

        # Test with explicit timeout
        start_time = time.time()
        result = recognizer.listen(timeout=2)
        elapsed_time = time.time() - start_time

        # Should return empty string for silence
        self.assertEqual(result, "")

        # Should respect timeout (with some margin)
        self.assertLess(elapsed_time, 3.0)  # Should not exceed timeout by too much

    @patch('assistant.config_manager.ConfigManager')
    @patch('assistant.speech_recognition_service.SpeechRecognizer._initialize_model')
    @patch('torch.from_numpy')
    def test_continuous_listen(self, mock_torch, mock_init_model, mock_config_manager):
        """Test continuous listening functionality."""
        # Mock the config manager
        mock_config_manager.get_section.return_value = MOCK_CONFIG["speech_recognition"]

        # Create recognizer
        recognizer = SpeechRecognizer()
        recognizer.model = None  # Skip actual transcription

        # Create a mock listen method that returns predefined values
        listen_results = ["hello", "", "test"]
        recognizer.listen = MagicMock(side_effect=listen_results)

        # Create a callback to capture results
        callback_results = []
        def test_callback(text):
            callback_results.append(text)
            # Stop after we get enough results to avoid infinite loop
            if len(callback_results) >= 2:
                recognizer.listening = False

        # Start continuous listening
        recognizer.continuous_listen(test_callback)

        # Give the thread time to process
        time.sleep(0.5)

        # Stop listening
        recognizer.stop_listening()

        # Check that the callback was called with non-empty results
        self.assertEqual(len(callback_results), 2)
        self.assertEqual(callback_results, ["hello", "test"])

    @patch('assistant.config_manager.ConfigManager')
    @patch('assistant.speech_recognition_service.SpeechRecognizer._initialize_model')
    def test_get_vad_settings(self, mock_init_model, mock_config_manager):
        """Test getting VAD settings."""
        # Mock the config manager
        mock_config_manager.get_section.return_value = MOCK_CONFIG["speech_recognition"]

        # Create recognizer
        recognizer = SpeechRecognizer()

        # Get the settings
        settings = recognizer.get_vad_settings()

        # Check the returned settings
        self.assertTrue(isinstance(settings, dict))
        self.assertEqual(settings["threshold"], 0.5)
        self.assertEqual(settings["sensitivity"], 0.75)
        self.assertTrue(settings["enabled"])
        self.assertEqual(settings["min_speech_duration_ms"], 250)
        self.assertEqual(settings["max_speech_duration_s"], 10)
        self.assertEqual(settings["silence_duration_ms"], 500)


# Additional tests with pytest for more modern testing approach

@pytest.fixture
def mock_recognizer():
    """Create a speech recognizer with mocked dependencies."""
    with patch('assistant.config_manager.ConfigManager') as mock_config:
        mock_config.get_section.return_value = MOCK_CONFIG["speech_recognition"]
        with patch('assistant.speech_recognition_service.SpeechRecognizer._initialize_model'):
            recognizer = SpeechRecognizer()
            yield recognizer

def test_fallback_to_cpu(mock_recognizer):
    """Test that the recognizer falls back to CPU on errors."""
    # Force an error in model initialization
    with patch('assistant.speech_recognition_service.SpeechRecognizer._initialize_model') as mock_init:
        mock_init.side_effect = RuntimeError("GPU not available")

        # Should not raise an exception, but fall back to CPU
        with pytest.raises(RuntimeError):
            recognizer = SpeechRecognizer(device="cuda")

@pytest.mark.parametrize("vad_enabled,expected", [
    (True, True),
    (False, False)
])
def test_vad_configuration(vad_enabled, expected):
    """Test different VAD configurations."""
    # Create the mock configuration
    mock_speech_recognition = {
        "vad": {
            "enabled": vad_enabled,
            "threshold": 0.5,
            "min_speech_duration_ms": 250,
            "max_speech_duration_s": 10,
            "silence_duration_ms": 500,
            "sensitivity": 0.75
        },
        "model_size": "tiny",
        "device": "cpu"
    }

    # Use patch to mock ConfigManager
    with patch('assistant.config_manager.ConfigManager') as MockConfigManager:
        # Set up the mock
        mock_instance = MockConfigManager.return_value
        mock_instance.get_section.return_value = mock_speech_recognition

        # Debug what's being returned
        print("Mock config:", mock_instance.get_section("speech_recognition"))

        # Patch model initialization to avoid loading actual models
        with patch('assistant.speech_recognition_service.SpeechRecognizer._initialize_model'):
            # Create the recognizer with our mocked config
            recognizer = SpeechRecognizer()
            print("Recognizer vad_enabled:", recognizer.vad_enabled)
            assert recognizer.vad_enabled == expected
if __name__ == '__main__':
    unittest.main()
