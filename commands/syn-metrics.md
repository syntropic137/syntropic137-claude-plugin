---
model: sonnet
allowed-tools: Bash
argument-hint: "[--workflow <id>]"
---

# /syn-metrics — Aggregated Metrics

Parse the user's argument:
- No argument → `uv run --package syn-cli syn metrics show`
- `--workflow <id>` → `uv run --package syn-cli syn metrics show --workflow <id>`

Run the appropriate command and display the output. If the API is unreachable, suggest running `/syn-health` to diagnose.
