#!/usr/bin/env python3
"""
Sends the digest HTML via Resend API.
Reads RESEND_API_KEY from environment variable.
"""

import os
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def send_digest(html_body: str, subject: str, recipients: list[str]) -> bool:
    """
    Send the digest email via Resend API.
    Returns True on success, False on failure.
    """
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        print("ERROR: RESEND_API_KEY environment variable not set.")
        return False

    try:
        import httpx
    except ImportError:
        print("httpx not installed. Run: pip3 install httpx")
        return False

    payload = {
        "from": "Alex's Daily Alu Digest <onboarding@resend.dev>",
        "to": recipients,
        "subject": subject,
        "html": html_body,
    }

    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
        if response.status_code == 200:
            result = response.json()
            print(f"Email sent successfully. ID: {result.get('id', 'unknown')}")
            return True
        else:
            print(f"ERROR sending email (HTTP {response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"ERROR sending email: {e}")
        return False


if __name__ == "__main__":
    # Quick test: send a minimal test email
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        print("Usage: RESEND_API_KEY=re_... python3 scripts/send_email.py")
        sys.exit(1)

    test_html = "<h1>Test</h1><p>Alu Digest email test — if you see this, sending works!</p>"
    success = send_digest(test_html, "Alu Digest — Send Test", ["stadelmann.alexander@gmail.com"])
    sys.exit(0 if success else 1)
