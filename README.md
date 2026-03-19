# Alex's Daily Alu Digest

Automated daily aluminium industry news digest for Novelis — delivered to your inbox every weekday at 7 AM CET.

**Archive:** https://alex-stad.github.io/alu-digest/

## How it works

A Claude Code scheduled task runs each weekday morning and:
1. Searches 13 targeted queries across aluminium news sources (AlCircle, Fastmarkets, Reuters, Aluminium International Today, etc.)
2. Scores and selects the 5–8 most relevant stories for Novelis (flat-rolled products, competitors, recycling/ESG, trade policy, LME prices)
3. Writes 2-sentence English summaries for each story
4. Sends a formatted HTML email to both recipients via Resend
5. Publishes the digest to the GitHub Pages archive

## Files

| File | Purpose |
|------|---------|
| `task_prompt.md` | The scheduled task instructions — edit to tune search queries or criteria |
| `config.yml` | Recipients, settings |
| `templates/email_template.html` | HTML email design |
| `templates/archive_template.html` | GitHub Pages archive design |
| `scripts/render_html.py` | Jinja2 HTML renderer |
| `scripts/send_email.py` | Resend API email sender |
| `scripts/test_send.py` | Send a test digest email |
| `scripts/update_archive_index.py` | Update the GitHub Pages archive index |

## Tuning

Edit `task_prompt.md` to:
- Add or remove search queries
- Adjust relevance scoring criteria
- Change the number of articles selected
- Modify summary style

## Requirements

- Python 3.10+
- `pip3 install jinja2 httpx`
- `RESEND_API_KEY` environment variable
