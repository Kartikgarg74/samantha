"""
Text-to-Speech Service Module

This module provides text-to-speech capabilities for the assistant,
supporting multiple engines and voice customization.
"""

import os
import logging
import tempfile
import wave
import numpy as np
from typing import Dict, Optional, List, Union, Any

# Optional imports for various TTS engines
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Import config manager
from assistant.config_manager import config_manager


logger = logging.getLogger(__name__)


class TTSService:
    """
    Text-to-Speech Service that supports multiple engines
    and voice customization options.
    """

    # Available TTS engines
    ENGINES = {
        "pyttsx3": "Local TTS using pyttsx3",
        "gtts": "Google Text-to-Speech API",
        "silero": "Silero TTS model"
    }

    def __init__(self):
        """
        Initialize the TTS service with the specified engine.
        """
        # Load configuration
        tts_config = config_manager.get_section("tts")
        self.engine_name = tts_config.get("engine", "pyttsx3")
        self.voice_id = tts_config.get("voice_id")
        self.language = tts_config.get("language", "en")
        self.rate = tts_config.get("rate", 150)
        self.volume = tts_config.get("volume", 1.0)
        self.pitch = tts_config.get("pitch", 1.0)

        # Check if the configured engine is available
        if self.engine_name == "pyttsx3" and not PYTTSX3_AVAILABLE:
            logger.warning("pyttsx3 not available, falling back to gTTS")
            self.engine_name = "gtts" if GTTS_AVAILABLE else None
        elif self.engine_name == "gtts" and not GTTS_AVAILABLE:
            logger.warning("gTTS not available, falling back to pyttsx3")
            self.engine_name = "pyttsx3" if PYTTSX3_AVAILABLE else None
        elif self.engine_name == "silero" and not TORCH_AVAILABLE:
            logger.warning("Torch not available for Silero, falling back to another engine")
            if PYTTSX3_AVAILABLE:
                self.engine_name = "pyttsx3"
            elif GTTS_AVAILABLE:
                self.engine_name = "gtts"
            else:
                self.engine_name = None

        # Initialize the selected engine
        self._engine = None
        self._silero_model = None
        if self.engine_name:
            self._initialize_engine()
        else:
            logger.error("No TTS engine available")
            raise RuntimeError("No TTS engine available. Please install pyttsx3 or gTTS.")

    def _initialize_engine(self):
        """Initialize the selected TTS engine."""
        if self.engine_name == "pyttsx3":
            self._initialize_pyttsx3()
        elif self.engine_name == "gtts":
            # gTTS doesn't need initialization, it's used on-demand
            pass
        elif self.engine_name == "silero":
            self._initialize_silero()

    def _initialize_pyttsx3(self):
        """Initialize the pyttsx3 engine."""
        if not PYTTSX3_AVAILABLE:
            raise RuntimeError("pyttsx3 is not installed")

        self._engine = pyttsx3.init()
        self._engine.setProperty('rate', self.rate)
        self._engine.setProperty('volume', self.volume)

        # Set voice if specified
        if self.voice_id:
            self._engine.setProperty('voice', self.voice_id)

    def _initialize_silero(self):
        """Initialize the Silero TTS model."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("torch is not installed")

        # Import here to avoid dependency if not using Silero
        try:
            torch.hub._validate_not_a_forked_repo = lambda a, b, c: True  # Bypass Torch Hub validation
            self._silero_model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language=self.language,
                speaker="v3_en"  # Default English speaker
            )
            self._silero_model.to('cpu')  # Use CPU by default
        except Exception as e:
            logger.error(f"Failed to load Silero model: {e}")
            raise RuntimeError(f"Failed to load Silero model: {e}")

    def speak(self, text: str) -> None:
        """
        Convert text to speech and play it.

        Args:
            text: Text to convert to speech
        """
        if not text:
            return

        try:
            if self.engine_name == "pyttsx3":
                self._speak_pyttsx3(text)
            elif self.engine_name == "gtts":
                self._speak_gtts(text)
            elif self.engine_name == "silero":
                self._speak_silero(text)
        except Exception as e:
            logger.error(f"TTS error: {e}")

    def _speak_pyttsx3(self, text: str) -> None:
        """Use pyttsx3 for TTS."""
        if not self._engine:
            self._initialize_pyttsx3()
        self._engine.say(text)
        self._engine.runAndWait()

    def _speak_gtts(self, text: str) -> None:
        """Use Google Text-to-Speech for TTS."""
        if not GTTS_AVAILABLE:
            raise RuntimeError("gTTS is not installed")

        # Create a temporary file to store the speech
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Generate speech
            tts = gTTS(text=text, lang=self.language)
            tts.save(temp_filename)

            # Play the generated speech
            os.system(f"afplay {temp_filename}")  # macOS
            # For other platforms, use appropriate commands:
            # os.system(f"start {temp_filename}")  # Windows
            # os.system(f"mpg123 {temp_filename}")  # Linux
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def _speak_silero(self, text: str) -> None:
        """Use Silero TTS model."""
        if not self._silero_model:
            self._initialize_silero()

        # Generate audio
        sample_rate = 48000
        audio = self._silero_model.apply_tts(
            text=text,
            speaker=f"v3_{self.language}",
            sample_rate=sample_rate
        )

        # Convert to numpy array
        audio_np = audio.numpy()

        # Save as WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Normalize audio data to -1 to 1 range
            max_val = np.max(np.abs(audio_np))
            if max_val > 0:
                audio_np = audio_np / max_val

            # Convert to 16-bit PCM
            audio_16bit = (audio_np * 32767).astype(np.int16)

            # Save as WAV
            with wave.open(temp_filename, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_16bit.tobytes())

            # Play the audio
            os.system(f"afplay {temp_filename}")  # macOS
            # For other platforms:
            # os.system(f"start {temp_filename}")  # Windows
            # os.system(f"aplay {temp_filename}")  # Linux
        finally:
            # Clean up
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def set_voice(self, voice_id: str) -> None:
        """
        Set the voice to use for speech.

        Args:
            voice_id: ID of the voice to use
        """
        self.voice_id = voice_id
        if self.engine_name == "pyttsx3" and self._engine:
            self._engine.setProperty('voice', voice_id)

    def set_rate(self, rate: int) -> None:
        """
        Set the speech rate.

        Args:
            rate: Speech rate (words per minute)
        """
        self.rate = rate
        if self.engine_name == "pyttsx3" and self._engine:
            self._engine.setProperty('rate', rate)

    def set_volume(self, volume: float) -> None:
        """
        Set the speech volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
        if self.engine_name == "pyttsx3" and self._engine:
            self._engine.setProperty('volume', self.volume)

    def get_available_voices(self) -> List[Dict[str, str]]:
        """
        Get a list of available voices.

        Returns:
            List of voice information dictionaries
        """
        voices = []
        if self.engine_name == "pyttsx3" and self._engine:
            for voice in self._engine.getProperty('voices'):
                voices.append({
                    'id': voice.id,
                    'name': voice.name,
                    'gender': getattr(voice, 'gender', 'unknown'),
                    'age': getattr(voice, 'age', 'unknown'),
                    'language': getattr(voice, 'languages', ['unknown'])[0]
                })
        elif self.engine_name == "silero":
            voices = [
                {'id': 'v3_en', 'name': 'English', 'language': 'en'},
                {'id': 'v3_de', 'name': 'German', 'language': 'de'},
                {'id': 'v3_es', 'name': 'Spanish', 'language': 'es'},
                {'id': 'v3_fr', 'name': 'French', 'language': 'fr'},
                {'id': 'v3_ru', 'name': 'Russian', 'language': 'ru'}
            ]
        return voices

    def text_to_audio_file(self, text: str, filename: str) -> bool:
        """
        Convert text to speech and save it to a file.

        Args:
            text: Text to convert
            filename: Output file path

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.engine_name == "gtts":
                tts = gTTS(text=text, lang=self.language)
                tts.save(filename)
                return True
            elif self.engine_name == "silero" and self._silero_model:
                # Generate audio
                sample_rate = 48000
                audio = self._silero_model.apply_tts(
                    text=text,
                    speaker=f"v3_{self.language}",
                    sample_rate=sample_rate
                )

                # Convert to numpy array
                audio_np = audio.numpy()

                # Normalize audio data
                max_val = np.max(np.abs(audio_np))
                if max_val > 0:
                    audio_np = audio_np / max_val

                # Convert to 16-bit PCM
                audio_16bit = (audio_np * 32767).astype(np.int16)

                # Save as WAV
                with wave.open(filename, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_16bit.tobytes())
                return True
            else:
                logger.warning(f"Saving audio not supported with {self.engine_name}")
                return False
        except Exception as e:
            logger.error(f"Failed to save audio to file: {e}")
            return False

    def set_language(self, language: str) -> None:
        """
        Set the language for speech.

        Args:
            language: Language code (e.g., 'en', 'fr')
        """
        self.language = language
        # Note: For pyttsx3, language is tied to voice selection


# Create an instance for easy importing
tts_service = TTSService()


if __name__ == "__main__":
    # Example usage
    tts = TTSService()
    tts.speak("Hello! I am Samantha, your voice assistant. How can I help you today?")

    # List available voices
    voices = tts.get_available_voices()
    print(f"Available voices: {voices}")
