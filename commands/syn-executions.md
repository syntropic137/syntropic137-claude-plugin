---
model: sonnet
allowed-tools: Bash
argument-hint: "[list | show <id> | status <id>]"
---

# /syn-executions — Execution Monitoring

First, resolve the API URL:

```bash
if [ -n "${SYN_API_URL:-}" ]; then
    SYN_API_URL="$SYN_API_URL"
elif [ -f "$HOME/.syntropic137/.env" ]; then
    _hostname=$(grep '^SYN_PUBLIC_HOSTNAME=' "$HOME/.syntropic137/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
    if [ -n "$_hostname" ]; then
        SYN_API_URL="https://$_hostname"
    fi
fi
SYN_API_URL="${SYN_API_URL:-http://localhost:8137}"
```

Detect whether the `syn` CLI is available:

```bash
if command -v syn &>/dev/null; then
    SYN_CLI="syn"
else
    SYN_CLI=""
fi
```

Parse the user's argument:

- No argument or `list` →
  - If SYN_CLI: `$SYN_CLI execution list`
  - Fallback: `curl -sf "$SYN_API_URL/api/v1/executions"`
- `show <id>` →
  - If SYN_CLI: `$SYN_CLI execution show <id>`
  - Fallback: `curl -sf "$SYN_API_URL/api/v1/executions/<id>"`
- `status <id>` →
  - If SYN_CLI: `$SYN_CLI workflow status <id>`
  - Fallback: `curl -sf "$SYN_API_URL/api/v1/executions/<id>/status"`

Display execution details including: status, workflow name, phase progress, started/completed timestamps, and cost if available. For running executions, show which phase is currently active.
