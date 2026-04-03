---
model: sonnet
allowed-tools: Bash
argument-hint: "[--workflow <id>]"
---

# /syn-metrics — Aggregated Metrics

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
- No argument:
  - If SYN_CLI: `$SYN_CLI metrics show`
  - Else: `curl -sf "$SYN_API_URL/api/v1/metrics"`
- `--workflow <id>`:
  - If SYN_CLI: `$SYN_CLI metrics show --workflow <id>`
  - Else: `curl -sf "$SYN_API_URL/api/v1/metrics?workflow_id=<id>"`

Run the appropriate command and display the output (pipe through `jq .` for readability if available). If the API is unreachable, suggest running `/syn-health` to diagnose.
