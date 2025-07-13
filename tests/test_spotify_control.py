import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unittest.mock import patch, MagicMock
import re

from assistant.spotify_control import SpotifyControl, control_spotify, enhanced_control_spotify

class TestSpotifyControl(unittest.TestCase):
    """Test SpotifyControl class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher = patch('assistant.spotify_control.prompt_manager')
        self.mock_prompt_manager = self.patcher.start()
        self.mock_prompt_manager.get_prompt.return_value = "Test Spotify prompt"
        self.mock_prompt_manager.list_contexts.return_value = ["spotify.general", "spotify.recommend", "spotify.search"]

        # Mock the SpotifyAuth and SpotifyController classes
        self.auth_patcher = patch('assistant.spotify_control.SpotifyAuth')
        self.controller_patcher = patch('assistant.spotify_control.SpotifyController')

        self.mock_auth = self.auth_patcher.start()
        self.mock_controller = self.controller_patcher.start()

        # Create a mock for the LLM
        self.mock_llm = MagicMock()

        # Create the SpotifyControl instance
        self.spotify_control = SpotifyControl()
        self.spotify_control.llm = self.mock_llm

    def tearDown(self):
        """Tear down test fixtures."""
        self.patcher.stop()
        self.auth_patcher.stop()
        self.controller_patcher.stop()

    def test_initialization(self):
        """Test SpotifyControl initialization."""
        self.mock_prompt_manager.get_prompt.assert_called_with("spotify.general")
        self.assertIsNotNone(self.spotify_control.spotify)

    def test_get_contextual_prompt(self):
        """Test getting contextual prompts."""
        # Test with valid task type
        prompt = self.spotify_control.get_contextual_prompt("recommend", {"genre": "rock"})
        self.mock_prompt_manager.get_prompt.assert_called_with("spotify.recommend", {"user_preferences": {"genre": "rock"}})

        # Reset call history and reconfigure mock
        self.mock_prompt_manager.get_prompt.reset_mock()
        self.mock_prompt_manager.get_prompt.return_value = "Test Spotify general prompt"

        # Test with invalid task type
        result = self.spotify_control.get_contextual_prompt("invalid_task")
        self.mock_prompt_manager.get_prompt.assert_called_with("spotify.general")

    def test_get_music_recommendations(self):
        """Test getting music recommendations."""
        # Configure mock
        self.mock_llm.get_response.return_value = "Test recommendations"

        # Test method
        result = self.spotify_control.get_music_recommendations(
            "Recommend me some rock music", {"genre": "rock"}
        )

        # Verify the result and method calls
        self.assertEqual(result, "Test recommendations")
        self.mock_llm.get_response.assert_called_once()

    def test_is_connected(self):
        """Test connection check."""
        # Test when spotify is set
        self.assertTrue(self.spotify_control.is_connected())

        # Test when spotify is None
        self.spotify_control.spotify = None
        self.assertFalse(self.spotify_control.is_connected())

    def test_play_music_no_song(self):
        """Test playing music without specifying a song."""
        # Configure mock
        mock_spotify = self.spotify_control.spotify
        mock_spotify.play.return_value = True
        mock_spotify.get_currently_playing.return_value = {
            "item": {
                "name": "Test Song",
                "artists": [{"name": "Test Artist"}]
            }
        }

        # Test method
        result = self.spotify_control.play_music()

        # Verify result and method calls
        self.assertEqual(result, "▶️ Resumed: Test Song by Test Artist")
        mock_spotify.play.assert_called_once()

    def test_play_music_with_song(self):
        """Test playing a specific song."""
        # Configure mock
        mock_spotify = self.spotify_control.spotify
        mock_spotify.search.return_value = {
            "tracks": {
                "items": [{
                    "uri": "spotify:track:123",
                    "name": "Bohemian Rhapsody",
                    "artists": [{"name": "Queen"}]
                }]
            }
        }
        mock_spotify.play.return_value = True

        # Test method
        result = self.spotify_control.play_music("Bohemian Rhapsody")

        # Verify result and method calls
        self.assertEqual(result, "🎵 Now playing: Bohemian Rhapsody by Queen")
        mock_spotify.search.assert_called_once_with("Bohemian Rhapsody", "track", 1)
        mock_spotify.play.assert_called_once_with(uris=["spotify:track:123"])


class TestControlSpotifyBasic(unittest.TestCase):
    """Test control_spotify function with basic command matching."""

    def test_play_command(self):
        """Test simple play command."""
        with patch('assistant.spotify_control.SpotifyControl') as mock_spotify_class:
            mock_spotify = mock_spotify_class.return_value
            mock_spotify.is_connected.return_value = True
            mock_spotify.play_music.return_value = "Playing music"

            result = control_spotify("play")

            mock_spotify.play_music.assert_called_once_with()
            self.assertEqual(result, "Playing music")

    def test_pause_command(self):
        """Test pause command."""
        with patch('assistant.spotify_control.SpotifyControl') as mock_spotify_class:
            mock_spotify = mock_spotify_class.return_value
            mock_spotify.is_connected.return_value = True
            mock_spotify.pause_music.return_value = "Music paused"

            result = control_spotify("pause")

            mock_spotify.pause_music.assert_called_once()
            self.assertEqual(result, "Music paused")

    def test_next_command(self):
        """Test next track command."""
        with patch('assistant.spotify_control.SpotifyControl') as mock_spotify_class:
            mock_spotify = mock_spotify_class.return_value
            mock_spotify.is_connected.return_value = True
            mock_spotify.next_song.return_value = "Next track"

            result = control_spotify("next")

            mock_spotify.next_song.assert_called_once()
            self.assertEqual(result, "Next track")


class TestVoiceAnalysis(unittest.TestCase):
    """Test voice analysis methods."""

    def setUp(self):
        """Set up test fixtures."""
        # Use patch as context managers for better control
        patcher1 = patch('assistant.spotify_control.SpotifyAuth')
        patcher2 = patch('assistant.spotify_control.SpotifyController')
        patcher3 = patch('assistant.spotify_control.prompt_manager')

        self.mock_auth = patcher1.start()
        self.mock_controller = patcher2.start()
        self.mock_prompt_manager = patcher3.start()

        self.addCleanup(patcher1.stop)
        self.addCleanup(patcher2.stop)
        self.addCleanup(patcher3.stop)

        # Create a SpotifyControl instance for testing
        self.spotify_control = SpotifyControl()

    def test_analyze_voice_command(self):
        """Test analyze_voice_command method."""
        result = self.spotify_control.analyze_voice_command("play bohemian rhapsody")

        self.assertEqual(result["intent"], "play")
        self.assertEqual(result["params"].get("song_name"), "bohemian rhapsody")

    def test_analyze_voice_transcription_basic(self):
        """Test analyze_voice_transcription method with a simple command."""
        result = self.spotify_control.analyze_voice_transcription("play")

        self.assertEqual(result["intent"], "play")

    def test_analyze_voice_transcription_volume(self):
        """Test analyze_voice_transcription method with volume command."""
        result = self.spotify_control.analyze_voice_transcription("volume up")

        self.assertEqual(result["intent"], "volume_up")


class TestEnhancedControl(unittest.TestCase):
    """Test enhanced_control_spotify function."""

    def test_enhanced_control_play(self):
        """Test enhanced control with basic play command."""
        with patch('assistant.spotify_control.SpotifyControl') as mock_spotify_class:
            mock_spotify = mock_spotify_class.return_value
            mock_spotify.is_connected.return_value = True
            mock_spotify.analyze_voice_transcription.return_value = {"intent": "play", "entities": {}}
            mock_spotify.play_music.return_value = "Playing music"

            result = enhanced_control_spotify("play")

            mock_spotify.analyze_voice_transcription.assert_called_once_with("play")
            mock_spotify.play_music.assert_called_once()
            self.assertEqual(result, "Playing music")


if __name__ == '__main__':
    unittest.main()
