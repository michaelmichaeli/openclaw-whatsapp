#!/usr/bin/env python3
"""
Calendar Event Creator — creates events in Google Calendar or Apple Calendar (iCloud).

Usage:
  python3 create_event.py --calendar google \
      --summary "Team Meeting" \
      --start "2026-05-10 14:00" \
      --end "2026-05-10 15:00" \
      --location "Tel Aviv Office" \
      --timezone "Asia/Jerusalem"

  python3 create_event.py --calendar apple \
      --summary "Dentist" \
      --start "2026-05-12 09:00" \
      --end "2026-05-12 10:00" \
      --timezone "Asia/Jerusalem"

First-time setup:
  Google: run setup_google_auth.py once, then set GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET in .env
  Apple:  set APPLE_ID and APPLE_APP_PASSWORD in .env
"""

import argparse
import json
import os
import sys
import stat
from datetime import datetime, timezone as dt_timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv not installed. Run: pip3 install -r requirements.txt")
    sys.exit(1)

CREDENTIALS_DIR = Path.home() / ".calendar_creator"
GOOGLE_TOKEN_PATH = CREDENTIALS_DIR / "google_token.json"
ENV_PATH = Path(__file__).parent.parent / ".env"


def load_env():
    load_dotenv(dotenv_path=ENV_PATH)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Create an event in Google Calendar or Apple Calendar (iCloud)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--calendar", choices=["google", "apple"], required=True,
        help="Target calendar: 'google' or 'apple'",
    )
    parser.add_argument("--summary", required=True, help="Event title")
    parser.add_argument(
        "--start", required=True,
        help="Start datetime in format 'YYYY-MM-DD HH:MM'",
    )
    parser.add_argument(
        "--end", required=True,
        help="End datetime in format 'YYYY-MM-DD HH:MM'",
    )
    parser.add_argument("--location", default="", help="Event location (optional)")
    parser.add_argument("--description", default="", help="Event description (optional)")
    parser.add_argument(
        "--timezone", default="Asia/Jerusalem",
        help="Timezone name, e.g. 'Asia/Jerusalem', 'UTC', 'America/New_York' (default: Asia/Jerusalem)",
    )
    parser.add_argument(
        "--calendar-name", default=None,
        help="(Apple only) Name of the iCloud calendar to use. Defaults to primary.",
    )
    return parser.parse_args()


def parse_datetime(dt_str, tz_name):
    """Parse 'YYYY-MM-DD HH:MM' and attach timezone info."""
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(tz_name)
    except Exception:
        print(f"Error: Unknown timezone '{tz_name}'. Use a standard tz name like 'Asia/Jerusalem'.")
        sys.exit(1)

    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except ValueError:
        print(f"Error: Invalid datetime '{dt_str}'. Expected format: YYYY-MM-DD HH:MM")
        sys.exit(1)

    return dt.replace(tzinfo=tz)


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------

def _load_google_credentials():
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        print("Error: google-auth not installed. Run: pip3 install -r requirements.txt")
        sys.exit(1)

    if not GOOGLE_TOKEN_PATH.exists():
        print(
            "Error: Google token not found.\n"
            "Run setup_google_auth.py first to authenticate with Google."
        )
        sys.exit(1)

    token_data = json.loads(GOOGLE_TOKEN_PATH.read_text())

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data["refresh_token"],
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data.get("scopes", ["https://www.googleapis.com/auth/calendar.events"]),
    )

    # Refresh if expired
    if not creds.valid:
        creds.refresh(Request())
        # Persist the new access token
        token_data["token"] = creds.token
        GOOGLE_TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
        os.chmod(GOOGLE_TOKEN_PATH, stat.S_IRUSR | stat.S_IWUSR)

    return creds


def create_google_event(summary, start_dt, end_dt, location, description, tz_name):
    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("Error: google-api-python-client not installed. Run: pip3 install -r requirements.txt")
        sys.exit(1)

    creds = _load_google_credentials()
    service = build("calendar", "v3", credentials=creds)

    event_body = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": tz_name,
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": tz_name,
        },
    }

    result = service.events().insert(calendarId="primary", body=event_body).execute()
    return result.get("htmlLink", result.get("id", "created"))


