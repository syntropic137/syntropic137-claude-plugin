---
model: sonnet
allowed-tools: Bash
argument-hint: "<session-id> [events | tools | errors]"
---

# /syn-observe — Observability Data

This command requires a session ID as the first argument.

Parse the user's arguments:
- `<session-id>` (only ID provided) → `uv run --package syn-cli syn observe events <session-id>`
- `<session-id> events` → `uv run --package syn-cli syn observe events <session-id>`
- `<session-id> tools` → `uv run --package syn-cli syn observe tools <session-id>`
- `<session-id> errors` → `uv run --package syn-cli syn observe errors <session-id>`

If no session ID is provided, tell the user they need to specify one and suggest running `/syn-sessions list` to find available sessions.

Run the appropriate command and display the output. If the API is unreachable, suggest running `/syn-health` to diagnose.
