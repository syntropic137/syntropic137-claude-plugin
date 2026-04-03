---
model: sonnet
allowed-tools: Bash
argument-hint: "[list | show <id> | search <query>]"
---

# /syn-workflows — Workflow Management

First, detect if the `syn` CLI is available:

```bash
if command -v syn &>/dev/null; then
    SYN_CLI="syn"
elif command -v uv &>/dev/null; then
    SYN_CLI="uv run --package syn-cli syn"
else
    SYN_CLI=""
fi
```

Parse the user's argument to determine the subcommand:

- No argument or `list` →
  - If SYN_CLI: `$SYN_CLI workflow list`
  - Fallback: `curl -sf "${SYN_API_URL:-http://localhost:8137}/api/v1/workflows"`
- `show <id>` →
  - If SYN_CLI: `$SYN_CLI workflow show <id>`
  - Fallback: `curl -sf "${SYN_API_URL:-http://localhost:8137}/api/v1/workflows/<id>"`
- `search <query>` →
  - If SYN_CLI: `$SYN_CLI workflow search "<query>"`
  - Fallback: `curl -sf "${SYN_API_URL:-http://localhost:8137}/api/v1/workflows?q=<query>"`

Display results and summarize for the user. If listing, highlight workflow name, type, classification, and phase count.
