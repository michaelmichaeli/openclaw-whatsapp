# OpenClaw WhatsApp Bot Setup

זה repo עם קונפיגורציה והוראות להפעלת OpenClaw עם WhatsApp integration.

## עבור סשן חדש במחשב אחר:

### 1. שכפל את הקבצים
```bash
git clone <REPO_URL>
cd openclaw-setup
```

### 2. עדכן את ה-API Keys
העתק את `.env.example` ל-`.env` והוסף את ה-API keys שלך:
```bash
cp .env.example .env
```

ערוך את `.env` עם ה-keys שלך:
- `ANTHROPIC_API_KEY` - מ-Anthropic console
- `OPENCODE_API_KEY` - מ-OpenCode
- `OPENCLAW_GATEWAY_TOKEN` - Token עבור גישה מרחוק

### 3. העתק את הקונפיגורציה לשרת
```bash
scp -o StrictHostKeyChecking=no openclaw.json root@204.168.251.210:/opt/openclaw/openclaw.json
scp -o StrictHostKeyChecking=no auth-profiles.json root@204.168.251.210:/opt/openclaw/.state/agents/main/agent/auth-profiles.json
```

### 4. הפעל את OpenClaw בשרת
```bash
ssh -o StrictHostKeyChecking=no root@204.168.251.210 "systemctl enable openclaw && systemctl start openclaw"
```

### 5. בדוק את הסטטוס
```bash
ssh -o StrictHostKeyChecking=no root@204.168.251.210 "systemctl status openclaw"
```

### 6. גישה דרך SSH Tunnel
```bash
ssh -L 18789:127.0.0.1:18789 -N -f root@204.168.251.210
```

ואז פתח ב-browser: `http://localhost:18789`

## IP של השרת
- Host: `204.168.251.210`
- Port: `18789`
- Gateway Token: זה שהגדרת ב-.env

## הערות חשובות
- WhatsApp משבית כרגע (לא משדרת)
- Telegram משבית כרגע (לא משדרת)
- המודל הנוכחי: `openai/opencode`
