# New Laptop Setup — Alex's Daily Alu Digest

Follow these steps **in order**. Do not skip ahead.
Estimated time: 10–15 minutes.

---

## STEP 1 — Check Python dependencies (do this FIRST)

Open Terminal and run:

```bash
python3 -c "import jinja2, httpx; print('✓ Dependencies OK')"
```

**If you see an error** (`ModuleNotFoundError`), install the missing packages:

```bash
pip3 install jinja2 httpx
```

Then re-run the check until you see `✓ Dependencies OK` before continuing.

---

## STEP 2 — Check gh CLI is authenticated

```bash
gh auth status
```

You should see `Logged in to github.com as alex-stad`.

**If not logged in**, run:

```bash
gh auth login
```

Choose: GitHub.com → HTTPS → authenticate via browser. Takes 30 seconds.

---

## STEP 3 — Clone the repository

```bash
mkdir -p "/Users/alexanderstadelmann/Claude Projects"
cd "/Users/alexanderstadelmann/Claude Projects"
gh repo clone alex-stad/alu-digest daily-alu-digest
```

Verify it worked:

```bash
ls "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/scripts/"
```

You should see: `generate_digest.py  render_html.py  send_email.py  test_send.py  update_archive_index.py`

---

## STEP 4 — Add the .env file (AirDrop)

The `.env` file contains the Resend API key. It is **not** on GitHub for security reasons.
You should have received it via AirDrop. Place it here:

```
/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/.env
```

Verify its contents:

```bash
cat "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/.env"
```

You should see: `RESEND_API_KEY=re_...`

---

## STEP 5 — Add the output folder (AirDrop, optional)

The `output/` folder contains yesterday's digest JSON, used by the no-repeat rule.
You should have received `digest_2026-03-26.json` via AirDrop. Place it here:

```
/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/output/digest_2026-03-26.json
```

If you don't have it, that's fine — the digest will still run, just without
the no-repeat check for the first day.

---

## STEP 6 — Configure git user

```bash
cd "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest"
git config user.name "Alex Stadelmann"
git config user.email "alex-stad@users.noreply.github.com"
```

---

## STEP 7 — Test the pipeline end-to-end

Run this to verify rendering and email delivery work:

```bash
cd "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest"
export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.local/bin:$PATH"
python3 scripts/test_send.py
```

Expected output:
```
Rendering HTML digest...
Preview saved to: .../output/preview_email.html
Sending test email to: stadelmann.alexander@gmail.com
Email sent successfully. ID: ...
Test passed. Check your inbox...
```

**Do not continue to Step 8 until you see a test email arrive in your Gmail.**

---

## STEP 8 — Re-create the scheduled task

The scheduled task must be re-created with the correct path for this laptop.
**Open Claude Code** in the project directory and paste this prompt:

```
Create a new scheduled task with the following settings:

taskId: alex-daily-alu-digest
description: Daily aluminium industry news digest for Alex Stadelmann (Novelis)
cronExpression: 30 13 * * 1-5
prompt: Read the file at "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/task_prompt.md" and execute every step described in the TASK PROMPT section. Follow all instructions exactly as written. Do not skip any step. The final step must be running the bash command in Step 8 which calls generate_digest.py — this is what actually sends the email. Do not consider the task complete until that command has run and printed a summary line starting with ✓ or ⚠.
```

Confirm the task appears in the Claude Code sidebar under "Scheduled".

---

## STEP 9 — Run a manual test digest

In Claude Code, trigger the scheduled task manually (click "Run now" in the sidebar),
or paste this into Claude Code:

```
Run the daily alu digest task now by reading and executing task_prompt.md at
"/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/task_prompt.md"
```

Verify:
- Email arrives at `stadelmann.alexander@gmail.com`
- Archive updates at https://alex-stad.github.io/alu-digest/
- Output file saved at `output/digest_YYYY-MM-DD.json`

---

## STEP 10 — Verify scheduled runs

The task is set to run at **7:30 AM CET (= 1:30 PM local Bangkok time)**, Monday–Friday.

Check the schedule is correct:
- In Claude Code sidebar → Scheduled Tasks → `alex-daily-alu-digest`
- Should show: `At 1:30 PM, Monday through Friday`

**Your Mac must be awake at 1:30 PM Bangkok time (= 7:30 AM CET) for the task to run.**

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: jinja2` | `pip3 install jinja2 httpx` |
| `RESEND_API_KEY not set` | Check `.env` file exists in project root |
| `gh auth` fails | Run `gh auth login` and authenticate in browser |
| Email not arriving | Check spam; verify Resend key in `.env` is correct |
| GitHub Pages not updating | Run `gh auth status` — may need `gh auth login` again |
| Scheduled task not running | Mac must be awake; check Claude Code sidebar for errors |

---

## File map (what everything does)

| File | Purpose |
|------|---------|
| `task_prompt.md` | The daily task instructions — edit to tune news queries or criteria |
| `config.yml` | Recipients, settings reference |
| `scripts/generate_digest.py` | Master pipeline: render → email → archive |
| `scripts/render_html.py` | Jinja2 HTML renderer |
| `scripts/send_email.py` | Resend API email sender |
| `scripts/test_send.py` | Send a test digest email |
| `templates/email_template.html` | Email HTML design |
| `templates/archive_template.html` | GitHub Pages archive design |
| `output/` | Daily digest files (gitignored — local only) |
| `.env` | API key (gitignored — never on GitHub) |

---

## Key URLs

- Archive: https://alex-stad.github.io/alu-digest/
- GitHub repo: https://github.com/alex-stad/alu-digest
- Resend dashboard: https://resend.com/emails
