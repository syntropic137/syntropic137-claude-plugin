---
model: sonnet
allowed-tools: Bash
argument-hint: "[list | show <id>]"
---

# /syn-sessions — Session Management

Parse the user's argument to determine the subcommand:
- No argument or `list` → `uv run --package syn-cli syn sessions list`
- `show <id>` → `uv run --package syn-cli syn sessions show <id>`

Run the appropriate command and display the output. If the API is unreachable, suggest running `/syn-health` to diagnose.
