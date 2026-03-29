# New Laptop Setup Prompt

Copy and paste the block below into Claude Code on the new laptop.
Before you do, make sure you have completed Steps 1–6 of SETUP.md manually
(dependencies, gh auth, git clone, .env file, output folder, git config).

---

## PASTE THIS INTO CLAUDE CODE:

```
I am setting up a project called "Alex's Daily Alu Digest" on a new laptop.
The project has already been cloned from GitHub to:
/Users/alexanderstadelmann/Claude Projects/daily-alu-digest

Please do the following steps in order:

STEP 1 — Verify dependencies
Run this and confirm it succeeds:
  python3 -c "import jinja2, httpx; print('Dependencies OK')"
If it fails, run: pip3 install jinja2 httpx

STEP 2 — Verify .env file
Confirm the file exists at:
  /Users/alexanderstadelmann/Claude Projects/daily-alu-digest/.env
And that it contains RESEND_API_KEY=re_...
Do NOT print the key value, just confirm it is present and non-empty.

STEP 3 — Run the pipeline test
Run:
  cd "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest"
  export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.local/bin:$PATH"
  python3 scripts/test_send.py
Confirm a test email was sent to stadelmann.alexander@gmail.com.
Stop and report any errors before continuing.

STEP 4 — Create the scheduled task
Create a new Claude Code scheduled task with these exact settings:
  taskId: alex-daily-alu-digest
  description: Daily aluminium industry news digest for Alex Stadelmann (Novelis)
  cronExpression: 30 13 * * 1-5
  prompt: Read the file at "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/task_prompt.md" and execute every step described in the TASK PROMPT section. Follow all instructions exactly as written. Do not skip any step. The final step must be running the bash command in Step 8 which calls generate_digest.py — this is what actually sends the email. Do not consider the task complete until that command has run and printed a summary line starting with ✓ or ⚠.

STEP 5 — Confirm setup
Print a summary confirming:
- Dependencies installed: jinja2, httpx
- .env file present with RESEND_API_KEY
- test_send.py succeeded
- Scheduled task created: alex-daily-alu-digest, cron 30 13 * * 1-5
- Next scheduled run time
```
