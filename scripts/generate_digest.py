#!/usr/bin/env python3
"""
generate_digest.py — master pipeline runner.

Called by the scheduled task after Claude has assembled digest_data JSON.
Handles: rendering, email send, local save, GitHub Pages archive update.

Usage:
    python3 scripts/generate_digest.py --json-file /path/to/digest.json
    python3 scripts/generate_digest.py --json '{"date": "...", "articles": [...]}'
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.render_html import render_email, render_archive_page
from scripts.send_email import send_digest


def _load_env() -> None:
    """Load .env file from project root into os.environ (no external deps)."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env()

BUTTONDOWN_API_KEY = os.environ.get("BUTTONDOWN_API_KEY", "")
if not BUTTONDOWN_API_KEY:
    print("[ERROR] BUTTONDOWN_API_KEY not set. Add it to .env in the project root.")
    sys.exit(1)

# Auto-detect gh CLI: Homebrew (/usr/local/bin or /opt/homebrew/bin) or manual install
def _find_gh() -> str:
    for candidate in ["/usr/local/bin/gh", "/opt/homebrew/bin/gh",
                      str(Path.home() / ".local/bin/gh")]:
        if Path(candidate).exists():
            return candidate
    return "gh"  # fall back to PATH

GH_PATH = _find_gh()


def _update_dedup_history(out_dir: Path, date_slug: str, digest_data: dict) -> None:
    """
    Maintain output/dedup_history.json — a slim list of {date, title} entries
    for the last 14 days. Used by Claude for dedup checks instead of reading
    full digest JSON files (~5,600 tokens → ~1,400 tokens).
    """
    history_file = out_dir / "dedup_history.json"
    entries = []
    if history_file.exists():
        try:
            entries = json.loads(history_file.read_text(encoding="utf-8"))
        except Exception:
            entries = []

    # Remove today's entries (in case of re-run) and entries older than 14 days
    cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    entries = [e for e in entries
               if e.get("date") != date_slug and e.get("date", "") >= cutoff]

    # Prepend today's articles (newest first)
    new_entries = [
        {"date": date_slug, "title": art.get("title", "")}
        for art in digest_data.get("articles", [])
    ]
    entries = new_entries + entries

    history_file.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[OK] dedup_history.json updated ({len(entries)} entries)")


def run(digest_data: dict, date_slug: str = None) -> bool:
    # Fix 6: accept an externally-provided date_slug so the job's date and the
    # script's date are always consistent (guards against midnight crossing).
    if date_slug is None:
        date_slug = datetime.now().strftime("%Y-%m-%d")
    out_dir = REPO_ROOT / "output"
    out_dir.mkdir(exist_ok=True)

    errors = []

    # ── 1. Render ──────────────────────────────────────────────────────────
    try:
        html = render_email(digest_data)
        email_path = out_dir / f"{date_slug}.html"
        email_path.write_text(html, encoding="utf-8")
        print(f"[OK] Digest rendered → {email_path}")
    except Exception as e:
        print(f"[ERROR] Render failed: {e}")
        return False  # fatal — can't send without HTML

    # ── 2. Send email (Fix 3: retry up to 3 times on transient failures) ──────
    import time as _time
    os.environ["BUTTONDOWN_API_KEY"] = BUTTONDOWN_API_KEY
    subject = f"Alex's Daily Alu Digest — {digest_data['date']}"
    email_sent = False
    for attempt in range(1, 4):
        try:
            if send_digest(html, subject):
                email_sent = True
                break
            print(f"[WARN] Email attempt {attempt}/3 returned False"
                  f"{' — retrying in 10s' if attempt < 3 else ' — giving up'}")
        except Exception as e:
            print(f"[WARN] Email attempt {attempt}/3 exception: {e}"
                  f"{' — retrying in 10s' if attempt < 3 else ' — giving up'}")
        if attempt < 3:
            _time.sleep(10)
    if not email_sent:
        errors.append("Email failed after 3 attempts")

    # ── 3. Save archive page ───────────────────────────────────────────────
    try:
        archive_html = render_archive_page(digest_data, date_slug)
        archive_path = out_dir / f"archive_{date_slug}.html"
        archive_path.write_text(archive_html, encoding="utf-8")
        print(f"[OK] Archive page saved → {archive_path}")
    except Exception as e:
        errors.append(f"Archive render: {e}")

    # ── 4. Push to GitHub Pages ────────────────────────────────────────────
    try:
        _push_to_gh_pages(date_slug, digest_data)
    except Exception as e:
        errors.append(f"GitHub Pages push: {e}")

    # ── 4b. Update slim dedup history ─────────────────────────────────────
    try:
        _update_dedup_history(out_dir, date_slug, digest_data)
    except Exception as e:
        errors.append(f"Dedup history update: {e}")

    # ── 5. Summary ─────────────────────────────────────────────────────────
    n = len(digest_data.get("articles", []))
    lme = digest_data.get("lme_price", "N/A")
    ecdp = digest_data.get("ecdp_price", "N/A")
    cats = ", ".join(sorted({a["category"] for a in digest_data.get("articles", [])}))
    print(f"\n{'✓' if not errors else '⚠'} Alex's Daily Alu Digest — {digest_data['date']}")
    print(f"  Articles : {n} ({cats})")
    print(f"  LME      : {lme}   ECDP: {ecdp}")
    print(f"  Email    : {'sent to subscribers' if not errors else 'see errors'} via Buttondown")
    print(f"  Archive  : https://alex-stad.github.io/alu-digest/")
    if errors:
        print(f"  ERRORS   : {'; '.join(errors)}")
    return not errors


