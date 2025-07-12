"""
Speech recognition implementation for Samantha Voice Assistant using Faster-Whisper.
Optimized for macOS with CPU inference.
"""

import os
import time
import threading
from datetime import datetime
import tempfile
import subprocess
import numpy as np

# Install required packages if not present
try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Installing faster-whisper...")
    subprocess.check_call(["pip", "install", "faster-whisper"])
    from faster_whisper import WhisperModel

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    print("Installing audio dependencies...")
    subprocess.check_call(["pip", "install", "sounddevice", "soundfile"])
    import sounddevice as sd
    import soundfile as sf

class SpeechRecognizer:
    def __init__(self, model_size="tiny", device="cpu", compute_type="int8", sample_rate=16000):
        """
        Initialize speech recognition with Faster-Whisper

        Args:
            model_size (str): Size of Whisper model ('tiny', 'base', 'small', 'medium', 'large')
            device (str): Device to use ('cpu', 'cuda', or 'mps' for Mac)
            compute_type (str): Compute type ('float16', 'int8', 'int8_float16')
            sample_rate (int): Audio sample rate in Hz
        """
        # Force CPU usage regardless of what's requested to avoid MPS issues
        if device != "cuda":  # Only keep cuda if explicitly requested
            device = "cpu"
            print("Using CPU for model inference (safer option)")

        print(f"Loading Faster-Whisper {model_size} model on {device}...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("Model loaded successfully!")

        self.sample_rate = sample_rate
        self.is_listening = False
        self.stream = None
        self.listen_thread = None
        self.callback = None
        self.audio_data = None
        self.audio_timeout = 5  # Default timeout in seconds
        self.result_text = None

    def start_listening(self, callback=None, timeout=5):
        """
        Start listening for speech in a background thread

        Args:
            callback (function): Function to call with recognized text
            timeout (int): Maximum time to wait for speech in seconds
        """
        if self.is_listening:
            return False

        self.is_listening = True
        self.callback = callback
        self.audio_timeout = timeout
        self.audio_data = np.array([], dtype=np.float32)

        # Start listening in a separate thread
        self.listen_thread = threading.Thread(target=self._listen_loop)
        self.listen_thread.daemon = True
        self.listen_thread.start()

        return True

    def stop_listening(self):
        """Stop the listening process"""
        if not self.is_listening:
            return False

        self.is_listening = False
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1.0)

        return True

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice to collect audio data"""
        if status:
            print(f"Audio callback status: {status}")

        if not self.is_listening:
            return

        # Append to our audio data (converting to float32 and normalizing)
        self.audio_data = np.append(self.audio_data, indata.flatten())

    def _listen_loop(self):
        """Background thread for continuous listening"""
        try:
            # Set up audio stream
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                callback=self._audio_callback
            )

            self.stream.start()

            # Wait for the specified timeout
            start_time = time.time()
            while self.is_listening and time.time() - start_time < self.audio_timeout:
                time.sleep(0.1)

            # Stop streaming
            self.stream.stop()
            self.stream.close()
            self.stream = None

            if len(self.audio_data) > 0:
                # Save audio to a temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_filename = temp_file.name
                    sf.write(temp_filename, self.audio_data, self.sample_rate)

                try:
                    # Transcribe the audio
                    segments, _ = self.model.transcribe(temp_filename, language="en", beam_size=1)
                    text = " ".join([segment.text for segment in segments]).strip()

                    # Call the callback with the recognized text
                    if text and self.callback:
                        self.callback(text)
                    elif text:
                        self.result_text = text
                finally:
                    # Clean up the temporary file
                    os.unlink(temp_filename)

        except Exception as e:
            print(f"Error in listening thread: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_listening = False

    def listen(self, timeout=5):
        """
        Listen for speech input and convert to text (blocking mode)

        Args:
            timeout (int): Maximum time to wait for speech in seconds

        Returns:
            str: Recognized text or empty string if nothing recognized
        """
        self.result_text = None

        def callback(text):
            self.result_text = text

        print("🎤 Listening... (speak now)")
        self.start_listening(callback=callback, timeout=timeout)

        # Wait until listening is done
        while self.is_listening:
            time.sleep(0.1)

        # Wait a little longer for processing to finish
        for _ in range(10):  # Wait up to 1 second for processing
            if self.result_text is not None:
                break
            time.sleep(0.1)

        result = self.result_text or ""
        self.result_text = None
        return result

    def continuous_listen(self, callback, timeout=None):
        """
        Start continuous listening with callback for each recognized phrase

        Args:
            callback (function): Function to call with each recognized text
            timeout (int, optional): Stop listening after this many seconds
        """
        self.start_listening(callback=callback, timeout=timeout)

    def transcribe_file(self, file_path):
        """
        Transcribe audio from a file

        Args:
            file_path (str): Path to audio file

        Returns:
            str: Transcribed text
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return ""

        segments, _ = self.model.transcribe(file_path, language="en", beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text