# ---------------------------------------------------------------------------
# Apple Calendar (iCloud CalDAV)
# ---------------------------------------------------------------------------

def _get_apple_credentials():
    apple_id = os.getenv("APPLE_ID")
    app_password = os.getenv("APPLE_APP_PASSWORD")

    if not apple_id:
        apple_id = input("Enter your Apple ID (email): ").strip()
    if not app_password:
        print(
            "\nYou need an App-Specific Password for iCloud access.\n"
            "Generate one at: https://appleid.apple.com → Sign-In & Security → App-Specific Passwords\n"
        )
        import getpass
        app_password = getpass.getpass("Enter your iCloud App-Specific Password: ").strip()

    if not apple_id or not app_password:
        print("Error: Apple ID and App-Specific Password are required.")
        sys.exit(1)

    return apple_id, app_password


def create_apple_event(summary, start_dt, end_dt, location, description, calendar_name):
    try:
        import caldav
        from icalendar import Calendar, Event
    except ImportError:
        print("Error: caldav / icalendar not installed. Run: pip3 install -r requirements.txt")
        sys.exit(1)

    import uuid as uuid_mod

    apple_id, app_password = _get_apple_credentials()

    print("Connecting to iCloud CalDAV…")
    client = caldav.DAVClient(
        url="https://caldav.icloud.com/",
        username=apple_id,
        password=app_password,
    )

    try:
        principal = client.principal()
    except Exception as e:
        print(f"Error: Could not connect to iCloud CalDAV: {e}")
        print("Check that your Apple ID and App-Specific Password are correct.")
        sys.exit(1)

    calendars = principal.calendars()
    if not calendars:
        print("Error: No calendars found on this iCloud account.")
        sys.exit(1)

    # Select calendar by name, or fall back to first available
    target_cal = None
    if calendar_name:
        for cal in calendars:
            props = cal.get_properties([caldav.dav.DisplayName()])
            name = props.get("{DAV:}displayname", "")
            if name.lower() == calendar_name.lower():
                target_cal = cal
                break
        if target_cal is None:
            names = []
            for cal in calendars:
                props = cal.get_properties([caldav.dav.DisplayName()])
                names.append(props.get("{DAV:}displayname", "?"))
            print(f"Error: Calendar '{calendar_name}' not found. Available: {', '.join(names)}")
            sys.exit(1)
    else:
        target_cal = calendars[0]

    # Build iCalendar event
    cal = Calendar()
    cal.add("prodid", "-//Calendar Event Creator//EN")
    cal.add("version", "2.0")

    event = Event()
    event.add("uid", str(uuid_mod.uuid4()))
    event.add("summary", summary)
    event.add("dtstart", start_dt)
    event.add("dtend", end_dt)
    event.add("dtstamp", datetime.now(dt_timezone.utc))
    if location:
        event.add("location", location)
    if description:
        event.add("description", description)

    cal.add_component(event)

    target_cal.save_event(cal.to_ical().decode("utf-8"))
    return "created successfully"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    load_env()
    args = parse_args()

    start_dt = parse_datetime(args.start, args.timezone)
    end_dt = parse_datetime(args.end, args.timezone)

    if start_dt >= end_dt:
        print("Error: start time must be before end time.")
        sys.exit(1)

    print(f"\nCreating event in {args.calendar.capitalize()} Calendar…")
    print(f"  Title   : {args.summary}")
    print(f"  Start   : {start_dt.isoformat()}")
    print(f"  End     : {end_dt.isoformat()}")
    if args.location:
        print(f"  Location: {args.location}")

    if args.calendar == "google":
        link = create_google_event(
            summary=args.summary,
            start_dt=start_dt,
            end_dt=end_dt,
            location=args.location,
            description=args.description,
            tz_name=args.timezone,
        )
        print(f"\nEvent created: {link}")

    else:  # apple
        result = create_apple_event(
            summary=args.summary,
            start_dt=start_dt,
            end_dt=end_dt,
            location=args.location,
            description=args.description,
            calendar_name=args.calendar_name,
        )
        print(f"\nEvent {result}")


if __name__ == "__main__":
    main()
