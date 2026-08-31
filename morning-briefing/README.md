# morning-briefing

Gathers weather + today's Google Calendar, researches a fixed topic list with
the **last30days** engine (multi-platform social/web research), asks Claude to
synthesize a short briefing, and emails it to you via Gmail. Designed to run
unattended every morning via cron.

## What it demonstrates

Outgrowing the hand-rolled loop. The original (see git history) was the
one-shot shape: gather context → one model call → send. Once it needed to run
research across several topics and decide what's newsworthy, it moved to the
**Claude Agent SDK**, which supplies the loop, typed messages, and tool
permissioning.

## Architecture

```
agent.py
 ├─ get_google_credentials()          reused OAuth token (browser once)
 ├─ SDK tools (mcp server "briefing") — the ONLY tools the model gets
 │    ├─ get_weather                   open-meteo
 │    ├─ get_calendar_events           Google Calendar API
 │    ├─ research_topics               runs the last30days engine per topic, in parallel
 │    └─ send_briefing_email           Gmail API — recipient FIXED in code
 ├─ gate()                            deny-by-default: anything else is refused, no prompt
 └─ query(prompt, options)            the agent loop (max 20 turns, $3 budget cap)
```

**last30days is called as a plain subprocess, not loaded as a plugin/skill.**
Its `SKILL.md` is a large interactive setup-and-synthesis protocol written for
a human-driven session — an unattended agent won't follow it (it bails to
plain web search). `research_topics` runs the engine binary directly with
fixed flags (`--emit=context --quick --days 7`), which is the useful part.

The model has no shell, no file writes, and no web tools. The email recipient
is hard-coded to `$BRIEFING_TO_EMAIL`; the model's tool input for the
recipient is ignored. Safe to leave in cron.

## One-time setup

### 1. The `claude` CLI (the Agent SDK shells out to it)

```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

### 2. The last30days submodule

```bash
git submodule update --init vendor/last30days-skill   # from the repo root
```

The engine has **no pip dependencies** (stdlib only) and runs on this venv's
interpreter.

### 3. Python deps

```bash
cd morning-briefing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Google `credentials.json`

Google Cloud Console: new project, enable **Gmail API** + **Google Calendar
API**, configure the OAuth consent screen (External; add your address under
**Test users**), create an **OAuth client ID** of type **Desktop app**,
download the JSON, save it here as `credentials.json` (gitignored). For an
unattended daily cron, also hit **Publish app** — "Testing" mode expires the
refresh token after 7 days.

### 5. Environment variables

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export BRIEFING_TO_EMAIL=you@gmail.com
export BRIEFING_LAT=34.05      # optional, defaults to Los Angeles
export BRIEFING_LON=-118.24    # optional

# Calendars (optional). Default: every calendar you have checked in Google
# Calendar. Override with "primary" or a comma-separated list of calendar ids.
# export BRIEFING_CALENDARS=primary
# export BRIEFING_CALENDARS_EXCLUDE="SMCHS Bell Schedule,Holidays in United States"
```

Event times are shown in the machine's local timezone; all-day events from
shared calendars are tagged with the calendar name.

### 6. last30days API keys (optional — fuller source coverage)

Zero-config sources (Reddit, Hacker News, GitHub, Polymarket, web) work with
no keys. For X / YouTube / TikTok / Instagram, create `~/.config/last30days/.env`:

```bash
mkdir -p ~/.config/last30days && touch ~/.config/last30days/.env && open -e ~/.config/last30days/.env
```

```
SCRAPECREATORS_API_KEY=...     # TikTok, Instagram, YouTube comments  (scrapecreators.com)
XAI_API_KEY=...                # X/Twitter search + better reranking   (console.x.ai)
```

The engine reads that file itself. YouTube *video* transcripts also want
`yt-dlp`: `brew install yt-dlp`.

### 7. First run (authorizes Google)

```bash
python agent.py
```

Opens a browser once for Gmail + Calendar consent (**Advanced → Go to
&lt;app&gt; (unsafe)** → allow both). Saves `token.json`; every later run is
silent.

## Topics

Edit `topics.txt` — one topic per line, `#` comments and blank lines ignored.
No code change needed. Each line is one `last30days` research call, all run in
parallel.

Optional per-topic targeting: append `| <flags>` and they're added to that
topic's engine command — e.g. `--x-handle elonmusk`, `--subreddits
servicenow`, `--github-repo owner/repo`. `last30days.py --help` lists them all.

```
AI agents | --subreddits AI_Agents,singularity,LocalLLaMA
Elon Musk latest posts | --x-handle elonmusk
```

## Scheduling (daily, unattended)

`run.sh` is the entry point for scheduled runs — it sets `PATH` (so the
`claude` CLI is found) and sources `env.sh` for secrets, since launchd and
cron don't load your shell rc.

### env.sh (gitignored — create it)

```bash
cp /dev/null env.sh && open -e env.sh
```

```
export ANTHROPIC_API_KEY=sk-ant-...
export BRIEFING_TO_EMAIL=you@gmail.com
# export BRIEFING_LAT=34.05   # optional
# export BRIEFING_LON=-118.24
```

```bash
chmod 600 env.sh
```

### launchd (recommended on macOS)

```bash
cp com.romesh.morning-briefing.plist.example \
   ~/Library/LaunchAgents/com.romesh.morning-briefing.plist
# adjust the paths inside if your checkout isn't ~/agents
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.romesh.morning-briefing.plist
```

| Action | Command |
|---|---|
| Run now (test) | `launchctl kickstart -p gui/$(id -u)/com.romesh.morning-briefing` |
| Stop scheduling | `launchctl bootout gui/$(id -u)/com.romesh.morning-briefing` |
| After editing the plist | `bootout`, then `bootstrap` again |
| Check it's loaded | `launchctl list \| grep morning` |

Runs at 07:00, or the next wake if the Mac was asleep then. Output (including
the turn/cost summary line) goes to `briefing.log`.

### cron (alternative)

```
0 7 * * * /Users/you/agents/morning-briefing/run.sh
```

Cron won't wake a sleeping Mac; launchd will run the job on next wake.

### Keeping it working

- **Publish the Google OAuth consent screen** — in "Testing" mode the refresh
  token dies after 7 days and the job starts failing. Publishing needs no
  review for these scopes.
- `git submodule update --remote vendor/last30days-skill` occasionally to pull
  engine updates.
