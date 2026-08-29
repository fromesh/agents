# morning-briefing

Gathers weather, today's Google Calendar events, and news headlines; asks Claude
to synthesize a short briefing; emails it to you via Gmail. Designed to run
unattended every morning via cron.

## What it demonstrates

The other common agent shape (compare to `../example-agent`, which is a
tool-use loop): gather context from a few sources up front, hand it to the
model **once** to synthesize, then take a real-world action (send email) with
the result. No back-and-forth — just gather -> synthesize -> act.

## One-time setup

1. Follow the Google Cloud steps to get `credentials.json` (project + enable
   Gmail API & Calendar API + OAuth consent screen + Desktop app OAuth client).
   Put the downloaded file in this folder as `credentials.json`.
   **Never commit this file** — it's already in `.gitignore`.

2. Create a virtualenv and install deps:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set environment variables (put these in your shell profile, or a local
   `.env` you source before running):
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   export BRIEFING_TO_EMAIL=you@gmail.com
   export BRIEFING_LAT=34.05      # optional, defaults to Los Angeles
   export BRIEFING_LON=-118.24    # optional
   export BRIEFING_NEWS_FEED=https://feeds.bbci.co.uk/news/rss.xml  # optional
   ```

4. Run it once manually:
   ```bash
   python agent.py
   ```
   This opens a browser to authorize Gmail + Calendar access. After you
   approve, it saves `token.json` (also gitignored) so every future run is
   silent — no browser, safe for cron.

## Scheduling with cron

Find the absolute paths first:
```bash
which python3   # or: readlink -f .venv/bin/python
pwd
```

Then `crontab -e` and add a line to run at 7:00 AM daily:
```
0 7 * * * cd /absolute/path/to/agents/morning-briefing && /absolute/path/to/.venv/bin/python agent.py >> briefing.log 2>&1
```

Notes:
- Cron runs with a minimal environment — it won't automatically have your
  shell's exported variables. Either put the `export` lines in a small
  `env.sh` and source it in the cron line, or set the variables directly in
  the crontab with `ANTHROPIC_API_KEY=... BRIEFING_TO_EMAIL=... 0 7 * * * ...`.
- The `>> briefing.log 2>&1` keeps a log so you can check it ran (and see
  errors) without digging through system mail.
- OAuth refresh tokens can eventually expire if unused for 6 months, or if
  you're still in "Testing" mode on the consent screen (7-day expiry) —
  publish the OAuth consent screen (still fine for personal use, doesn't
  require Google review for the scopes used here) to avoid that.
