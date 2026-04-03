---
model: sonnet
allowed-tools: Bash
argument-hint: "<workflow-id> [--input key=value ...]"
---

# /syn-run — Execute a Workflow

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

Parse the user's argument. The first argument is the workflow ID. Remaining arguments are `--input key=value` pairs.

- If SYN_CLI: `$SYN_CLI workflow run <workflow-id> --input key1=value1 --input key2=value2`
- Fallback API call:
  ```bash
  curl -X POST "${SYN_API_URL:-http://localhost:8137}/api/v1/workflows/<workflow-id>/execute" \
    -H "Content-Type: application/json" \
    -d '{"inputs": {"key1": "value1", "key2": "value2"}}'
  ```

After launching, display the execution ID and suggest monitoring with `/syn-executions show <id>`.

If the user provides just a workflow name without inputs, first check what inputs are required using `/syn-workflows show <id>` and prompt the user for any required inputs before executing.
