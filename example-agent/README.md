# example-agent

Reference implementation of the core agent loop, hand-written with no framework.
Copy this folder as the starting point for a new agent.

## What it demonstrates

- Defining a tool (JSON schema + a real Python function)
- The request -> check-for-tool-use -> run-tool -> feed-result-back loop
- Terminating when the model responds with plain text instead of a tool call

## Run it

```bash
pip install -r ../requirements.txt
export ANTHROPIC_API_KEY=...
python agent.py
```

## Next steps once you outgrow this

- Multiple tools with a dispatch table (already sketched via `TOOL_IMPLEMENTATIONS`)
- Persisting `messages` across runs for a stateful agent
- Parallel tool calls (the loop already handles multiple `tool_use` blocks per turn)
- Moving to the Claude Agent SDK once you need subagents, hooks, or permission prompts
