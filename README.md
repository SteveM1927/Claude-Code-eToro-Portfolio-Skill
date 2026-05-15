# eToro Portfolio Skill for Claude Code

A Claude Code skill that fetches your live eToro portfolio, adds news context for each holding, surfaces growth opportunities, and sends the full briefing to WhatsApp.

## What it does

- Fetches real-time portfolio data via the eToro API (positions, daily P&L, unrealized P&L)
- Searches for news on each holding and the broader market
- Composes a formatted briefing and displays it in chat
- Optionally sends the briefing to your WhatsApp via CallMeBot

## Installation

Copy the skill into your Claude Code skills directory:

```bash
cp -r . ~/.claude/skills/etoro-stock
```

Or clone directly:

```bash
git clone <repo-url> ~/.claude/skills/etoro-stock
```

Install the Python dependency:

```bash
pip install requests
```

### Allow the scripts to run without permission prompts

Add the following to `~/.claude/settings.json` under `permissions.allow` (replace the path with your actual install location):

```json
{
  "permissions": {
    "allow": [
      "Bash(python3 /home/YOUR_USER/.claude/skills/etoro-stock/scripts/*)",
      "Bash(cat /tmp/etoro_msg.txt*)",
      "Bash(cat > /tmp/etoro_msg.txt*)",
      "Write(/tmp/etoro_msg.txt)"
    ]
  }
}
```

## Setup

Add the following to `~/.claude/settings.json` under the `env` key:

```json
{
  "env": {
    "ETORO_API_KEY": "your_etoro_api_key",
    "ETORO_USER_KEY": "your_etoro_user_key",
    "CALLMEBOT_PHONE": "your_phone_number_with_country_code",
    "CALLMEBOT_KEY": "your_callmebot_apikey"
  }
}
```

### Getting your eToro API keys

1. Log in to eToro web
2. Go to **Settings → Trading → API Keys**
3. Click **Create New Key**
4. Select **Real** environment and **Read** permission
5. Copy the API Key and User Key

### Getting your CallMeBot API key (WhatsApp)

1. Add `+34 644 63 67 97` to your WhatsApp contacts
2. Send the message: `I allow callmebot to send me messages`
3. You'll receive your API key by reply within a few minutes

> WhatsApp delivery is optional — if `CALLMEBOT_PHONE` / `CALLMEBOT_KEY` are not set, the briefing is still displayed in chat.

## Usage

Just ask Claude about your portfolio:

- "How is my eToro portfolio doing?"
- "Am I up or down today?"
- "Check my investments"
- "Portfolio update"
