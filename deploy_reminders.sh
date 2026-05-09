#!/bin/bash
# One-time setup: Apple Reminders via CalDAV on the OpenClaw server
# Run this on the server: bash deploy_reminders.sh
set -e

REPO_DIR="/opt/openclaw-whatsapp"
ENV_FILE="$REPO_DIR/.env"

echo "=== OpenClaw Apple Reminders Setup ==="
echo ""

# 1. Clone or update repo
if [ -d "$REPO_DIR/.git" ]; then
    echo "Updating repo..."
    git -C "$REPO_DIR" pull origin claude/calendar-event-creator-fNiJH
else
    echo "Cloning repo..."
    git clone -b claude/calendar-event-creator-fNiJH \
        https://github.com/michaelmichaeli/openclaw-whatsapp.git "$REPO_DIR"
fi

# 2. Install Python deps
echo ""
echo "Installing dependencies..."
pip3 install -q caldav icalendar python-dotenv

# 3. Write .env with Apple credentials
echo ""
echo "Writing credentials..."
cat > "$ENV_FILE" << 'ENVEOF'
APPLE_ID=michaelmichaeli888@gmail.com
APPLE_APP_PASSWORD=yphy-dnem-oiiw-bwjo
ENVEOF
chmod 600 "$ENV_FILE"

# 4. Test connection + list reminder lists
echo ""
echo "Testing iCloud CalDAV connection..."
cd "$REPO_DIR"
python3 calendar_creator/add_reminder.py --list-lists

echo ""
echo "=== Adding test reminder ==="
python3 calendar_creator/add_reminder.py \
    --title "✅ בדיקת חיבור - מחק אותי" \
    --list "רשימת קניות"

echo ""
echo "SUCCESS! Agent can now add to Apple Reminders."
echo ""
echo "Usage:"
echo "  python3 $REPO_DIR/calendar_creator/add_reminder.py --title \"פריט\" --list \"רשימת קניות\""
