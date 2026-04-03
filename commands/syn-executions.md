---
model: sonnet
allowed-tools: Bash
argument-hint: "[list | show <id> | status <id>]"
---

# /syn-executions — Execution Monitoring

First, detect the CLI:

```bash
if command -v syn &>/dev/null; then
    SYN_CLI="syn"
elif command -v uv &>/dev/null; then
    SYN_CLI="uv run --package syn-cli syn"
else
    SYN_CLI=""
fi
```

Parse the user's argument:

- No argument or `list` →
  - If SYN_CLI: `$SYN_CLI execution list`
  - Fallback: `curl -sf "${SYN_API_URL:-http://localhost:8137}/api/v1/executions"`
- `show <id>` →
  - If SYN_CLI: `$SYN_CLI execution show <id>`
  - Fallback: `curl -sf "${SYN_API_URL:-http://localhost:8137}/api/v1/executions/<id>"`
- `status <id>` →
  - If SYN_CLI: `$SYN_CLI workflow status <id>`
  - Fallback: `curl -sf "${SYN_API_URL:-http://localhost:8137}/api/v1/executions/<id>/status"`

Display execution details including: status, workflow name, phase progress, started/completed timestamps, and cost if available. For running executions, show which phase is currently active.
