---
model: sonnet
allowed-tools: Bash
argument-hint: "[list | create --from-package <name> | pause <id> | resume <id>]"
---

# /syn-triggers — Trigger Management

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
  - If SYN_CLI: `$SYN_CLI triggers list`
  - Fallback: `curl -sf "${SYN_API_URL:-http://localhost:8137}/api/v1/triggers"`
- `create --from-package <name>` →
  - If SYN_CLI: `$SYN_CLI triggers create --from-package <name>`
  - Fallback: Inform user the CLI is required for trigger creation from packages
- `pause <id>` →
  - If SYN_CLI: `$SYN_CLI triggers pause <id>`
  - Fallback: `curl -X POST "${SYN_API_URL:-http://localhost:8137}/api/v1/triggers/<id>/pause"`
- `resume <id>` →
  - If SYN_CLI: `$SYN_CLI triggers resume <id>`
  - Fallback: `curl -X POST "${SYN_API_URL:-http://localhost:8137}/api/v1/triggers/<id>/resume"`

Display trigger details including: name, event type, conditions, associated workflow, and status (active/paused). Highlight any safety configuration (max_attempts, cooldown, budget).
