---
model: sonnet
allowed-tools: Bash
argument-hint: "[list | create --from-package <name> | pause <id> | resume <id>]"
---

# /syn-triggers — Trigger Management

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
  - If SYN_CLI: `$SYN_CLI triggers list`
  - Fallback: `curl -sf "$SYN_API_URL/api/v1/triggers"`
- `create --from-package <name>` →
  - If SYN_CLI: `$SYN_CLI triggers create --from-package <name>`
  - Fallback: Inform user the CLI is required for trigger creation from packages
- `pause <id>` →
  - If SYN_CLI: `$SYN_CLI triggers pause <id>`
  - Fallback: `curl -fsS -X POST "$SYN_API_URL/api/v1/triggers/<id>/pause"`
- `resume <id>` →
  - If SYN_CLI: `$SYN_CLI triggers resume <id>`
  - Fallback: `curl -fsS -X POST "$SYN_API_URL/api/v1/triggers/<id>/resume"`

Display trigger details including: name, event type, conditions, associated workflow, and status (active/paused). Highlight any safety configuration (max_attempts, cooldown, budget).
