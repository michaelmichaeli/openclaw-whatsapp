#!/bin/bash

# OpenClaw Setup Script
# זה script לכך שלא תצטרך להריץ את כל הפקודות בעצמך

set -e

echo "🔧 OpenClaw Setup"
echo "================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "בואי ליצור .env:"
    cp .env.example .env
    echo "✅ .env created from .env.example"
    echo "⚠️  עדכן את .env עם ה-API keys שלך!"
    exit 1
fi

# Get the gateway token from .env
GATEWAY_TOKEN=$(grep "OPENCLAW_GATEWAY_TOKEN=" .env | cut -d'=' -f2)

if [ -z "$GATEWAY_TOKEN" ] || [ "$GATEWAY_TOKEN" = "sk-openclaw-YOUR_TOKEN_HERE" ]; then
    echo "❌ OPENCLAW_GATEWAY_TOKEN not configured in .env"
    exit 1
fi

# Update openclaw.json with the correct token
echo "🔐 Updating gateway token in openclaw.json..."
sed -i '' "s|sk-openclaw-2947b9cb5aef4cd30a72100e9013c62ee4884b1744e7514b8daadf442397a4d8|$GATEWAY_TOKEN|g" openclaw.json

# Update auth-profiles.json with API keys
echo "🔑 Updating API keys in auth-profiles.json..."
ANTHROPIC_KEY=$(grep "ANTHROPIC_API_KEY=" .env | cut -d'=' -f2)
OPENCODE_KEY=$(grep "OPENCODE_API_KEY=" .env | cut -d'=' -f2)

sed -i '' "s|sk-ant-api03-YOUR_ANTHROPIC_KEY_HERE|$ANTHROPIC_KEY|g" auth-profiles.json
sed -i '' "s|sk-YOUR_OPENCODE_KEY_HERE|$OPENCODE_KEY|g" auth-profiles.json

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Upload files to server:"
echo "   scp -o StrictHostKeyChecking=no openclaw.json root@204.168.251.210:/opt/openclaw/"
echo "   scp -o StrictHostKeyChecking=no auth-profiles.json root@204.168.251.210:/opt/openclaw/.state/agents/main/agent/"
echo ""
echo "2. Start OpenClaw:"
echo "   ssh -o StrictHostKeyChecking=no root@204.168.251.210 'systemctl restart openclaw'"
echo ""
echo "3. Connect via SSH tunnel:"
echo "   ssh -L 18789:127.0.0.1:18789 -N -f root@204.168.251.210"
echo ""
echo "4. Open in browser:"
echo "   http://localhost:18789"
