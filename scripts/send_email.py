#!/usr/bin/env python3
"""
Sends the digest HTML via Buttondown API (newsletter to all subscribers).
Reads BUTTONDOWN_API_KEY from environment variable.
"""

import os
import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def send_digest(html_body: str, subject: str) -> bool:
    """
    Send the digest as a Buttondown newsletter email to all subscribers.
    Returns True on success, False on failure.
    """
    api_key = os.environ.get("BUTTONDOWN_API_KEY", "").strip()
    if not api_key:
        print("ERROR: BUTTONDOWN_API_KEY environment variable not set.")
        return False

    try:
        import httpx
    except ImportError:
        print("httpx not installed. Run: pip3 install httpx")
        return False

    payload = {
        "subject": subject,
        "body": html_body,
        "status": "about_to_send",
    }

    try:
        response = httpx.post(
            "https://api.buttondown.com/v1/emails",
            json=payload,
            headers={
                "Authorization": f"Token {api_key}",
                "X-Buttondown-Live-Dangerously": "true",
            },
            timeout=30,
        )
        if response.status_code in (200, 201):
            result = response.json()
            print(f"Newsletter sent successfully. ID: {result.get('id', 'unknown')}")
            return True
        else:
            print(f"ERROR sending newsletter (HTTP {response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"ERROR sending newsletter: {e}")
        return False


def send_draft(html_body: str, subject: str) -> bool:
    """
    Create a Buttondown draft (not sent to subscribers). Useful for testing.
    Returns True on success, False on failure.
    """
    api_key = os.environ.get("BUTTONDOWN_API_KEY", "").strip()
    if not api_key:
        print("ERROR: BUTTONDOWN_API_KEY environment variable not set.")
        return False

    try:
        import httpx
    except ImportError:
        print("httpx not installed. Run: pip3 install httpx")
        return False

    payload = {
        "subject": subject,
        "body": html_body,
        "status": "draft",
    }

    try:
        response = httpx.post(
            "https://api.buttondown.com/v1/emails",
            json=payload,
            headers={"Authorization": f"Token {api_key}"},
            timeout=30,
        )
        if response.status_code in (200, 201):
            result = response.json()
            print(f"Draft created successfully. ID: {result.get('id', 'unknown')}")
            return True
        else:
            print(f"ERROR creating draft (HTTP {response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"ERROR creating draft: {e}")
        return False


if __name__ == "__main__":
    # Quick test: create a draft email (does NOT send to subscribers)
    api_key = os.environ.get("BUTTONDOWN_API_KEY", "")
    if not api_key:
        # Try loading from .env
        env_file = REPO_ROOT / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())
        api_key = os.environ.get("BUTTONDOWN_API_KEY", "")

    if not api_key:
        print("Usage: BUTTONDOWN_API_KEY=... python3 scripts/send_email.py")
        sys.exit(1)

    test_html = "<h1>Test</h1><p>Alu Digest email test — if you see this, sending works!</p>"
    success = send_draft(test_html, "Alu Digest — Send Test")
    sys.exit(0 if success else 1)
