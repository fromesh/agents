# agents

Personal repo for agents I build with Claude. Each agent lives in its own top-level folder.

## Structure

```
agents/
  example-agent/     # reference implementation - the core loop, written by hand
  <next-agent>/
  ...
```

## Conventions

- Each agent folder is self-contained: its own `agent.py`, `README.md`, and (if its deps
  diverge from the shared basics) its own `requirements.txt`.
- Start from `example-agent/` when building something new — it's the minimal
  request -> tool-check -> tool-run -> feed-back-in loop, no framework, so it's easy
  to see exactly what's happening before adding abstraction.
- Once an agent's needs outgrow the manual loop (subagents, persistent sessions,
  permission prompts, hooks), consider porting it to the Claude Agent SDK rather than
  hand-rolling those features.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
```
