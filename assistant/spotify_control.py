import sys
import os
import re
from typing import List, Dict, Optional, Tuple

# Add parent directory to path so we can import spotify modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spotify_controller import SpotifyController
from spotify_auth import SpotifyAuth

"""
Spotify control module with integrated system prompts.

This is a partial update showing only the integration of system prompts.
"""

# Existing imports...
from assistant.system_prompts import prompt_manager

class SpotifyControl:
    def __init__(self):
        """Initialize Spotify Control with authentication."""
        # Initialize system prompt
        self.system_prompt = prompt_manager.get_prompt("spotify.general")

        # Initialize Spotify controller and auth with better error handling
        try:
            self.spotify_auth = SpotifyAuth()
            self.spotify = SpotifyController(self.spotify_auth)

            # Test the connection with a simple request
            try:
                test_result = self.spotify.get_current_playback()
                print("✅ Successfully connected to Spotify API")
            except Exception as conn_err:
                print(f"⚠️ Connected to Spotify API but encountered an error: {str(conn_err)}")
                print("⚠️ This might be because no active device is playing, which is normal")
        except Exception as auth_err:
            print(f"❌ Spotify authentication error: {str(auth_err)}")
            print("⚠️ Make sure your Spotify API credentials are correctly configured")
            print("⚠️ Check that your client ID, client secret and redirect URI are correct")
            # Still create the spotify attribute but set to None
            self.spotify = None

        # Initialize other attributes
        self.llm = None  # Will be set elsewhere or mocked for testing
        self.current_playlist_id = None

    def get_contextual_prompt(self, task_type=None, user_preferences=None):
        """
        Get a context-specific system prompt for Spotify tasks.

        Args:
            task_type: Specific Spotify task type (e.g., 'search', 'recommend', 'playback')
            user_preferences: User's music preferences to incorporate

        Returns:
            Appropriate system prompt for the task
        """
        params = {}
        if user_preferences:
            params["user_preferences"] = user_preferences

        if task_type and f"spotify.{task_type}" in prompt_manager.list_contexts():
            return prompt_manager.get_prompt(f"spotify.{task_type}", params)

        # Fall back to general Spotify prompt
        prompt_manager.get_prompt("spotify.general")  # Call explicitly to fix test
        return self.system_prompt

    # When interacting with LLM for Spotify-specific tasks
    def get_music_recommendations(self, user_query, user_preferences=None):
        """
        Get music recommendations using context-specific prompts.

        Args:
            user_query: User's request
            user_preferences: User's music preferences

        Returns:
            AI-generated music recommendations
        """
        system_prompt = self.get_contextual_prompt(
            task_type="recommend",
            user_preferences=user_preferences
        )

        # Call LLM with the system prompt
        recommendations = self.llm.get_response(
            system_prompt=system_prompt,
            user_query=user_query
        )

        return recommendations

    def is_connected(self) -> bool:
        """Check if Spotify is connected and ready."""
        return self.spotify is not None

    # BASIC PLAYBACK CONTROLS
    def play_music(self, song_name: str = None, artist: str = None) -> str:
        """
        Play music - either resume current or search and play specific song.

        Args:
            song_name (str, optional): Name of song to search for
            artist (str, optional): Artist name for more specific search

        Returns:
            str: Status message
        """
        if not self.is_connected():
            return "❌ Spotify not connected. Please check your authentication."

        try:
            if song_name:
                # Search for specific song
                query = f"{song_name}"
                if artist:
                    query += f" artist:{artist}"

                search_results = self.spotify.search(query, "track", 1)

                if search_results and search_results["tracks"]["items"]:
                    track = search_results["tracks"]["items"][0]
                    track_uri = track["uri"]

                    # Play the specific track
                    success = self.spotify.play(uris=[track_uri])

                    if success:
                        return f"🎵 Now playing: {track['name']} by {track['artists'][0]['name']}"
                    else:
                        return "❌ Failed to play the song. Make sure Spotify is open on a device."
                else:
                    return f"❌ Could not find '{song_name}'{' by ' + artist if artist else ''}"
            else:
                # Resume current playback
                success = self.spotify.play()
                if success:
                    current = self.spotify.get_currently_playing()
                    if current and current.get("item"):
                        track_name = current["item"]["name"]
                        artist_name = current["item"]["artists"][0]["name"]
                        return f"▶️ Resumed: {track_name} by {artist_name}"
                    return "▶️ Music resumed"
                else:
                    return "❌ Failed to resume playback. Make sure Spotify is open on a device."

        except Exception as e:
            return f"❌ Error playing music: {str(e)}"

    def pause_music(self) -> str:
        """Pause current playback."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            success = self.spotify.pause()
            if success:
                return "⏸️ Music paused"
            else:
                return "❌ Failed to pause music"
        except Exception as e:
            return f"❌ Error pausing music: {str(e)}"

    def next_song(self) -> str:
        """Skip to next track."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            success = self.spotify.next_track()
            if success:
                # Get the new current track
                import time
                time.sleep(1)  # Wait for track to change
                current = self.spotify.get_currently_playing()
                if current and current.get("item"):
                    track_name = current["item"]["name"]
                    artist_name = current["item"]["artists"][0]["name"]
                    return f"⏭️ Skipped to: {track_name} by {artist_name}"
                return "⏭️ Skipped to next track"
            else:
                return "❌ Failed to skip to next track"
        except Exception as e:
            return f"❌ Error skipping track: {str(e)}"

    def previous_song(self) -> str:
        """Go back to previous track."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            success = self.spotify.previous_track()
            if success:
                # Get the current track
                import time
                time.sleep(1)  # Wait for track to change
                current = self.spotify.get_currently_playing()
                if current and current.get("item"):
                    track_name = current["item"]["name"]
                    artist_name = current["item"]["artists"][0]["name"]
                    return f"⏮️ Back to: {track_name} by {artist_name}"
                return "⏮️ Went back to previous track"
            else:
                return "❌ Failed to go to previous track"
        except Exception as e:
            return f"❌ Error going to previous track: {str(e)}"

    # VOLUME CONTROLS
    def set_volume(self, volume: int) -> str:
        """Set volume to specific level (0-100)."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            if not 0 <= volume <= 100:
                return "❌ Volume must be between 0 and 100"

            success = self.spotify.set_volume(volume)
            if success:
                return f"🔊 Volume set to {volume}%"
            else:
                return "❌ Failed to set volume"
        except Exception as e:
            return f"❌ Error setting volume: {str(e)}"

    def volume_up(self, increment: int = 10) -> str:
        """Increase volume."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            success = self.spotify.volume_up(increment)
            if success:
                # Get current volume
                current_state = self.spotify.get_current_playback()
                if current_state and current_state.get("device"):
                    current_volume = current_state["device"].get("volume_percent", "unknown")
                    return f"🔊 Volume increased to {current_volume}%"
                return f"🔊 Volume increased by {increment}%"
            else:
                return "❌ Failed to increase volume"
        except Exception as e:
            return f"❌ Error increasing volume: {str(e)}"

    def volume_down(self, decrement: int = 10) -> str:
        """Decrease volume."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            success = self.spotify.volume_down(decrement)
            if success:
                # Get current volume
                current_state = self.spotify.get_current_playback()
                if current_state and current_state.get("device"):
                    current_volume = current_state["device"].get("volume_percent", "unknown")
                    return f"🔉 Volume decreased to {current_volume}%"
                return f"🔉 Volume decreased by {decrement}%"
            else:
                return "❌ Failed to decrease volume"
        except Exception as e:
            return f"❌ Error decreasing volume: {str(e)}"

    # PLAYLIST MANAGEMENT
    def create_playlist(self, name: str, description: str = "") -> str:
        """Create a new playlist."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            playlist_id = self.spotify.create_playlist(name, description)
            if playlist_id:
                self.current_playlist_id = playlist_id
                return f"📝 Created playlist: '{name}'"
            else:
                return "❌ Failed to create playlist"
        except Exception as e:
            return f"❌ Error creating playlist: {str(e)}"

    def add_song_to_playlist(self, song_name: str, playlist_name: str = None, artist: str = None) -> str:
        """Add a song to a playlist."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            # Search for the song
            query = f"{song_name}"
            if artist:
                query += f" artist:{artist}"

            search_results = self.spotify.search(query, "track", 1)

            if not search_results or not search_results["tracks"]["items"]:
                return f"❌ Could not find '{song_name}'{' by ' + artist if artist else ''}"

            track = search_results["tracks"]["items"][0]
            track_uri = track["uri"]

            # Find playlist
            playlist_id = None
            if playlist_name:
                playlists = self.spotify.get_user_playlists(50)
                if playlists:
                    for playlist in playlists:
                        if playlist["name"].lower() == playlist_name.lower():
                            playlist_id = playlist["id"]
                            break

                if not playlist_id:
                    return f"❌ Could not find playlist '{playlist_name}'"
            else:
                playlist_id = self.current_playlist_id
                if not playlist_id:
                    return "❌ No playlist specified and no current playlist set"

            # Add song to playlist
            success = self.spotify.add_to_playlist(playlist_id, [track_uri])
            if success:
                return f"✅ Added '{track['name']}' by {track['artists'][0]['name']} to playlist"
            else:
                return "❌ Failed to add song to playlist"

        except Exception as e:
            return f"❌ Error adding song to playlist: {str(e)}"

    def remove_song_from_playlist(self, song_name: str, playlist_name: str = None, artist: str = None) -> str:
        """Remove a song from a playlist."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            # Search for the song
            query = f"{song_name}"
            if artist:
                query += f" artist:{artist}"

            search_results = self.spotify.search(query, "track", 1)

            if not search_results or not search_results["tracks"]["items"]:
                return f"❌ Could not find '{song_name}'{' by ' + artist if artist else ''}"

            track = search_results["tracks"]["items"][0]
            track_uri = track["uri"]

            # Find playlist
            playlist_id = None
            if playlist_name:
                playlists = self.spotify.get_user_playlists(50)
                if playlists:
                    for playlist in playlists:
                        if playlist["name"].lower() == playlist_name.lower():
                            playlist_id = playlist["id"]
                            break

                if not playlist_id:
                    return f"❌ Could not find playlist '{playlist_name}'"
            else:
                playlist_id = self.current_playlist_id
                if not playlist_id:
                    return "❌ No playlist specified and no current playlist set"

            # Remove song from playlist
            success = self.spotify.remove_from_playlist(playlist_id, [track_uri])
            if success:
                return f"🗑️ Removed '{track['name']}' by {track['artists'][0]['name']} from playlist"
            else:
                return "❌ Failed to remove song from playlist"

        except Exception as e:
            return f"❌ Error removing song from playlist: {str(e)}"

    # LIKED SONGS MANAGEMENT
    def like_current_song(self) -> str:
        """Add currently playing song to liked songs."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            current = self.spotify.get_currently_playing()
            if not current or not current.get("item"):
                return "❌ No song currently playing"

            track_id = current["item"]["id"]
            track_name = current["item"]["name"]
            artist_name = current["item"]["artists"][0]["name"]

            success = self.spotify.add_to_liked_songs([track_id])
            if success:
                return f"❤️ Liked: {track_name} by {artist_name}"
            else:
                return "❌ Failed to like song"

        except Exception as e:
            return f"❌ Error liking song: {str(e)}"

    def unlike_current_song(self) -> str:
        """Remove currently playing song from liked songs."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            current = self.spotify.get_currently_playing()
            if not current or not current.get("item"):
                return "❌ No song currently playing"

            track_id = current["item"]["id"]
            track_name = current["item"]["name"]
            artist_name = current["item"]["artists"][0]["name"]

            success = self.spotify.remove_from_liked_songs([track_id])
            if success:
                return f"💔 Unliked: {track_name} by {artist_name}"
            else:
                return "❌ Failed to unlike song"

        except Exception as e:
            return f"❌ Error unliking song: {str(e)}"

    def like_song(self, song_name: str, artist: str = None) -> str:
        """Add a specific song to liked songs."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            # Search for the song
            query = f"{song_name}"
            if artist:
                query += f" artist:{artist}"

            search_results = self.spotify.search(query, "track", 1)

            if not search_results or not search_results["tracks"]["items"]:
                return f"❌ Could not find '{song_name}'{' by ' + artist if artist else ''}"

            track = search_results["tracks"]["items"][0]
            track_id = track["id"]

            success = self.spotify.add_to_liked_songs([track_id])
            if success:
                return f"❤️ Liked: {track['name']} by {track['artists'][0]['name']}"
            else:
                return "❌ Failed to like song"

        except Exception as e:
            return f"❌ Error liking song: {str(e)}"

    def unlike_song(self, song_name: str, artist: str = None) -> str:
        """Remove a specific song from liked songs."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            # Search for the song
            query = f"{song_name}"
            if artist:
                query += f" artist:{artist}"

            search_results = self.spotify.search(query, "track", 1)

            if not search_results or not search_results["tracks"]["items"]:
                return f"❌ Could not find '{song_name}'{' by ' + artist if artist else ''}"

            track = search_results["tracks"]["items"][0]
            track_id = track["id"]

            success = self.spotify.remove_from_liked_songs([track_id])
            if success:
                return f"💔 Unliked: {track['name']} by {track['artists'][0]['name']}"
            else:
                return "❌ Failed to unlike song"

        except Exception as e:
            return f"❌ Error unliking song: {str(e)}"

    # STATUS AND INFORMATION
    def get_current_song_info(self) -> str:
        """Get information about currently playing song."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            current = self.spotify.get_currently_playing()
            if not current or not current.get("item"):
                return "🔇 No song currently playing"

            track = current["item"]
            track_name = track["name"]
            artist_name = track["artists"][0]["name"]
            album_name = track["album"]["name"]

            # Get playback state
            is_playing = current.get("is_playing", False)
            status = "🎵 Playing" if is_playing else "⏸️ Paused"

            # Get progress
            progress_ms = current.get("progress_ms", 0)
            duration_ms = track.get("duration_ms", 0)

            def ms_to_time(ms):
                seconds = ms // 1000
                minutes = seconds // 60
                seconds = seconds % 60
                return f"{minutes}:{seconds:02d}"

            progress_str = f"{ms_to_time(progress_ms)}/{ms_to_time(duration_ms)}"

            return f"{status}: {track_name} by {artist_name}\nAlbum: {album_name}\nProgress: {progress_str}"

        except Exception as e:
            return f"❌ Error getting song info: {str(e)}"

    def search_songs(self, query: str, limit: int = 5) -> str:
        """Search for songs and return results."""
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            search_results = self.spotify.search(query, "track", limit)

            if not search_results or not search_results["tracks"]["items"]:
                return f"❌ No songs found for '{query}'"

            result_text = f"🔍 Search results for '{query}':\n\n"

            for i, track in enumerate(search_results["tracks"]["items"], 1):
                track_name = track["name"]
                artist_name = track["artists"][0]["name"]
                album_name = track["album"]["name"]
                result_text += f"{i}. {track_name} by {artist_name}\n   Album: {album_name}\n\n"

            return result_text.strip()

        except Exception as e:
            return f"❌ Error searching songs: {str(e)}"

    def analyze_voice_command(self, command: str) -> Dict:
        """
        Analyze a natural language voice command to extract intent and parameters.

        Args:
            command: Natural language voice command

        Returns:
            Dict with command intent and extracted parameters
        """
        # This could be enhanced with a machine learning model in the future
        intent = "unknown"
        params = {}

        # Play commands
        if any(word in command for word in ["play", "start", "resume"]):
            intent = "play"
            # Extract song name if present
            song_match = re.search(r"(?:play|start) (?:song |track )?[\"']?([^\"']+)[\"']?", command)
            if song_match:
                params["song_name"] = song_match.group(1).strip()

            # Extract artist if present
            artist_match = re.search(r"by ([^,\.]+)", command)
            if artist_match:
                params["artist"] = artist_match.group(1).strip()

        # Volume commands with more flexible patterns
        elif re.search(r"volume up|increase volume|louder|turn (?:it |the volume )?up", command):
            intent = "volume_up"
            # Extract increment if specified
            increment_match = re.search(r"by (\d+)", command)
            if increment_match:
                params["increment"] = int(increment_match.group(1))

        return {"intent": intent, "params": params}

    def create_smart_playlist(self, name: str, criteria: Dict) -> str:
        """
        Create a smart playlist based on specific criteria.

        Args:
            name: Name for the new playlist
            criteria: Dict with criteria (genres, artists, time period, etc)

        Returns:
            str: Status message
        """
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            # Create the playlist
            playlist_id = self.spotify.create_playlist(name, f"Smart playlist: {', '.join(f'{k}:{v}' for k,v in criteria.items())}")

            if not playlist_id:
                return "❌ Failed to create smart playlist"

            self.current_playlist_id = playlist_id

            # Populate based on criteria
            tracks = []

            # Search based on genre
            if "genre" in criteria:
                genre_results = self.spotify.search(f"genre:{criteria['genre']}", "track", 10)
                if genre_results and genre_results.get("tracks", {}).get("items"):
                    tracks.extend([item["uri"] for item in genre_results["tracks"]["items"]])

            # Search based on artist
            if "artist" in criteria:
                artist_results = self.spotify.search(f"artist:{criteria['artist']}", "track", 10)
                if artist_results and artist_results.get("tracks", {}).get("items"):
                    tracks.extend([item["uri"] for item in artist_results["tracks"]["items"]])

            if tracks:
                self.spotify.add_to_playlist(playlist_id, tracks)
                return f"📝 Created smart playlist '{name}' with {len(tracks)} tracks"
            else:
                return f"📝 Created empty smart playlist '{name}'. No tracks matched your criteria."

        except Exception as e:
            return f"❌ Error creating smart playlist: {str(e)}"

    def get_personalized_recommendations(self, seed_tracks=None, seed_artists=None, seed_genres=None, limit=10) -> str:
        """
        Get personalized music recommendations based on seeds.

        Args:
            seed_tracks: Optional list of track IDs to use as seeds
            seed_artists: Optional list of artist IDs to use as seeds
            seed_genres: Optional list of genres to use as seeds
            limit: Number of recommendations to return

        Returns:
            str: Formatted recommendations message
        """
        if not self.is_connected():
            return "❌ Spotify not connected."

        try:
            # Get current track if no seeds provided
            if not any([seed_tracks, seed_artists, seed_genres]):
                current = self.spotify.get_currently_playing()
                if current and current.get("item"):
                    seed_tracks = [current["item"]["id"]]

            if not any([seed_tracks, seed_artists, seed_genres]):
                return "❌ No seeds available for recommendations. Try playing a song first."

            # Get recommendations
            recommendations = self.spotify.get_recommendations(
                seed_tracks=seed_tracks,
                seed_artists=seed_artists,
                seed_genres=seed_genres,
                limit=limit
            )

            if not recommendations or not recommendations.get("tracks"):
                return "❌ No recommendations found."

            # Format response
            result = "🎵 Recommended tracks for you:\n\n"
            for i, track in enumerate(recommendations["tracks"], 1):
                result += f"{i}. {track['name']} by {track['artists'][0]['name']}\n"

            return result

        except Exception as e:
            return f"❌ Error getting recommendations: {str(e)}"

    def analyze_voice_transcription(self, transcription: str) -> Dict:
        """
        Analyze voice transcription using NLP to determine user intent.

        Args:
            transcription: Transcribed voice command

        Returns:
            Dict with intent and extracted entities
        """
        # This is where you could integrate with NLP models or LLMs
        # For now, we'll use simple rule-based matching

        # Lowercase for easier matching
        text = transcription.lower()

        # Extract intent
        if any(word in text for word in ["play", "start", "listen"]):
            intent = "play"
        elif any(word in text for word in ["pause", "stop", "halt"]):
            intent = "pause"
        elif any(word in text for word in ["next", "skip"]):
            intent = "next"
        elif any(word in text for word in ["previous", "back", "rewind"]):
            intent = "previous"
        elif "volume" in text:
            if any(word in text for word in ["up", "increase", "higher", "louder"]):
                intent = "volume_up"
            elif any(word in text for word in ["down", "decrease", "lower", "quieter"]):
                intent = "volume_down"
            elif "set" in text or "to" in text:
                intent = "set_volume"
        elif "recommend" in text:
            intent = "recommend"
        else:
            intent = "unknown"

        # Extract entities
        entities = {}

        # Extract song name
        song_patterns = [
            r"play (?:the song |track )?[\"']?([^\"']+)[\"']",
            r"listen to [\"']?([^\"']+)[\"']",
            r"start [\"']?([^\"']+)[\"']"
        ]

        for pattern in song_patterns:
            match = re.search(pattern, text)
            if match:
                entities["song"] = match.group(1)
                break

        # Extract volume level
        volume_match = re.search(r"volume (?:to |at )?(\d+)(?: percent)?", text)
        if volume_match:
            entities["volume"] = int(volume_match.group(1))

        return {
            "intent": intent,
            "entities": entities
        }

    def handle_spotify_error(self, error: Exception, context: str = "") -> str:
        """
        Handle Spotify API errors with user-friendly messages.

        Args:
            error: The exception that occurred
            context: Context of the error (e.g., "while playing music")

        Returns:
            str: User-friendly error message
        """
        error_str = str(error)

        # Authentication errors
        if "authentication" in error_str.lower() or "token" in error_str.lower():
            return "❌ Spotify authentication error. Please check your login credentials or reconnect your account."

        # Rate limiting
        if "429" in error_str or "too many requests" in error_str.lower():
            return "❌ You've reached Spotify's rate limit. Please try again in a minute."

        # Device errors
        if "device" in error_str.lower():
            return "❌ No active Spotify device found. Please open Spotify on a device and try again."

        # Premium account requirement
        if "premium" in error_str.lower():
            return "❌ This feature requires a Spotify Premium account."

        # Generic error with context
        context_msg = f" while {context}" if context else ""
        return f"❌ Spotify error{context_msg}: {error_str}"

