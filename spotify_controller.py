import os
from dotenv import load_dotenv
from spotify_auth import SpotifyAuth
import requests
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()

class SpotifyController:
    def __init__(self, access_token: str = None):
        if access_token:
            self.access_token = access_token
        else:
            # Authenticate automatically
            auth = SpotifyAuth()
            self.access_token = auth.authenticate()

        self.base_url = "https://api.spotify.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
        """Make a request to the Spotify Web API."""
        url = f"{self.base_url}/{endpoint}"

        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code in [200, 201, 204]:
                return response.json() if response.content else {"success": True}
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    # PLAYBACK CONTROL METHODS
    def play(self, context_uri: Optional[str] = None, uris: Optional[List[str]] = None,
             device_id: Optional[str] = None, position_ms: int = 0) -> bool:
        """Start or resume playback."""
        endpoint = "me/player/play"
        if device_id:
            endpoint += f"?device_id={device_id}"

        data = {}
        if context_uri:
            data["context_uri"] = context_uri
        if uris:
            data["uris"] = uris
        if position_ms > 0:
            data["position_ms"] = position_ms

        result = self._make_request(endpoint, "PUT", data)
        return result is not None

    def pause(self, device_id: Optional[str] = None) -> bool:
        """Pause playback."""
        endpoint = "me/player/pause"
        if device_id:
            endpoint += f"?device_id={device_id}"

        result = self._make_request(endpoint, "PUT")
        return result is not None

    def next_track(self, device_id: Optional[str] = None) -> bool:
        """Skip to next track."""
        endpoint = "me/player/next"
        if device_id:
            endpoint += f"?device_id={device_id}"

        result = self._make_request(endpoint, "POST")
        return result is not None

    def previous_track(self, device_id: Optional[str] = None) -> bool:
        """Skip to previous track."""
        endpoint = "me/player/previous"
        if device_id:
            endpoint += f"?device_id={device_id}"

        result = self._make_request(endpoint, "POST")
        return result is not None

    def set_volume(self, volume_percent: int, device_id: Optional[str] = None) -> bool:
        """Set playback volume."""
        if not 0 <= volume_percent <= 100:
            print("Volume must be between 0 and 100")
            return False

        endpoint = f"me/player/volume?volume_percent={volume_percent}"
        if device_id:
            endpoint += f"&device_id={device_id}"

        result = self._make_request(endpoint, "PUT")
        return result is not None

    def volume_up(self, increment: int = 10, device_id: Optional[str] = None) -> bool:
        """Increase volume."""
        current_state = self.get_current_playback()
        if current_state and current_state.get("device"):
            current_volume = current_state["device"].get("volume_percent", 50)
            new_volume = min(100, current_volume + increment)
            return self.set_volume(new_volume, device_id)
        return False

    def volume_down(self, decrement: int = 10, device_id: Optional[str] = None) -> bool:
        """Decrease volume."""
        current_state = self.get_current_playback()
        if current_state and current_state.get("device"):
            current_volume = current_state["device"].get("volume_percent", 50)
            new_volume = max(0, current_volume - decrement)
            return self.set_volume(new_volume, device_id)
        return False

    # PLAYLIST MANAGEMENT METHODS
    def create_playlist(self, name: str, description: str = "", public: bool = False) -> Optional[str]:
        """Create a new playlist."""
        user_info = self._make_request("me")
        if not user_info:
            return None

        user_id = user_info["id"]

        data = {
            "name": name,
            "description": description,
            "public": public
        }

        result = self._make_request(f"users/{user_id}/playlists", "POST", data)
        return result["id"] if result else None

    def add_to_playlist(self, playlist_id: str, track_uris: List[str], position: Optional[int] = None) -> bool:
        """Add tracks to a playlist."""
        endpoint = f"playlists/{playlist_id}/tracks"

        data = {"uris": track_uris}
        if position is not None:
            data["position"] = position

        result = self._make_request(endpoint, "POST", data)
        return result is not None

    def remove_from_playlist(self, playlist_id: str, track_uris: List[str]) -> bool:
        """Remove tracks from a playlist."""
        endpoint = f"playlists/{playlist_id}/tracks"

        tracks = [{"uri": uri} for uri in track_uris]
        data = {"tracks": tracks}

        result = self._make_request(endpoint, "DELETE", data)
        return result is not None

    def get_user_playlists(self, limit: int = 20, offset: int = 0) -> Optional[List[Dict]]:
        """Get user's playlists."""
        endpoint = f"me/playlists?limit={limit}&offset={offset}"
        result = self._make_request(endpoint)
        return result["items"] if result else None

    # LIKED SONGS METHODS
    def add_to_liked_songs(self, track_ids: List[str]) -> bool:
        """Add tracks to user's liked songs."""
        endpoint = "me/tracks"
        data = {"ids": track_ids}

        result = self._make_request(endpoint, "PUT", data)
        return result is not None

    def remove_from_liked_songs(self, track_ids: List[str]) -> bool:
        """Remove tracks from user's liked songs."""
        endpoint = "me/tracks"
        data = {"ids": track_ids}

        result = self._make_request(endpoint, "DELETE", data)
        return result is not None

    def check_liked_songs(self, track_ids: List[str]) -> Optional[List[bool]]:
        """Check if tracks are in user's liked songs."""
        ids_string = ",".join(track_ids)
        endpoint = f"me/tracks/contains?ids={ids_string}"

        result = self._make_request(endpoint)
        return result if result else None

    def get_liked_songs(self, limit: int = 20, offset: int = 0) -> Optional[List[Dict]]:
        """Get user's liked songs."""
        endpoint = f"me/tracks?limit={limit}&offset={offset}"
        result = self._make_request(endpoint)
        return result["items"] if result else None

    # UTILITY METHODS
    def get_current_playback(self) -> Optional[Dict]:
        """Get current playback state."""
        return self._make_request("me/player")

    def get_currently_playing(self) -> Optional[Dict]:
        """Get currently playing track."""
        return self._make_request("me/player/currently-playing")

    def search(self, query: str, search_type: str = "track", limit: int = 20) -> Optional[Dict]:
        """Search for tracks, albums, artists, or playlists."""
        endpoint = f"search?q={query}&type={search_type}&limit={limit}"
        return self._make_request(endpoint)

    def get_track_info(self, track_id: str) -> Optional[Dict]:
        """Get detailed information about a track."""
        return self._make_request(f"tracks/{track_id}")

    def get_user_top_tracks(self, time_range: str = "medium_term", limit: int = 20) -> Optional[List[Dict]]:
        """Get user's top tracks."""
        endpoint = f"me/top/tracks?time_range={time_range}&limit={limit}"
        result = self._make_request(endpoint)
        return result["items"] if result else None
