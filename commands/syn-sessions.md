---
model: sonnet
allowed-tools: Bash
argument-hint: "[list [--workflow <id>] [--status <status>] | show <id>]"
---

# /syn-sessions — Session Management

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

Parse the user's argument to determine the subcommand:
- No argument or `list` → `curl -sf "$SYN_API_URL/api/v1/sessions"`
- `list --workflow <id>` → `curl -sf "$SYN_API_URL/api/v1/sessions?workflow_id=<id>"`
- `list --status <status>` → `curl -sf "$SYN_API_URL/api/v1/sessions?status=<status>"` (values: `running`, `completed`, `failed`, `cancelled`)
- `list --workflow <id> --status <status>` → combine both query params
- `show <id>` → `curl -sf "$SYN_API_URL/api/v1/sessions/<id>"`

Run the appropriate command and display the output (pipe through `python3 -m json.tool` for readability if available). If the API is unreachable, suggest running `/syn-health` to diagnose.