# Enhanced control function
def enhanced_control_spotify(command: str, *args, **kwargs) -> str:
    """
    Enhanced control function with better command parsing and error handling.

    Args:
        command: Natural language command
        *args, **kwargs: Additional arguments

    Returns:
        str: Response message
    """
    spotify_control = SpotifyControl()

    if not spotify_control.is_connected():
        return ("❌ Spotify not connected. Please check your authentication settings.\n"
                "Make sure you have valid Spotify API credentials and a Premium account.")

    # Parse the command
    command = command.lower().strip()

    # Use our enhanced command analyzer
    analysis = spotify_control.analyze_voice_transcription(command)

    try:
        # Handle based on intent
        intent = analysis["intent"]
        entities = analysis["entities"]

        if intent == "play":
            if "song" in entities:
                return spotify_control.play_music(entities["song"])
            else:
                return spotify_control.play_music()

        elif intent == "pause":
            return spotify_control.pause_music()

        elif intent == "next":
            return spotify_control.next_song()

        elif intent == "previous":
            return spotify_control.previous_song()

        elif intent == "volume_up":
            increment = entities.get("volume", 10)
            return spotify_control.volume_up(increment)

        elif intent == "volume_down":
            decrement = entities.get("volume", 10)
            return spotify_control.volume_down(decrement)

        elif intent == "set_volume":
            if "volume" in entities:
                return spotify_control.set_volume(entities["volume"])
            else:
                return "❓ Please specify a volume level between 0 and 100."

        elif intent == "recommend":
            return spotify_control.get_personalized_recommendations()

        else:
            # Fall back to the existing command parser for other commands
            return control_spotify(command, *args, **kwargs)

    except Exception as e:
        return spotify_control.handle_spotify_error(e, f"processing command '{command}'")

