#!/usr/bin/env python3
"""
Sends the eToro portfolio summary via WhatsApp (CallMeBot).
Called by the etoro-stock skill after Claude composes the full message.

Usage:
  python3 send_etoro.py "message text here"
  echo "message" | python3 send_etoro.py
"""

import os
import sys
import requests


CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"


def send(text):
    phone = os.environ.get("CALLMEBOT_PHONE", "")
    key = os.environ.get("CALLMEBOT_KEY", "")
    if not phone or not key:
        print(
            "WhatsApp not configured. Add to ~/.claude/settings.json under 'env':\n"
            '  "CALLMEBOT_PHONE": "your_phone_number"\n'
            '  "CALLMEBOT_KEY":   "your_callmebot_apikey"\n'
            "Get a free key: message +34 644 63 67 97 on WhatsApp with "
            "'I allow callmebot to send me messages'"
        )
        return
    r = requests.get(
        CALLMEBOT_URL,
        params={"phone": phone, "text": text, "apikey": key},
        timeout=15,
    )
    if r.status_code == 200:
        print("WhatsApp notification sent ✅")
    else:
        print(f"WhatsApp send failed: HTTP {r.status_code} — {r.text[:100]}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    else:
        msg = sys.stdin.read().strip()
    if msg:
        send(msg)
    else:
        print("No message to send.")
