---
model: sonnet
allowed-tools: Bash
argument-hint: "<session-id> [events | tools | tokens | errors] [--limit N]"
---

# /syn-observe — Observability Data

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

This command requires a session ID as the first argument.

Parse the user's arguments:
- `<session-id>` (only ID provided) or `<session-id> events`:
  - If SYN_CLI: `$SYN_CLI events session <session-id>`
  - Else: `curl -sf "$SYN_API_URL/api/v1/events/sessions/<session-id>"`
- `<session-id> tools [--limit N]` (default limit: 100):
  - If SYN_CLI: `$SYN_CLI observe tools <session-id>`
  - Else: `curl -sf "$SYN_API_URL/api/v1/events/sessions/<session-id>/tools?limit=<N>"`
- `<session-id> tokens`:
  - `curl -sf "$SYN_API_URL/api/v1/events/sessions/<session-id>/tokens"`
- `<session-id> errors`:
  - If SYN_CLI: `$SYN_CLI events session <session-id> --type error`
  - Else: `curl -sf "$SYN_API_URL/api/v1/events/sessions/<session-id>?event_type=error"`

If no session ID is provided, tell the user they need to specify one and suggest running `/syn-sessions list` to find available sessions.

Run the appropriate command and display the output (pipe through `jq .` for readability if available). If the API is unreachable, suggest running `/syn-health` to diagnose.