def _push_to_gh_pages(date_slug: str, digest_data: dict):
    """
    Updates the gh-pages branch using a git worktree — never touches the main
    working directory, so no stashing, no branch switching, no data loss.
    """
    import tempfile, shutil

    year, month, day = date_slug.split("-")
    repo = REPO_ROOT
    out_dir = repo / "output"
    archive_src = out_dir / f"archive_{date_slug}.html"

    if not archive_src.exists():
        raise FileNotFoundError(f"Archive source not found: {archive_src}")

    env = os.environ.copy()
    # Include common install paths for git: Mac (Homebrew) + Linux (GitHub Actions)
    env["PATH"] = (
        f"/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:"
        f"/Library/Frameworks/Python.framework/Versions/3.14/bin:"
        f"/Library/Frameworks/Python.framework/Versions/3.13/bin:"
        f"/Library/Frameworks/Python.framework/Versions/3.12/bin:"
        f"{Path.home()}/.local/bin:{env.get('PATH', '')}"
    )

    def git(*args, cwd=repo):
        result = subprocess.run(["git"] + list(args), cwd=cwd, env=env,
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout.strip()

    worktree = Path(tempfile.mkdtemp(prefix="alu-digest-ghpages-"))
    try:
        git("fetch", "origin", "gh-pages")
        git("worktree", "add", str(worktree), "origin/gh-pages")

        # Copy archive page into the worktree
        dest_dir = worktree / year / month
        dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / f"{day}.html").write_text(
            archive_src.read_text(encoding="utf-8"), encoding="utf-8"
        )

        # Update entries.json and index.html inside the worktree
        _update_entries(worktree, date_slug, digest_data)

        git("add", "-A", cwd=worktree)
        try:
            git("commit", "-m", f"Digest {date_slug}", cwd=worktree)
        except RuntimeError:
            print("[OK] Nothing new to commit to gh-pages")
            return
        # Fix 9: retry push once after rebasing in case of concurrent push
        try:
            git("push", "origin", "HEAD:gh-pages", cwd=worktree)
        except RuntimeError:
            print("[WARN] gh-pages push failed — fetching latest and retrying once")
            git("fetch", "origin", "gh-pages")
            git("rebase", "origin/gh-pages", cwd=worktree)
            git("push", "origin", "HEAD:gh-pages", cwd=worktree)
        print("[OK] GitHub Pages updated")

    finally:
        try:
            git("worktree", "remove", "--force", str(worktree))
        except Exception:
            shutil.rmtree(worktree, ignore_errors=True)


def _update_entries(base: Path, date_slug: str, digest_data: dict):
    from scripts.render_html import render_archive_index
    from scripts.update_archive_index import date_slug_to_display

    entries_file = base / "entries.json"
    entries = []
    if entries_file.exists():
        try:
            entries = json.loads(entries_file.read_text())
        except Exception:
            entries = []

    entries = [e for e in entries if e.get("date_slug") != date_slug]
    lead = ""
    if digest_data.get("articles"):
        lead = digest_data["articles"][0].get("title", "")[:80]

    entries.insert(0, {
        "date_slug": date_slug,
        "date_display": date_slug_to_display(date_slug),
        "lead_headline": lead,
    })
    entries = entries[:90]
    entries_file.write_text(json.dumps(entries, indent=2, ensure_ascii=False))

    index_html = render_archive_index(entries)
    (base / "index.html").write_text(index_html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--json-file", help="Path to JSON file with digest data")
    group.add_argument("--json", help="JSON string with digest data")
    # Fix 6: accept date slug from caller so script and workflow stay in sync
    parser.add_argument("--date-slug", help="Date slug YYYY-MM-DD (defaults to today)")
    args = parser.parse_args()

    if args.json_file:
        data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    else:
        data = json.loads(args.json)

    ok = run(data, date_slug=args.date_slug)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
