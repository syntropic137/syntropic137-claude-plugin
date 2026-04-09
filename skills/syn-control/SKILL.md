---
name: syn-control
description: Control running Syntropic137 executions — list, pause, resume, cancel, and check status of workflow executions
argument-hint: <list|status|pause|resume|cancel> [execution-id] [args]
disable-model-invocation: true
allowed-tools: Bash
model: sonnet
---

```bash
PARSED_ARGS=()
while IFS= read -r arg; do
  PARSED_ARGS+=("$arg")
done < <(
  python3 -c 'import os, shlex; [print(arg) for arg in shlex.split(os.environ.get("ARGUMENTS", ""))]'
)

SUBCOMMAND="${PARSED_ARGS[0]:-}"
ARGS=("${PARSED_ARGS[@]:1}")

# Resolve API URL for list/status endpoints (not in Node CLI)
if [ -n "${SYN_API_URL:-}" ]; then
  _url="$SYN_API_URL"
elif [ -f "$HOME/.syntropic137/.env" ]; then
  _hostname=$(grep '^SYN_PUBLIC_HOSTNAME=' "$HOME/.syntropic137/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
  _url="${_hostname:+https://$_hostname}"
fi
_url="${_url:-http://localhost:8137}"

_curl_json() {
  local url="$1"
  local response
  if response=$(curl -sf "$url"); then
    printf '%s\n' "$response" | python3 -m json.tool 2>/dev/null || printf '%s\n' "$response"
  else
    echo "Error: API unreachable at $url. Run /syn-health to diagnose." >&2
    exit 1
  fi
}

case "$SUBCOMMAND" in
  list)
    STATUS_FILTER=$(printf '%s\n' "${ARGS[@]}" | awk '{for (i=1; i<=NF; i++) if ($i=="--status" && i<NF) { print $(i+1); exit }}')
    if [ -n "$STATUS_FILTER" ]; then
      _curl_json "$_url/api/v1/executions?status=$STATUS_FILTER"
    else
      _curl_json "$_url/api/v1/executions"
    fi
    ;;
  status)
    EXEC_ID="${ARGS[0]:-}"
    if [ -z "$EXEC_ID" ]; then
      _curl_json "$_url/api/v1/executions"
    else
      syn control status "$EXEC_ID"
    fi
    ;;
  pause)
    syn control pause "${ARGS[@]}"
    ;;
  resume)
    syn control resume "${ARGS[@]}"
    ;;
  cancel)
    syn control cancel "${ARGS[@]}"
    ;;
  ""|help)
    echo "Usage: /syn-control <subcommand> [args]"
    echo ""
    echo "Subcommands:"
    echo "  list [--status running|paused|failed|completed]"
    echo "                                 List workflow executions"
    echo "  status [execution-id]          Show execution status (all if no ID)"
    echo "  pause <execution-id> [--reason \"...\"]"
    echo "                                 Pause a running execution"
    echo "  resume <execution-id>          Resume a paused execution"
    echo "  cancel <execution-id> [--reason \"...\"]"
    echo "                                 Cancel an execution"
    echo ""
    echo "Examples:"
    echo "  /syn-control list"
    echo "  /syn-control list --status running"
    echo "  /syn-control status exec-abc123"
    echo "  /syn-control pause exec-abc123 --reason \"reviewing intermediate results\""
    echo "  /syn-control resume exec-abc123"
    echo "  /syn-control cancel exec-abc123 --reason \"wrong workflow\""
    ;;
  *)
    echo "Unknown subcommand: $SUBCOMMAND"
    echo "Run /syn-control help for usage."
    exit 1
    ;;
esac
```

If `syn` is not found, install with: `npx @syntropic137/setup cli`
On API errors, run `/syn-health` to diagnose platform status.
