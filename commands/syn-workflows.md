---
model: sonnet
allowed-tools: Bash
argument-hint: "[list | show <id> | search <query>]"
---

# /syn-workflows — Workflow Management

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

Parse the user's argument to determine the subcommand:

- No argument or `list` →
  - If SYN_CLI: `$SYN_CLI workflow list`
  - Fallback: `curl -sf "$SYN_API_URL/api/v1/workflows"`
- `show <id>` →
  - If SYN_CLI: `$SYN_CLI workflow show <id>`
  - Fallback: `curl -sf "$SYN_API_URL/api/v1/workflows/<id>"`
- `search <query>` →
  - If SYN_CLI: `$SYN_CLI workflow search "<query>"`
  - Fallback: `curl -fsS --get --data-urlencode "q=<query>" "$SYN_API_URL/api/v1/workflows"`

Display results and summarize for the user. If listing, highlight workflow name, type, classification, and phase count.
