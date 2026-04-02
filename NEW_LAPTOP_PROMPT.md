# New Laptop Setup Prompt

Copy everything between the triple backticks and paste it into Claude Code on the new laptop.
That's all you need to do.

---

```
Set up my Daily Alu Digest project on this laptop by running these steps automatically using bash commands. Do not ask me to do anything manually — execute everything yourself.

STEP 1 — Install Python dependencies if missing
Run:
  python3 -c "import jinja2, httpx" 2>/dev/null || pip3 install jinja2 httpx
Then confirm both are importable.

STEP 2 — Authenticate gh CLI if needed
Run: gh auth status
If not authenticated, run: gh auth login --web

STEP 3 — Clone the repo
Run:
  mkdir -p "/Users/alexanderstadelmann/Claude Projects"
  cd "/Users/alexanderstadelmann/Claude Projects"
  gh repo clone alex-stad/alu-digest daily-alu-digest

STEP 4 — Move AirDropped files from Downloads
Two files were AirDropped and are sitting in ~/Downloads. Find and move them automatically:

  # Move .env to project root
  find ~/Downloads -maxdepth 2 -name ".env" | head -1 | xargs -I{} cp {} "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/.env"

  # Create output folder and move digest JSON
  mkdir -p "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/output"
  find ~/Downloads -maxdepth 2 -name "digest_*.json" | head -1 | xargs -I{} cp {} "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/output/"

Verify both files landed correctly:
  cat "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/.env" | grep -c "BUTTONDOWN_API_KEY" && echo ".env OK"
  ls "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/output/"digest_*.json && echo "digest JSON OK"

If either file is missing, search more broadly: find ~ -maxdepth 4 -name ".env" -o -name "digest_*.json" 2>/dev/null

STEP 5 — Configure git
Run:
  cd "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest"
  git config user.name "Alex Stadelmann"
  git config user.email "alex-stad@users.noreply.github.com"
  gh auth setup-git

STEP 6 — Run the pipeline test
Run:
  cd "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest"
  export PATH="/usr/local/bin:/opt/homebrew/bin:$HOME/.local/bin:$PATH"
  python3 scripts/test_send.py

Confirm output contains "Email sent successfully". If it fails, report the exact error and stop.

STEP 7 — Create the scheduled task
Create a Claude Code scheduled task with these exact parameters:
  taskId: alex-daily-alu-digest
  description: Daily aluminium industry news digest for Alex Stadelmann (Novelis)
  cronExpression: 30 13 * * 1-5
  prompt: Read the file at "/Users/alexanderstadelmann/Claude Projects/daily-alu-digest/task_prompt.md" and execute every step described in the TASK PROMPT section. Follow all instructions exactly as written. Do not skip any step. The final step must be running the bash command in Step 8 which calls generate_digest.py — this is what actually sends the email. Do not consider the task complete until that command has run and printed a summary line starting with ✓ or ⚠.

STEP 8 — Print a final confirmation summary
Print:
  ✓ Setup complete
  - Python deps: jinja2, httpx installed
  - .env: present at project root (BUTTONDOWN_API_KEY loaded)
  - output/ digest JSON: present
  - git configured: Alex Stadelmann
  - pipeline test: draft created in Buttondown
  - scheduled task: alex-daily-alu-digest, runs Mon-Fri at 13:30 local (= 07:30 CET)
  - next run: [show next scheduled time]
```
