---
name: syn-insights
description: Query Syntropic137 observability data — sessions, artifacts, token costs, tool timelines, and system-wide insights
argument-hint: <overview|sessions|artifacts|costs|tools|tokens> [args]
disable-model-invocation: true
allowed-tools: Bash
model: sonnet
---

```bash
set -o pipefail

# Resolve API URL
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

_flag_value() {
  # Extract value of --flag from argument list: _flag_value "--flag" "$@"
  local flag="$1"; shift
  local prev=""
  for arg in "$@"; do
    if [ "$prev" = "$flag" ]; then printf '%s' "$arg"; return; fi
    prev="$arg"
  done
}

PARSED_ARGS=()
while IFS= read -r arg; do
  PARSED_ARGS+=("$arg")
done < <(
  python3 -c 'import os, shlex; [print(arg) for arg in shlex.split(os.environ.get("ARGUMENTS", ""))]'
)

SUBCOMMAND="${PARSED_ARGS[0]:-}"
ARGS=("${PARSED_ARGS[@]:1}")

case "$SUBCOMMAND" in
  overview)
    echo "=== Platform Overview ==="
    _curl_json "$_url/api/v1/organizations/overview"
    ;;
  sessions)
    SESSION_ID="${ARGS[0]:-}"
    WF_FILTER=$(_flag_value "--workflow" "${ARGS[@]}")
    STATUS_FILTER=$(_flag_value "--status" "${ARGS[@]}")
    if [ -n "$SESSION_ID" ] && [[ "$SESSION_ID" != --* ]]; then
      _curl_json "$_url/api/v1/sessions/$SESSION_ID"
    else
      QUERY=""
      [ -n "$WF_FILTER" ]     && QUERY="workflow_id=$WF_FILTER"
      [ -n "$STATUS_FILTER" ] && QUERY="${QUERY}${QUERY:+&}status=$STATUS_FILTER"
      _curl_json "$_url/api/v1/sessions${QUERY:+?$QUERY}"
    fi
    ;;
  artifacts)
    WF_FILTER=$(_flag_value "--workflow" "${ARGS[@]}")
    ART_ID="${ARGS[0]:-}"
    RAW=false
    for arg in "${ARGS[@]}"; do [ "$arg" = "--raw" ] && RAW=true; done
    if [ -n "$ART_ID" ] && [[ "$ART_ID" != --* ]]; then
      if [ "$RAW" = true ]; then
        syn artifacts content "$ART_ID" --raw
      else
        syn artifacts show "$ART_ID"
      fi
    elif [ -n "$WF_FILTER" ]; then
      syn artifacts list --workflow "$WF_FILTER"
    else
      syn artifacts list
    fi
    ;;
  costs)
    COST_TARGET="${ARGS[0]:-}"
    COST_ID="${ARGS[1]:-}"
    case "$COST_TARGET" in
      session)
        _curl_json "$_url/api/v1/costs/sessions/$COST_ID"
        ;;
      workflow|execution)
        _curl_json "$_url/api/v1/costs/executions/$COST_ID"
        ;;
      *)
        _curl_json "$_url/api/v1/costs/summary"
        ;;
    esac
    ;;
  tools)
    SESSION_ID="${ARGS[0]:-}"
    LIMIT=$(_flag_value "--limit" "${ARGS[@]}")
    LIMIT="${LIMIT:-100}"
    if [ -z "$SESSION_ID" ] || [[ "$SESSION_ID" == --* ]]; then
      echo "Usage: /syn-insights tools <session-id> [--limit N]" >&2
      exit 1
    fi
    _curl_json "$_url/api/v1/events/sessions/$SESSION_ID/tools?limit=$LIMIT"
    ;;
  tokens)
    SESSION_ID="${ARGS[0]:-}"
    if [ -z "$SESSION_ID" ] || [[ "$SESSION_ID" == --* ]]; then
      echo "Usage: /syn-insights tokens <session-id>" >&2
      exit 1
    fi
    _curl_json "$_url/api/v1/events/sessions/$SESSION_ID/tokens"
    ;;
  ""|help)
    echo "Usage: /syn-insights <subcommand> [args]"
    echo ""
    echo "Subcommands:"
    echo "  overview                       Cross-org health and cost summary"
    echo "  sessions [session-id]          List sessions or show session detail"
    echo "  sessions --workflow <id>       Sessions for a specific workflow"
    echo "  sessions --status <status>     Filter by status (running/completed/failed)"
    echo "  sessions --workflow <id> --status <status>"
    echo "                                 Combine both filters"
    echo "  artifacts [artifact-id]        List artifacts or show artifact detail"
    echo "  artifacts --workflow <id>      Artifacts for a specific workflow"
    echo "  artifacts <id> --raw           Show raw artifact content"
    echo "  costs [session <id>]           Cost summary or session cost"
    echo "  costs [workflow <id>]          Cost breakdown for a workflow execution"
    echo "  tools <session-id> [--limit N] Tool call timeline for a session"
    echo "  tokens <session-id>            Token usage metrics for a session"
    echo ""
    echo "Examples:"
    echo "  /syn-insights overview"
    echo "  /syn-insights sessions"
    echo "  /syn-insights sessions sess-abc123"
    echo "  /syn-insights sessions --workflow wf-abc123 --status completed"
    echo "  /syn-insights artifacts --workflow wf-abc123"
    echo "  /syn-insights costs"
    echo "  /syn-insights costs session sess-abc123"
    echo "  /syn-insights tools sess-abc123"
    echo "  /syn-insights tokens sess-abc123"
    ;;
  *)
    echo "Unknown subcommand: $SUBCOMMAND"
    echo "Run /syn-insights help for usage."
    exit 1
    ;;
esac
```

On API errors, run `/syn-health` to diagnose platform status.
If `syn` CLI is not found, install with: `npx @syntropic137/setup cli`
