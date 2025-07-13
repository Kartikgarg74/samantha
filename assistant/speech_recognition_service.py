"""
Speech Recognition Service Module

This module provides speech-to-text functionality for the assistant,
supporting multiple recognition engines and language options.
"""

import os
import logging
import tempfile
import json
import time
import threading
import queue
from typing import Dict, Optional, List, Any, Union, Callable
from assistant.StatusIndicator import StatusIndicator
# Optional imports for various speech recognition engines
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Import config manager
from assistant.config_manager import config_manager


logger = logging.getLogger(__name__)


class SpeechRecognitionService:
    """
    Speech recognition service that supports multiple engines
    and language options.
    """

    # Available speech recognition engines
    ENGINES = {
        "google": "Google Speech Recognition",
        "whisper": "OpenAI Whisper",
        "sphinx": "CMU Sphinx (offline)",
        "vosk": "Vosk (offline)"
    }

    def __init__(self):
        """
        Initialize the speech recognition service.
        """
        # Load configuration
        self.config = config_manager.get_section("speech_recognition")
        self.engine_name = self.config.get("engine", "google")
        self.language = self.config.get("language", "en-US")
        self.energy_threshold = self.config.get("energy_threshold", 300)
        self.pause_threshold = self.config.get("pause_threshold", 0.8)
        self.timeout = self.config.get("timeout", 5)
        self.phrase_time_limit = self.config.get("phrase_time_limit", None)
        self.continuous_listen = self.config.get("continuous_listen", False)
        self.whisper_model_name = self.config.get("whisper_model", "base")

        # Internal state
        self._listening = False
        self._recognizer = None
        self._microphone = None
        self._whisper_model = None
        self._continuous_thread = None
        self._result_queue = queue.Queue()
        self._callbacks = []

        # Initialize recognizer
        self._initialize()

    def _initialize(self):
        """Initialize the speech recognition components."""
        if not SR_AVAILABLE:
            logger.error("speech_recognition library not available")
            raise ImportError("Please install the speech_recognition library")

        try:
            # Initialize recognizer
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = self.energy_threshold
            self._recognizer.pause_threshold = self.pause_threshold

            # Load Whisper model if selected
            if self.engine_name == "whisper" and WHISPER_AVAILABLE:
                self._load_whisper_model()

            logger.info(f"Initialized speech recognition with engine: {self.engine_name}")
        except Exception as e:
            logger.error(f"Failed to initialize speech recognition: {e}")
            raise

    def _load_whisper_model(self):
        """Load the OpenAI Whisper model."""
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper library not available, falling back to Google")
            self.engine_name = "google"
            return

        try:
            logger.info(f"Loading Whisper model: {self.whisper_model_name}")
            self._whisper_model = whisper.load_model(self.whisper_model_name)
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            self.engine_name = "google"

    def recognize_speech(self, audio_data=None, timeout=None) -> Dict[str, Any]:
        """
        Recognize speech from audio data or microphone input.

        Args:
            audio_data: Audio data to recognize, if None uses microphone
            timeout: Recognition timeout in seconds

        Returns:
            Dictionary with recognition results
        """
        if timeout is None:
            timeout = self.timeout

        result = {
            "success": False,
            "error": None,
            "text": "",
            "confidence": 0.0,
            "engine": self.engine_name
        }

        try:
            # Get audio from microphone if not provided
            if audio_data is None:
                audio_data = self._listen()
                if audio_data is None:
                    result["error"] = "No audio input received"
                    return result

            # Perform recognition based on selected engine
            if self.engine_name == "google":
                text = self._recognizer.recognize_google(
                    audio_data,
                    language=self.language,
                    show_all=False
                )
                result["text"] = text
                result["success"] = True
                result["confidence"] = 0.8  # Google doesn't provide confidence

            elif self.engine_name == "whisper" and self._whisper_model:
                # Save audio to temporary file for Whisper
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                    tmp_filename = tmp_file.name

                try:
                    # Convert audio data to WAV file
                    with open(tmp_filename, "wb") as f:
                        f.write(audio_data.get_wav_data())

                    # Process with Whisper
                    whisper_result = self._whisper_model.transcribe(tmp_filename)

                    result["text"] = whisper_result["text"]
                    result["success"] = True
                    result["confidence"] = whisper_result.get("confidence", 0.7)
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_filename):
                        os.remove(tmp_filename)

            elif self.engine_name == "sphinx":
                text = self._recognizer.recognize_sphinx(
                    audio_data,
                    language=self.language
                )
                result["text"] = text
                result["success"] = True
                result["confidence"] = 0.6  # Sphinx doesn't provide confidence

            else:
                result["error"] = f"Engine '{self.engine_name}' not supported or configured"

        except sr.UnknownValueError:
            result["error"] = "Could not understand audio"
        except sr.RequestError as e:
            result["error"] = f"Recognition request failed: {e}"
        except Exception as e:
            result["error"] = f"Recognition error: {e}"
            logger.error(f"Speech recognition error: {e}", exc_info=True)

        return result

    def _listen(self, timeout: Optional[int] = None):
        if timeout is None:
            timeout = config_manager.get('speech_recognition.timeout.default', 5)
        try:
            listening_thread = threading.Thread(target=StatusIndicator.show_listening, args=(timeout,))
            listening_thread.daemon = True
            listening_thread.start()
            # Initialize microphone if needed
            if self._microphone is None:
                self._microphone = sr.Microphone()

            with self._microphone as source:
                logger.debug("Adjusting for ambient noise")
                self._recognizer.adjust_for_ambient_noise(source, duration=1)

                logger.debug("Listening for speech")
                timeout = self.timeout
                if isinstance(timeout, dict):
                    logger.warning("Timeout was a dictionary, using default 5 seconds instead")
                    timeout = 5
                phrase_time_limit = self.phrase_time_limit
                if isinstance(phrase_time_limit, dict):
                    logger.warning("Phrase time limit was a dictionary, using None instead")
                    phrase_time_limit = None
                audio = self._recognizer.listen()
                return audio
            if audio is None:
                result = self.recognizer.recognize_speech(audio_data)
                text = result["text"] if result["success"] else ""
            else:""

        except sr.WaitTimeoutError:
            logger.warning("Listening timed out waiting for phrase to start")
            return None
        except Exception as e:
            logger.error(f"Error listening for speech: {e}", exc_info=True)
            return None

    def start_continuous_listening(self, callback: Callable[[Dict[str, Any]], None]) -> bool:
        """
        Start continuous listening in background thread.

        Args:
            callback: Function to call with recognition results

        Returns:
            True if started successfully, False otherwise
        """
        if self._listening:
            logger.warning("Continuous listening already active")
            return False

        self._callbacks.append(callback)
        self._listening = True

        # Start background thread
        self._continuous_thread = threading.Thread(
            target=self._continuous_listen_thread,
            daemon=True
        )
        self._continuous_thread.start()

        logger.info("Started continuous listening")
        return True

    def stop_continuous_listening(self) -> bool:
        """
        Stop continuous listening.

        Returns:
            True if stopped successfully, False otherwise
        """
        if not self._listening:
            logger.warning("Continuous listening not active")
            return False

        self._listening = False

        # Wait for thread to end
        if self._continuous_thread and self._continuous_thread.is_alive():
            self._continuous_thread.join(timeout=1.0)

        self._callbacks = []
        logger.info("Stopped continuous listening")
        return True

    def _continuous_listen_thread(self) -> None:
        """Background thread function for continuous listening."""
        logger.debug("Continuous listening thread started")

        while self._listening:
            try:
                # Listen for audio
                audio_data = self._listen()

                # If we got audio, recognize it
                if audio_data:
                    result = self.recognize_speech(audio_data)

                    # If successful and not empty, notify callbacks
                    if result["success"] and result["text"].strip():
                        for callback in self._callbacks:
                            try:
                                callback(result)
                            except Exception as e:
                                logger.error(f"Error in speech recognition callback: {e}")

            except Exception as e:
                logger.error(f"Error in continuous listening thread: {e}")

            # Short sleep to prevent CPU overuse on errors
            time.sleep(0.1)

        logger.debug("Continuous listening thread stopped")

    def set_engine(self, engine_name: str) -> bool:
        """
        Set the speech recognition engine.

        Args:
            engine_name: Name of the engine

        Returns:
            True if successful, False otherwise
        """
        if engine_name not in self.ENGINES:
            logger.warning(f"Unknown engine: {engine_name}")
            return False

        self.engine_name = engine_name

        # If switching to Whisper, load the model
        if engine_name == "whisper" and WHISPER_AVAILABLE and self._whisper_model is None:
            self._load_whisper_model()

        return True

    def set_language(self, language: str) -> None:
        """
        Set recognition language.

        Args:
            language: Language code (e.g., 'en-US', 'fr-FR')
        """
        self.language = language

    def set_energy_threshold(self, threshold: int) -> None:
        """
        Set energy threshold for detection.

        Args:
            threshold: Energy threshold value
        """
        self.energy_threshold = threshold
        if self._recognizer:
            self._recognizer.energy_threshold = threshold

    def set_pause_threshold(self, threshold: float) -> None:
        """
        Set pause threshold for detection.

        Args:
            threshold: Pause threshold value in seconds
        """
        self.pause_threshold = threshold
        if self._recognizer:
            self._recognizer.pause_threshold = threshold

    def get_available_engines(self) -> Dict[str, str]:
        """
        Get list of available speech recognition engines.

        Returns:
            Dictionary of available engines
        """
        available = {}

        # Check Google (requires internet)
        available["google"] = "Available"

        # Check Whisper
        if WHISPER_AVAILABLE:
            available["whisper"] = "Available"
        else:
            available["whisper"] = "Not installed"

        # Check Sphinx
        try:
            import pocketsphinx
            available["sphinx"] = "Available"
        except ImportError:
            available["sphinx"] = "Not installed"

        # Check Vosk
        try:
            import vosk
            available["vosk"] = "Available"
        except ImportError:
            available["vosk"] = "Not installed"

        return available

    def transcribe_file(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe speech from an audio file.

        Args:
            file_path: Path to audio file

        Returns:
            Dictionary with transcription results
        """
        result = {
            "success": False,
            "error": None,
            "text": "",
            "confidence": 0.0,
            "engine": self.engine_name
        }

        if not os.path.exists(file_path):
            result["error"] = f"File not found: {file_path}"
            return result

        try:
            if self.engine_name == "whisper" and self._whisper_model:
                # Use Whisper directly for file transcription
                whisper_result = self._whisper_model.transcribe(file_path)
                result["text"] = whisper_result["text"]
                result["success"] = True
                result["confidence"] = whisper_result.get("confidence", 0.7)
            else:
                # Use speech_recognition with file
                with sr.AudioFile(file_path) as source:
                    audio = self._recognizer.record(source)
                    # Use the regular recognition function
                    return self.recognize_speech(audio)

        except Exception as e:
            result["error"] = f"Transcription error: {e}"
            logger.error(f"Error transcribing file: {e}", exc_info=True)

        return result


# Create an instance for easy importing
speech_recognition_service = SpeechRecognitionService()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Example usage
    service = SpeechRecognitionService()

    # List available engines
    print("Available speech recognition engines:")
    available_engines = service.get_available_engines()
    for engine, status in available_engines.items():
        print(f" - {engine}: {status}")

    # Test speech recognition (if running directly)
    try:
        print("\nTesting speech recognition...")
        print("Please say something...")
        result = service.recognize_speech()

        if result["success"]:
            print(f"Recognized: {result['text']}")
        else:
            print(f"Recognition failed: {result['error']}")
    except Exception as e:
        print(f"Error testing speech recognition: {e}")
