#!/bin/bash
# Wrapper for unattended (launchd / cron) runs of the morning-briefing agent.
# Sets up a minimal environment - launchd and cron do not load your shell rc.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# The Agent SDK shells out to the `claude` CLI, which lives in the nvm node dir.
export PATH="/Users/rameshfernando/.nvm/versions/node/v24.16.0/bin:/opt/homebrew/bin:/usr/bin:/bin"

# Secrets and config (gitignored).
# shellcheck disable=SC1091
source "$HERE/env.sh"

exec "$HERE/.venv/bin/python" agent.py
