#!/usr/bin/env python3
"""
Apple Reminders adder via iCloud CalDAV.

Usage (CLI):
  python3 add_reminder.py --title "קנה חלב" --list "רשימת קניות"
  python3 add_reminder.py --title "לקרוא מייל" --due "2026-05-15"
  python3 add_reminder.py --list-lists   # show all reminder lists

Requires in .env:
  APPLE_ID=your@apple.com
  APPLE_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
  (generate at appleid.apple.com → Sign-In & Security → App-Specific Passwords)
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    print("Error: python-dotenv not installed. Run: pip3 install -r requirements.txt")
    sys.exit(1)

ENV_PATH = Path(__file__).parent.parent / ".env"


def load_env():
    if ENV_PATH.exists():
        load_dotenv(dotenv_path=ENV_PATH)


def get_credentials() -> tuple[str, str]:
    apple_id = os.getenv("APPLE_ID", "").strip()
    app_password = os.getenv("APPLE_APP_PASSWORD", "").strip()
    if not apple_id or not app_password:
        print(
            "Error: APPLE_ID and APPLE_APP_PASSWORD must be set in .env\n"
            "Generate an App-Specific Password at:\n"
            "  appleid.apple.com → Sign-In & Security → App-Specific Passwords"
        )
        sys.exit(1)
    return apple_id, app_password


def connect_caldav():
    try:
        import caldav
    except ImportError:
        print("Error: caldav not installed. Run: pip3 install caldav icalendar")
        sys.exit(1)

    apple_id, app_password = get_credentials()

    client = caldav.DAVClient(
        url="https://caldav.icloud.com/",
        username=apple_id,
        password=app_password,
    )
    try:
        principal = client.principal()
    except Exception as e:
        print(f"Error: Could not connect to iCloud CalDAV: {e}")
        print("Check that APPLE_ID and APPLE_APP_PASSWORD are correct.")
        sys.exit(1)
    return principal


def get_reminder_lists(principal) -> list[dict]:
    """Return all CalDAV collections that support VTODO (i.e. Reminder lists)."""
    lists = []
    try:
        calendars = principal.calendars()
    except Exception as e:
        print(f"Error fetching calendars: {e}")
        sys.exit(1)

    for cal in calendars:
        try:
            components = cal.get_supported_components()
        except Exception:
            components = []
        if "VTODO" in components:
            try:
                name = cal.name or cal.get_display_name()
            except Exception:
                name = None
            lists.append({"name": name or str(cal.url), "cal": cal})

    return lists


def find_list(principal, list_name: str | None):
    reminder_lists = get_reminder_lists(principal)

    if not reminder_lists:
        print("Error: No reminder lists found on this iCloud account.")
        print("Make sure Reminders is enabled in iCloud settings.")
        sys.exit(1)

    if list_name is None:
        return reminder_lists[0]["cal"], reminder_lists[0]["name"]

    for entry in reminder_lists:
        if entry["name"].lower() == list_name.lower():
            return entry["cal"], entry["name"]

    names = [e["name"] for e in reminder_lists]
    print(f"Error: List '{list_name}' not found.")
    print(f"Available lists: {', '.join(names)}")
    sys.exit(1)


def add_reminder(title: str, list_name: str | None = None, due_date: str | None = None, notes: str = "") -> str:
    """
    Add a reminder to an iCloud Reminders list.
    Returns the name of the list it was added to.
    """
    try:
        import caldav
        from icalendar import Calendar, Todo
    except ImportError:
        print("Error: caldav / icalendar not installed. Run: pip3 install caldav icalendar")
        sys.exit(1)

    principal = connect_caldav()
    target_cal, resolved_name = find_list(principal, list_name)

    # Build VTODO
    cal = Calendar()
    cal.add("prodid", "-//OpenClaw Reminders//EN")
    cal.add("version", "2.0")

    todo = Todo()
    todo.add("uid", str(uuid.uuid4()))
    todo.add("summary", title)
    todo.add("dtstamp", datetime.utcnow())
    todo.add("status", "NEEDS-ACTION")

    if notes:
        todo.add("description", notes)

    if due_date:
        try:
            due_dt = datetime.strptime(due_date, "%Y-%m-%d")
            todo.add("due", due_dt.date())
        except ValueError:
            print(f"Warning: Could not parse due date '{due_date}', expected YYYY-MM-DD. Skipping due date.")

    cal.add_component(todo)

    target_cal.save_todo(cal.to_ical().decode("utf-8"))
    return resolved_name


def main():
    load_env()

    parser = argparse.ArgumentParser(
        description="Add a reminder to Apple Reminders via iCloud CalDAV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--title", help="Reminder title")
    parser.add_argument("--list", dest="list_name", default=None, help="Reminder list name (default: first available)")
    parser.add_argument("--due", default=None, help="Due date in YYYY-MM-DD format (optional)")
    parser.add_argument("--notes", default="", help="Notes / description (optional)")
    parser.add_argument("--list-lists", action="store_true", help="Show all available reminder lists and exit")

    args = parser.parse_args()

    if args.list_lists:
        principal = connect_caldav()
        reminder_lists = get_reminder_lists(principal)
        if not reminder_lists:
            print("No reminder lists found.")
        else:
            print("Available reminder lists:")
            for entry in reminder_lists:
                print(f"  - {entry['name']}")
        return

    if not args.title:
        parser.error("--title is required (unless using --list-lists)")

    print(f"Adding reminder: '{args.title}'" + (f" → list: '{args.list_name}'" if args.list_name else ""))

    resolved = add_reminder(
        title=args.title,
        list_name=args.list_name,
        due_date=args.due,
        notes=args.notes,
    )

    print(f"✓ Added to '{resolved}'")


if __name__ == "__main__":
    main()
