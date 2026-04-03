---
model: sonnet
allowed-tools: Bash
argument-hint: "<workflow-id> [--input key=value ...]"
---

# /syn-run — Execute a Workflow

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

Parse the user's argument. The first argument is the workflow ID. Remaining arguments are `--input key=value` pairs.

- If SYN_CLI: `$SYN_CLI workflow run <workflow-id> --input key1=value1 --input key2=value2`
- Fallback API call:
  ```bash
  curl -fsS -X POST "$SYN_API_URL/api/v1/workflows/<workflow-id>/execute" \
    -H "Content-Type: application/json" \
    -d '{"inputs": {"key1": "value1", "key2": "value2"}}'
  ```

After launching, display the execution ID and suggest monitoring with `/syn-executions show <id>`.

If the user provides a workflow name (not a UUID), first resolve it to an ID using `/syn-workflows search <name>` or `/syn-workflows list`, then use the resolved ID. Once you have the ID, check what inputs are required using `/syn-workflows show <id>` and prompt the user for any required inputs before executing.
