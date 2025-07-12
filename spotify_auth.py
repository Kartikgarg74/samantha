import os
import base64
import requests
import webbrowser
from urllib.parse import urlencode
from flask import Flask, request
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SpotifyAuth:
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')
        self.access_token = None
        self.refresh_token = None

        if not self.client_id or not self.client_secret:
            raise ValueError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET in .env file")

    def get_auth_url(self):
        """Generate Spotify authorization URL"""
        scopes = [
            'user-read-playback-state',
            'user-modify-playback-state',
            'user-library-read',
            'user-library-modify',
            'playlist-read-private',
            'playlist-modify-public',
            'playlist-modify-private',
            'user-read-currently-playing',
            'user-top-read'
        ]

        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(scopes),
            'show_dialog': 'true'
        }

        auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
        return auth_url

    def get_token_from_code(self, code):
        """Exchange authorization code for access token"""
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

        headers = {
            'Authorization': f'Basic {auth_base64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)

        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token')
            return token_data
        else:
            raise Exception(f"Failed to get token: {response.text}")

    def refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            raise Exception("No refresh token available")

        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')

        headers = {
            'Authorization': f'Basic {auth_base64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }

        response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)

        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            return token_data
        else:
            raise Exception(f"Failed to refresh token: {response.text}")

    def authenticate(self):
        """Complete OAuth flow and return access token"""
        app = Flask(__name__)
        auth_code = None

        @app.route('/callback')
        def callback():
            nonlocal auth_code
            code = request.args.get('code')
            error = request.args.get('error')

            if error:
                return f"Authentication failed: {error}", 400

            if code:
                auth_code = code
                # Shutdown the server
                func = request.environ.get('werkzeug.server.shutdown')
                if func is None:
                    raise RuntimeError('Not running with the Werkzeug Server')
                func()
                return "Authentication successful! You can close this window.", 200

            return "No authorization code received", 400

        # Start Flask server in a separate thread
        server_thread = threading.Thread(target=lambda: app.run(port=8888, debug=False))
        server_thread.daemon = True
        server_thread.start()

        # Give server time to start
        time.sleep(1)

        # Open browser for authentication
        auth_url = self.get_auth_url()
        print(f"Opening browser for Spotify authentication...")
        print(f"If browser doesn't open, go to: {auth_url}")
        webbrowser.open(auth_url)

        # Wait for callback
        print("Waiting for authentication...")
        while auth_code is None:
            time.sleep(1)

        # Exchange code for token
        token_data = self.get_token_from_code(auth_code)
        print("Authentication successful!")
        return self.access_token

if __name__ == "__main__":
    auth = SpotifyAuth()
    token = auth.authenticate()
    print(f"Access Token: {token}")
