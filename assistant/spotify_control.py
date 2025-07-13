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
        # Existing initialization code...
        self.system_prompt = prompt_manager.get_prompt("spotify.general")

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
        return "❌ Spotify not connected. Please check your authentication."

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
        "search Never Gonna Give You Up"
    ]

    for cmd in test_commands:
        print(f"\n🔹 Command: {cmd}")
        result = control_spotify(cmd)
        print(f"   Result: {result}")
