"""
Speech recognition service with configurable VAD settings.
"""
import sounddevice as sd
import io
import wave
import tempfile
import time
import logging
from typing import Optional, Callable
import numpy as np
import threading
import torch

# Import the config manager
from assistant.config_manager import ConfigManager, config_manager

logger = logging.getLogger("SpeechRecognizer")

class SpeechRecognizer:
    """Speech recognizer with configurable VAD settings."""

    def __init__(self, model_size: str = None, device: str = None, vad_threshold: float = None, vad_sensitivity: float = None):
        """
        Initialize the speech recognizer.

        Args:
            model_size: Size of the model to use (tiny, base, small, medium, large)
            device: Device to use for inference (cpu, cuda, mps)
            vad_threshold: Voice activity detection threshold
            vad_sensitivity: Voice activity detection sensitivity
        """
        # Get config values, with function parameters taking precedence


        cfg = config_manager.get_section('speech_recognition')
        self.model_size = model_size or cfg.get('model_size', 'tiny')
        self.device = device or cfg.get('device', 'cpu')
        cfg_manager = ConfigManager()
        vad_cfg = cfg.get('vad', {})
        self.vad_enabled = vad_cfg.get("enabled", True)
        self.vad_threshold = vad_threshold or vad_cfg.get('threshold', 0.5)
        self.vad_sensitivity = vad_sensitivity or vad_cfg.get('sensitivity', 0.75)
        self.min_speech_duration_ms = vad_cfg.get('min_speech_duration_ms', 250)
        self.max_speech_duration_s = vad_cfg.get('max_speech_duration_s', 15)
        self.silence_duration_ms = vad_cfg.get('silence_duration_ms', 500)
        # Add these lines to your SpeechRecognizer __init__ method
        print("VAD config:", vad_cfg)
        print("VAD enabled setting:", vad_cfg.get('enabled', True))

        # Initialize the model
        self._initialize_model()

        # State variables
        self.listening = False
        self.continuous_thread = None

    def _initialize_model(self):
        """Initialize the speech recognition model."""
        try:
            # This is just a placeholder. In practice, you would load your
            # speech recognition model here (e.g., Faster Whisper)
            logger.info(f"Initializing speech recognition model (size={self.model_size}, device={self.device})")

            # Example: load Faster Whisper model
            try:
                from faster_whisper import WhisperModel
                self.model = WhisperModel(self.model_size, device=self.device)
                logger.info("Using Faster Whisper model for speech recognition")
            except ImportError:
                logger.warning("Faster Whisper not available, trying to use regular Whisper")
                try:
                    import whisper
                    self.model = whisper.load_model(self.model_size, device=self.device)
                    logger.info("Using OpenAI Whisper model for speech recognition")
                except ImportError:
                    logger.error("No speech recognition model available")
                    self.model = None

            # Initialize VAD if enabled
            if self.vad_enabled:
                try:
                    import torch
                    from speechbrain.pretrained import VAD
                    self.vad_model = VAD.from_hparams(source="speechbrain/vad-crdnn-libriparty")
                    logger.info("VAD model loaded successfully")
                except Exception as e:
                    logger.warning(f"Could not initialize VAD model: {e}")
                    self.vad_enabled = False

            logger.info("Speech recognition model initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing speech recognition model: {e}")
            # Fall back to smallest model on CPU if there's an error
            self.model_size = "tiny"
            self.device = "cpu"

            # Try again with fallback settings
            try:
                from faster_whisper import WhisperModel
                self.model = WhisperModel(self.model_size, device=self.device)
                logger.info("Using fallback Faster Whisper model")
            except Exception as e2:
                logger.error(f"Failed to initialize fallback model: {e2}")
                raise RuntimeError("Could not initialize speech recognition")

    def listen(self, timeout: int = 5) -> str:
        """
        Listen for speech and convert to text.

        Args:
            timeout: Maximum time to listen for in seconds

        Returns:
            Transcribed text
        """
        try:
            logger.debug(f"Listening for {timeout}s with VAD (threshold={self.vad_threshold}, sensitivity={self.vad_sensitivity})")

            # Sample rate and other parameters
            samplerate = 16000
            channels = 1

            # Record audio
            logger.debug(f"Recording audio for up to {timeout} seconds")
            audio_data = sd.rec(
                int(samplerate * timeout),
                samplerate=samplerate,
                channels=channels,
                dtype='int16'
            )

            # Wait for recording to finish or for speech to be detected
            start_time = time.time()
            speech_detected = False
            silence_counter = 0

            while time.time() - start_time < timeout:
                sd.wait()

                # If VAD is enabled, check if speech is present
                if self.vad_enabled and hasattr(self, 'vad_model'):
                    # Process the audio chunk
                    # This is simplified - in a real implementation,
                    # you'd process the audio in chunks during recording
                    try:
                        speech_prob = self.vad_model.get_speech_prob(torch.from_numpy(audio_data[:int((time.time() - start_time) * samplerate)].flatten()))
                        is_speech = speech_prob.mean() > self.vad_threshold

                        if is_speech:
                            speech_detected = True
                            silence_counter = 0
                        else:
                            silence_counter += 1

                        # If we've detected speech and then silence, stop recording
                        if speech_detected and silence_counter > int(self.silence_duration_ms * samplerate / 1000):
                            logger.debug("Speech followed by silence detected, stopping recording")
                            break

                    except Exception as e:
                        logger.warning(f"Error in VAD processing: {e}")

                # Small sleep to reduce CPU usage
                time.sleep(0.1)

            # If no speech detected or VAD not enabled, just use the full recording
            if not speech_detected and not self.vad_enabled:
                logger.debug("No VAD used or no speech detected, using full recording")

            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                audio_file = temp_audio.name
                with wave.open(audio_file, 'wb') as wf:
                    wf.setnchannels(channels)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(samplerate)
                    wf.writeframes(audio_data.tobytes())

            # Transcribe the audio
            if hasattr(self, 'model') and self.model:
                if hasattr(self.model, 'transcribe'):  # OpenAI Whisper
                    result = self.model.transcribe(audio_file)
                    text = result["text"].strip()
                else:  # Faster Whisper
                    segments, _ = self.model.transcribe(audio_file)
                    text = " ".join([segment.text for segment in segments]).strip()

                logger.info(f"Transcribed: '{text}'")
                return text
            else:
                logger.warning("No model available for transcription")
                return ""

        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
            return ""
        finally:
            # Clean up any temporary files
            try:
                import os
                if 'audio_file' in locals() and os.path.exists(audio_file):
                    os.unlink(audio_file)
            except:
                pass

    def continuous_listen(self, callback: Callable[[str], None]) -> None:
        """
        Start continuous listening mode.

        Args:
            callback: Function to call with transcribed text
        """
        if self.continuous_thread and self.continuous_thread.is_alive():
            logger.warning("Continuous listening already active")
            return

        self.listening = True

        def listen_thread():
            logger.info("Starting continuous listening thread")
            while self.listening:
                text = self.listen(timeout=2)  # Shorter timeout for responsiveness
                if text and callable(callback):
                    callback(text)

        self.continuous_thread = threading.Thread(target=listen_thread)
        self.continuous_thread.daemon = True
        self.continuous_thread.start()

    def stop_listening(self) -> None:
        """Stop listening."""
        logger.info("Stopping listening")
        self.listening = False
        if self.continuous_thread:
            if self.continuous_thread.is_alive():
                # Give the thread time to finish
                self.continuous_thread.join(timeout=1)
            self.continuous_thread = None

    def update_vad_settings(self, threshold: Optional[float] = None, sensitivity: Optional[float] = None) -> None:
        """
        Update VAD settings.

        Args:
            threshold: New threshold value (0-1)
            sensitivity: New sensitivity value (0-1)
        """
        if threshold is not None:
            self.vad_threshold = max(0.0, min(1.0, threshold))
            logger.debug(f"VAD threshold updated to {self.vad_threshold}")

        if sensitivity is not None:
            self.vad_sensitivity = max(0.0, min(1.0, sensitivity))
            logger.debug(f"VAD sensitivity updated to {self.vad_sensitivity}")

    def get_vad_settings(self) -> dict:
        """
        Get current VAD settings.

        Returns:
            Dictionary with current VAD settings
        """
        return {
            "enabled": self.vad_enabled,
            "threshold": self.vad_threshold,
            "sensitivity": self.vad_sensitivity,
            "min_speech_duration_ms": self.min_speech_duration_ms,
            "max_speech_duration_s": self.max_speech_duration_s,
            "silence_duration_ms": self.silence_duration_ms
        }