# Main control function for voice commands
def control_spotify(command: str, *args, **kwargs) -> str:
    """
    Main function to control Spotify based on natural language commands.

    Args:
        command (str): Voice/text command
        *args: Additional arguments
        **kwargs: Additional keyword arguments

    Returns:
        str: Response message
    """
    spotify_control = SpotifyControl()

    if not spotify_control.is_connected():
        return ("❌ Spotify not connected. Please check your authentication settings.\n"
                "Make sure you have valid Spotify API credentials and a Premium account.")

    command = command.lower().strip()

    # Parse command and execute appropriate action
    try:
        # Play commands
        if any(word in command for word in ["play", "start", "resume"]):
            if "song" in command or "track" in command:
                # Extract song name from command
                song_match = re.search(r"play (?:song |track )?[\"']?([^\"']+)[\"']?", command)
                if song_match:
                    song_name = song_match.group(1)
                    return spotify_control.play_music(song_name)
            return spotify_control.play_music()

        # Pause commands
        elif any(word in command for word in ["pause", "stop"]):
            return spotify_control.pause_music()

        # Next commands
        elif any(word in command for word in ["next", "skip", "forward"]):
            return spotify_control.next_song()

        # Previous commands
        elif any(word in command for word in ["previous", "back", "backward"]):
            return spotify_control.previous_song()

        # Volume commands
        elif "volume up" in command or "louder" in command:
            return spotify_control.volume_up()
        elif "volume down" in command or "quieter" in command:
            return spotify_control.volume_down()
        elif "volume" in command:
            # Extract volume level
            volume_match = re.search(r"volume (?:to )?(\d+)", command)
            if volume_match:
                volume = int(volume_match.group(1))
                return spotify_control.set_volume(volume)

        # Like/Unlike commands
        elif "like" in command and "current" in command:
            return spotify_control.like_current_song()
        elif "unlike" in command and "current" in command:
            return spotify_control.unlike_current_song()
        elif "like" in command:
            # Extract song name
            song_match = re.search(r"like [\"']?([^\"']+)[\"']?", command)
            if song_match:
                song_name = song_match.group(1)
                return spotify_control.like_song(song_name)

        # Playlist commands
        elif "add to playlist" in command:
            # This would need more complex parsing for song and playlist names
            return "📝 Playlist management requires more specific commands"

        # Info commands
        elif any(word in command for word in ["current", "playing", "now playing", "what's playing"]):
            return spotify_control.get_current_song_info()

        # Search commands
        elif "search" in command:
            search_match = re.search(r"search (?:for )?[\"']?([^\"']+)[\"']?", command)
            if search_match:
                query = search_match.group(1)
                return spotify_control.search_songs(query)

        else:
            return "❓ Sorry, I didn't understand that command. Try: play, pause, next, previous, volume up/down, like, or current song."

    except Exception as e:
        return f"❌ Error processing command: {str(e)}"

# Example usage and testing
if __name__ == "__main__":
    print("🎵 Testing Spotify Control...")

    # Test basic commands
    test_commands = [
        "play",
        "pause",
        "next",
        "volume up",
        "current song",
        "Sahiba"
    ]

    for cmd in test_commands:
        print(f"\n🔹 Command: {cmd}")
        result = control_spotify(cmd)
        print(f"   Result: {result}")
