import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes required to edit docs and compose gmail drafts
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/gmail.compose'
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')

def get_credentials():
    """Gets valid user credentials from storage or initiates OAuth flow."""
    creds = None
    
    # 1. Try loading token from environment variables (for cloud deployment)
    token_env = os.environ.get("GOOGLE_TOKEN_JSON")
    if token_env:
        try:
            token_data = json.loads(token_env)
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            print(f"Error loading GOOGLE_TOKEN_JSON: {e}")
            
    # Fallback to local token.json
    if not creds and os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        
    # If there are no valid credentials, handle authentication
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # If refresh fails, force re-authentication
                creds = None
                
        if not creds:
            # 2. Try loading credentials from environment variables (for cloud deployment)
            creds_env = os.environ.get("GOOGLE_CREDENTIALS_JSON")
            if creds_env:
                try:
                    client_config = json.loads(creds_env)
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    # Note: We cannot spin up local browser-server in headless environment
                    raise ValueError(
                        "Credentials expired or invalid in cloud environment. "
                        "Please refresh token.json locally and update the GOOGLE_TOKEN_JSON variable."
                    )
                except Exception as e:
                    if isinstance(e, ValueError):
                        raise e
                    raise ValueError(f"Error parsing GOOGLE_CREDENTIALS_JSON: {e}")
            
            # Local file fallback
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"credentials.json is missing at {CREDENTIALS_PATH}. "
                    "Please download it from Google Cloud Console and place it there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            # Starts a local web server for authorization
            creds = flow.run_local_server(port=0)
            
        # Save credentials for subsequent runs
        try:
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
        except Exception as e:
            # Ephemeral environment might not allow file writing, which is okay
            print(f"Warning: Could not save token.json locally: {e}")
            
    return creds

