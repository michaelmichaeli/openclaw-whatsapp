#!/usr/bin/env python3
"""
One-time Google Calendar OAuth 2.0 setup.
Run this once to obtain and store a refresh token.

Steps before running:
  1. Go to https://console.cloud.google.com/
  2. Create a project, enable Google Calendar API
  3. Create OAuth 2.0 credentials (type: "Desktop app")
  4. Download the JSON and note client_id + client_secret
  5. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env (or enter them below)
  6. Run: python3 setup_google_auth.py
"""

import os
import sys
import json
import stat
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from dotenv import load_dotenv
except ImportError:
    print("Missing dependencies. Run: pip3 install -r requirements.txt")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CREDENTIALS_DIR = Path.home() / ".calendar_creator"
TOKEN_PATH = CREDENTIALS_DIR / "google_token.json"
CLIENT_SECRETS_PATH = CREDENTIALS_DIR / "google_client_secrets.json"


def ensure_secure_dir():
    CREDENTIALS_DIR.mkdir(exist_ok=True)
    os.chmod(CREDENTIALS_DIR, stat.S_IRWXU)  # 700


def get_client_config():
    load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id:
        client_id = input("Enter your Google OAuth Client ID: ").strip()
    if not client_secret:
        client_secret = input("Enter your Google OAuth Client Secret: ").strip()

    if not client_id or not client_secret:
        print("Error: client_id and client_secret are required.")
        sys.exit(1)

    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    }


def run_oauth_flow(client_config):
    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    creds = flow.run_local_server(port=0)
    return creds


def save_token(creds):
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    }
    TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
    os.chmod(TOKEN_PATH, stat.S_IRUSR | stat.S_IWUSR)  # 600
    print(f"\nToken saved to: {TOKEN_PATH}")
    print(f"Refresh token: {creds.refresh_token}")
    print("\nSetup complete. You can now use create_event.py with --calendar google")


def main():
    ensure_secure_dir()
    print("=== Google Calendar OAuth Setup ===\n")
    print("A browser window will open. Log in with your Google account")
    print("and grant access to Google Calendar.\n")

    client_config = get_client_config()
    creds = run_oauth_flow(client_config)
    save_token(creds)


if __name__ == "__main__":
    main()
