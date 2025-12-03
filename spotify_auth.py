import json
import os
import webbrowser
import base64
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs
import threading

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
REDIRECT_URI = "http://localhost:8888/callback"
SCOPES = "user-modify-playback-state user-read-playback-state"

class SpotifyAuth:
    def __init__(self, config_path):
        self.config_path = config_path
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        self.refresh_token = None
        self.load_config()
    
    def load_config(self):
        """Load Spotify credentials from config file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.client_id = data.get('client_id')
                    self.client_secret = data.get('client_secret')
                    self.access_token = data.get('access_token')
                    self.refresh_token = data.get('refresh_token')
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save Spotify credentials to config file"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'access_token': self.access_token,
                'refresh_token': self.refresh_token
            }
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def set_credentials(self, client_id, client_secret):
        """Set Spotify app credentials"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.save_config()
    
    def get_auth_url(self):
        """Generate Spotify authorization URL"""
        if not self.client_id:
            return None
        
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'scope': SCOPES
        }
        return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
    
    def start_auth_flow(self, callback):
        """Start OAuth flow with callback server"""
        auth_url = self.get_auth_url()
        if not auth_url:
            return False
        
        # Start callback server
        server = CallbackServer(self, callback)
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()
        
        # Open browser
        webbrowser.open(auth_url)
        return True
    
    def exchange_code(self, code):
        """Exchange authorization code for access token"""
        if not self.client_id or not self.client_secret:
            return False
        
        auth_str = f"{self.client_id}:{self.client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {b64_auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI
        }
        
        try:
            response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens.get('access_token')
                self.refresh_token = tokens.get('refresh_token')
                self.save_config()
                return True
        except Exception as e:
            print(f"Error exchanging code: {e}")
        
        return False
    
    def refresh_access_token(self):
        """Refresh expired access token"""
        if not self.refresh_token or not self.client_id or not self.client_secret:
            return False
        
        auth_str = f"{self.client_id}:{self.client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {b64_auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        
        try:
            response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens.get('access_token')
                self.save_config()
                return True
        except Exception as e:
            print(f"Error refreshing token: {e}")
        
        return False
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.access_token is not None
    
    def play_track(self, track_uri, device_id=None):
        """Play a specific track"""
        if not self.access_token:
            return False
        
        url = "https://api.spotify.com/v1/me/player/play"
        if device_id:
            url += f"?device_id={device_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'uris': [track_uri]
        }
        
        try:
            response = requests.put(url, headers=headers, json=data)
            if response.status_code == 401:
                # Token expired, try refresh
                if self.refresh_access_token():
                    return self.play_track(track_uri, device_id)
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error playing track: {e}")
            return False
    
    def set_volume(self, volume_percent):
        """Set playback volume (0-100)"""
        if not self.access_token:
            return False
        
        url = f"https://api.spotify.com/v1/me/player/volume?volume_percent={volume_percent}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.put(url, headers=headers)
            if response.status_code == 401:
                if self.refresh_access_token():
                    return self.set_volume(volume_percent)
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error setting volume: {e}")
            return False

class CallbackServer:
    def __init__(self, auth, callback):
        self.auth = auth
        self.callback = callback
        self.server = None
    
    def start(self):
        """Start HTTP server for OAuth callback"""
        handler = self.create_handler()
        self.server = HTTPServer(('localhost', 8888), handler)
        self.server.handle_request()  # Handle one request then stop
    
    def create_handler(self):
        """Create request handler with access to auth and callback"""
        auth = self.auth
        callback = self.callback
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                query = parse_qs(self.path.split('?')[1] if '?' in self.path else '')
                code = query.get('code', [None])[0]
                
                if code:
                    success = auth.exchange_code(code)
                    callback(success)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    if success:
                        html = """
                        <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>✅ Success!</h1>
                        <p>You're now connected to Spotify!</p>
                        <p>You can close this window and return to BeatWake.</p>
                        </body></html>
                        """
                    else:
                        html = """
                        <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h1>❌ Error</h1>
                        <p>Failed to connect to Spotify. Please try again.</p>
                        </body></html>
                        """
                    self.wfile.write(html.encode())
            
            def log_message(self, format, *args):
                pass  # Suppress logging
        
        return CallbackHandler
