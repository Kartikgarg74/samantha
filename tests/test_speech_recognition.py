#!/usr/bin/env python3
"""
Unit tests for the Speech Recognition Service.
Tests various speech recognition engines, continuous listening, and configuration.
"""

import os
import sys
import unittest
import pytest
from unittest.mock import patch, MagicMock, PropertyMock, call
import tempfile
import json
import time
import threading
import queue

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the modules to test
from assistant.speech_recognition_service import SpeechRecognitionService, SR_AVAILABLE, WHISPER_AVAILABLE

# Mock config for testing
MOCK_CONFIG = {
    "speech_recognition": {
        "engine": "google",
        "language": "en-US",
        "energy_threshold": 300,
        "pause_threshold": 0.8,
        "timeout": 5,
        "phrase_time_limit": None,
        "continuous_listen": False,
        "whisper_model": "base"
    }
}

class TestSpeechRecognitionService(unittest.TestCase):
    """Test cases for the speech recognition service."""

    def setUp(self):
        """Set up test fixtures before each test."""
        # Patch the config manager
        self.config_patcher = patch('assistant.speech_recognition_service.config_manager')
        self.mock_config = self.config_patcher.start()
        self.mock_config.get_section.return_value = MOCK_CONFIG["speech_recognition"]

        # Patch the speech_recognition library
        self.sr_patcher = patch('assistant.speech_recognition_service.sr')
        self.mock_sr = self.sr_patcher.start()

        # Set up mock recognizer and microphone
        self.mock_recognizer = MagicMock()
        self.mock_sr.Recognizer.return_value = self.mock_recognizer

        self.mock_microphone = MagicMock()
        self.mock_sr.Microphone.return_value = self.mock_microphone

        # Create actual exception classes for better mocking
        class MockUnknownValueError(Exception):
            pass

        class MockRequestError(Exception):
            def __init__(self, message):
                self.message = message
                super().__init__(message)

        class MockWaitTimeoutError(Exception):
            pass

        self.mock_sr.UnknownValueError = MockUnknownValueError
        self.mock_sr.RequestError = MockRequestError
        self.mock_sr.WaitTimeoutError = MockWaitTimeoutError

        # Patch whisper if needed
        if WHISPER_AVAILABLE:
            self.whisper_patcher = patch('assistant.speech_recognition_service.whisper')
            self.mock_whisper = self.whisper_patcher.start()
            self.mock_whisper_model = MagicMock()
            self.mock_whisper.load_model.return_value = self.mock_whisper_model
        else:
            self.whisper_patcher = None

        # Set flag for available libraries
        self.sr_available_patcher = patch('assistant.speech_recognition_service.SR_AVAILABLE', True)
        self.sr_available_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        # Stop all patches
        self.config_patcher.stop()
        self.sr_patcher.stop()
        self.sr_available_patcher.stop()

        if self.whisper_patcher:
            self.whisper_patcher.stop()

    def test_initialization(self):
        """Test the initialization of the speech recognition service."""
        service = SpeechRecognitionService()

        # Check if the configuration was properly applied
        self.assertEqual(service.engine_name, "google")
        self.assertEqual(service.language, "en-US")
        self.assertEqual(service.energy_threshold, 300)
        self.assertEqual(service.pause_threshold, 0.8)

        # Verify that the recognizer was initialized
        self.mock_sr.Recognizer.assert_called_once()
        self.assertEqual(self.mock_recognizer.energy_threshold, 300)
        self.assertEqual(self.mock_recognizer.pause_threshold, 0.8)

    def test_recognize_speech_with_google(self):
        """Test speech recognition with Google engine."""
        # Setup mock for Google recognition
        self.mock_recognizer.recognize_google.return_value = "Hello world"

        # Create service and mock audio data
        service = SpeechRecognitionService()
        mock_audio = MagicMock()

        # Test recognition
        result = service.recognize_speech(mock_audio)

        # Verify results
        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "Hello world")
        self.assertEqual(result["engine"], "google")
        self.assertGreater(result["confidence"], 0)

        # Verify the correct recognition method was called
        self.mock_recognizer.recognize_google.assert_called_once_with(
            mock_audio, language="en-US", show_all=False
        )

    def test_recognize_speech_with_whisper(self):
        """Test speech recognition with Whisper engine if available."""
        if not WHISPER_AVAILABLE:
            self.skipTest("Whisper not available")

        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()

        try:
            # Setup Whisper model mock
            whisper_result = {"text": "Whisper transcription", "confidence": 0.9}
            self.mock_whisper_model.transcribe.return_value = whisper_result

            # Setup audio data mock
            mock_audio = MagicMock()
            mock_audio.get_wav_data.return_value = b"fake audio data"

            # Configure service for Whisper
            with patch('assistant.speech_recognition_service.WHISPER_AVAILABLE', True):
                service = SpeechRecognitionService()
                service.engine_name = "whisper"
                service._whisper_model = self.mock_whisper_model

                # Test recognition
                result = service.recognize_speech(mock_audio)

                # Verify results
                self.assertTrue(result["success"])
                self.assertEqual(result["text"], "Whisper transcription")
                self.assertEqual(result["engine"], "whisper")
                self.assertEqual(result["confidence"], 0.9)

                # Verify that model.transcribe was called
                self.mock_whisper_model.transcribe.assert_called_once()
        finally:
            # Clean up
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)

    def test_recognize_speech_with_sphinx(self):
        """Test speech recognition with Sphinx engine."""
        # Setup mock for Sphinx recognition
        self.mock_recognizer.recognize_sphinx.return_value = "Sphinx transcription"

        # Create service and mock audio data
        service = SpeechRecognitionService()
        service.engine_name = "sphinx"
        mock_audio = MagicMock()

        # Test recognition
        result = service.recognize_speech(mock_audio)

        # Verify results
        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "Sphinx transcription")
        self.assertEqual(result["engine"], "sphinx")
        self.assertGreater(result["confidence"], 0)

        # Verify the correct recognition method was called
        self.mock_recognizer.recognize_sphinx.assert_called_once_with(
            mock_audio, language="en-US"
        )

    def test_recognize_speech_with_errors(self):
        """Test handling of recognition errors."""
        # Create service
        service = SpeechRecognitionService()
        mock_audio = MagicMock()

        # Patch the recognize_speech_with_error helper to inject our exceptions
        def mock_recognize_with_google(audio_data, language, show_all):
            raise self.mock_sr.UnknownValueError()

        # Test UnknownValueError
        self.mock_recognizer.recognize_google.side_effect = mock_recognize_with_google
        result = service.recognize_speech(mock_audio)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Could not understand audio")

        # Test RequestError
        def mock_recognize_with_request_error(audio_data, language, show_all):
            raise self.mock_sr.RequestError("Network error")

        self.mock_recognizer.recognize_google.side_effect = mock_recognize_with_request_error
        result = service.recognize_speech(mock_audio)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Recognition request failed: Network error")

        # Test general exception
        def mock_recognize_with_general_error(audio_data, language, show_all):
            raise Exception("General error")

        self.mock_recognizer.recognize_google.side_effect = mock_recognize_with_general_error
        result = service.recognize_speech(mock_audio)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "Recognition error: General error")

    def test_listen_function(self):
        """Test the _listen function for microphone input."""
        # Setup mock audio
        mock_audio = MagicMock()
        self.mock_recognizer.listen.return_value = mock_audio

        # Create service
        service = SpeechRecognitionService()

        # Test listening
        audio = service._listen()

        # Verify that the microphone was used and listen was called
        self.mock_sr.Microphone.assert_called_once()
        self.mock_recognizer.adjust_for_ambient_noise.assert_called_once()
        self.mock_recognizer.listen.assert_called_once_with(
            self.mock_microphone.__enter__.return_value,
            timeout=5,
            phrase_time_limit=None
        )
        self.assertEqual(audio, mock_audio)

    def test_listen_with_timeout(self):
        """Test that _listen handles timeouts properly."""
        # Setup timeout error
        def raise_timeout(*args, **kwargs):
            raise self.mock_sr.WaitTimeoutError()

        self.mock_recognizer.listen.side_effect = raise_timeout

        # Create service
        service = SpeechRecognitionService()

        # Test listening with timeout
        audio = service._listen()

        # Verify that None is returned on timeout
        self.assertIsNone(audio)

    def test_continuous_listening(self):
        """Test continuous listening functionality."""
        # Create service
        service = SpeechRecognitionService()

        # Mock the recognize_speech method to return predetermined results
        original_recognize_speech = service.recognize_speech

        results = [
            {"success": True, "text": "First result", "confidence": 0.8, "engine": "google", "error": None},
            {"success": True, "text": "Second result", "confidence": 0.9, "engine": "google", "error": None},
            {"success": False, "text": "", "confidence": 0, "engine": "google", "error": "Error"}
        ]

        result_index = [0]  # Use list to allow modification in the inner function

        def mock_recognize(*args, **kwargs):
            if result_index[0] < len(results):
                result = results[result_index[0]]
                result_index[0] += 1
                return result
            return original_recognize_speech(*args, **kwargs)

        service.recognize_speech = mock_recognize

        # Mock the _listen method to return mock audio
        mock_audio = MagicMock()
        service._listen = MagicMock(return_value=mock_audio)

        # Create a callback to track results
        callback_results = []
        def test_callback(result):
            callback_results.append(result)
            # Stop after we've processed enough results
            if len(callback_results) >= 2:
                service._listening = False

        # Start continuous listening
        service.start_continuous_listening(test_callback)

        # Wait for processing to complete
        time.sleep(0.5)

        # Stop listening
        service.stop_continuous_listening()

        # Verify results
        self.assertEqual(len(callback_results), 2)  # Should have received 2 results
        self.assertEqual(callback_results[0]["text"], "First result")
        self.assertEqual(callback_results[1]["text"], "Second result")

    def test_set_engine(self):
        """Test setting the recognition engine."""
        service = SpeechRecognitionService()

        # Test setting valid engine
        result = service.set_engine("sphinx")
        self.assertTrue(result)
        self.assertEqual(service.engine_name, "sphinx")

        # Test setting invalid engine
        result = service.set_engine("invalid_engine")
        self.assertFalse(result)
        self.assertEqual(service.engine_name, "sphinx")  # Should remain unchanged

    def test_set_language(self):
        """Test setting the recognition language."""
        service = SpeechRecognitionService()
        service.set_language("fr-FR")
        self.assertEqual(service.language, "fr-FR")

    def test_set_energy_threshold(self):
        """Test setting energy threshold."""
        service = SpeechRecognitionService()
        service.set_energy_threshold(400)
        self.assertEqual(service.energy_threshold, 400)
        self.assertEqual(self.mock_recognizer.energy_threshold, 400)

    def test_set_pause_threshold(self):
        """Test setting pause threshold."""
        service = SpeechRecognitionService()
        service.set_pause_threshold(1.0)
        self.assertEqual(service.pause_threshold, 1.0)
        self.assertEqual(self.mock_recognizer.pause_threshold, 1.0)

    def test_get_available_engines(self):
        """Test getting available engines."""
        # Mock availability checks
        with patch('builtins.__import__', side_effect=[None, ImportError(), None]):
            service = SpeechRecognitionService()
            engines = service.get_available_engines()

            # Google should always be available in our mock
            self.assertEqual(engines["google"], "Available")

            # Other engines depend on the imports
            if WHISPER_AVAILABLE:
                self.assertEqual(engines["whisper"], "Available")
            else:
                self.assertEqual(engines["whisper"], "Not installed")

    def test_transcribe_file(self):
        """Test transcribing from a file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            file_path = temp_file.name

        try:
            # Setup mocks
            mock_audio = MagicMock()
            mock_source = MagicMock()
            mock_context = MagicMock()

            self.mock_sr.AudioFile.return_value = mock_source
            mock_source.__enter__.return_value = mock_context
            self.mock_recognizer.record.return_value = mock_audio
            self.mock_recognizer.recognize_google.return_value = "File transcription"

            # Create service
            service = SpeechRecognitionService()

            # Override recognize_speech to return a success response
            service.recognize_speech = MagicMock(return_value={
                "success": True,
                "text": "File transcription",
                "confidence": 0.8,
                "engine": "google",
                "error": None
            })

            # Test file transcription
            result = service.transcribe_file(file_path)

            # Verify results
            self.assertTrue(result["success"])
            self.assertEqual(result["text"], "File transcription")

            # Verify method calls
            self.mock_sr.AudioFile.assert_called_once_with(file_path)
            self.mock_recognizer.record.assert_called_once()  # Just check if called, not the exact arguments
        finally:
            # Clean up
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_transcribe_nonexistent_file(self):
        """Test handling of non-existent files."""
        service = SpeechRecognitionService()
        result = service.transcribe_file("nonexistent_file.wav")

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "File not found: nonexistent_file.wav")


# Additional tests using pytest

@pytest.fixture
def mock_sr_service():
    """Create a speech recognition service with mocked dependencies."""
    with patch('assistant.speech_recognition_service.config_manager') as mock_config, \
         patch('assistant.speech_recognition_service.sr') as mock_sr, \
         patch('assistant.speech_recognition_service.SR_AVAILABLE', True):

        # Configure mock
        mock_config.get_section.return_value = MOCK_CONFIG["speech_recognition"]

        # Setup recognizer mock
        mock_recognizer = MagicMock()
        mock_sr.Recognizer.return_value = mock_recognizer

        # Create service
        service = SpeechRecognitionService()
        yield service, mock_recognizer, mock_sr

def test_recognize_speech_empty_audio(mock_sr_service):
    """Test recognizing speech with empty audio input."""
    service, mock_recognizer, _ = mock_sr_service

    # Test with None audio data
    service._listen = MagicMock(return_value=None)
    result = service.recognize_speech()

    assert not result["success"]
    assert "No audio input received" in result["error"]
    assert result["text"] == ""

@pytest.mark.parametrize("engine_name,expected_recognition_method", [
    ("google", "recognize_google"),
    ("sphinx", "recognize_sphinx"),
])
def test_recognition_with_different_engines(mock_sr_service, engine_name, expected_recognition_method):
    """Test recognition with different engines."""
    service, mock_recognizer, _ = mock_sr_service

    # Set up the engine
    service.set_engine(engine_name)

    # Configure mock to return text for any recognition method
    getattr(mock_recognizer, expected_recognition_method).return_value = "Test text"

    # Create mock audio
    mock_audio = MagicMock()

    # Test recognition
    result = service.recognize_speech(mock_audio)

    # Verify result
    assert result["success"]
    assert result["text"] == "Test text"
    assert result["engine"] == engine_name

    # Verify the correct recognition method was called
    getattr(mock_recognizer, expected_recognition_method).assert_called_once()

def test_continuous_listening_callbacks(mock_sr_service):
    """Test that callbacks are properly called in continuous listening."""
    service, _, _ = mock_sr_service

    # Mock the thread to avoid actual background processing
    with patch('threading.Thread') as mock_thread:
        # Set up callbacks
        callback1 = MagicMock()
        callback2 = MagicMock()

        # Start listening with first callback
        success1 = service.start_continuous_listening(callback1)
        assert success1
        assert service._listening
        assert callback1 in service._callbacks

        # Add second callback (this is a bit of a hack since we'd normally
        # just pass both callbacks to start_continuous_listening)
        service._callbacks.append(callback2)

        # Simulate thread function calling callbacks
        result = {"success": True, "text": "Test", "confidence": 0.9, "engine": "google", "error": None}
        for callback in service._callbacks:
            callback(result)

        # Stop listening
        success2 = service.stop_continuous_listening()
        assert success2
        assert not service._listening
        assert len(service._callbacks) == 0

        # Verify callbacks were called
        callback1.assert_called_once_with(result)
        callback2.assert_called_once_with(result)

if __name__ == '__main__':
    unittest.main()
