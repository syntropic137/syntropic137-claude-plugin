---
model: sonnet
allowed-tools: Bash
argument-hint: "[summary | session <id> | workflow <id>]"
---

# /syn-costs — Cost Tracking

Parse the user's argument to determine the subcommand:
- No argument or `summary` → `uv run --package syn-cli syn costs summary`
- `session <id>` → `uv run --package syn-cli syn costs session <id>`
- `workflow <id>` → `uv run --package syn-cli syn costs workflow <id>`

Run the appropriate command and display the output. If the API is unreachable, suggest running `/syn-health` to diagnose.
