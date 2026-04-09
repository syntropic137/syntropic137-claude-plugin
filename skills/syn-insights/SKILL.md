---
name: syn-insights
description: Query Syntropic137 observability data — sessions, artifacts, token costs, tool timelines, and system-wide insights
argument-hint: <overview|sessions|artifacts|costs|tools|tokens> [args]
disable-model-invocation: true
allowed-tools: Bash
model: sonnet
---

```bash
# Resolve API URL
if [ -n "${SYN_API_URL:-}" ]; then
  _url="$SYN_API_URL"
elif [ -f "$HOME/.syntropic137/.env" ]; then
  _hostname=$(grep '^SYN_PUBLIC_HOSTNAME=' "$HOME/.syntropic137/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
  _url="${_hostname:+https://$_hostname}"
fi
_url="${_url:-http://localhost:8137}"

_json() { python3 -m json.tool 2>/dev/null || cat; }

SUBCOMMAND=$(echo "$ARGUMENTS" | awk '{print $1}')
ARGS=$(echo "$ARGUMENTS" | cut -d' ' -f2-)

case "$SUBCOMMAND" in
  overview)
    echo "=== Platform Overview ==="
    curl -sf "$_url/api/v1/organizations/overview" | _json
    ;;
  sessions)
    SESSION_ID=$(echo "$ARGS" | awk '{print $1}')
    WF_FILTER=$(echo "$ARGS" | grep -oP '(?<=--workflow )\S+' || true)
    STATUS_FILTER=$(echo "$ARGS" | grep -oP '(?<=--status )\S+' || true)
    if [ -n "$SESSION_ID" ] && [[ "$SESSION_ID" != --* ]]; then
      curl -sf "$_url/api/v1/sessions/$SESSION_ID" | _json
    elif [ -n "$WF_FILTER" ]; then
      curl -sf "$_url/api/v1/sessions?workflow_id=$WF_FILTER" | _json
    elif [ -n "$STATUS_FILTER" ]; then
      curl -sf "$_url/api/v1/sessions?status=$STATUS_FILTER" | _json
    else
      curl -sf "$_url/api/v1/sessions" | _json
    fi
    ;;
  artifacts)
    WF_FILTER=$(echo "$ARGS" | grep -oP '(?<=--workflow )\S+' || true)
    ART_ID=$(echo "$ARGS" | awk '{print $1}')
    RAW=$(echo "$ARGS" | grep -q '\-\-raw' && echo "1" || echo "")
    if [ -n "$ART_ID" ] && [[ "$ART_ID" != --* ]]; then
      if [ -n "$RAW" ]; then
        syn artifacts content $ART_ID --raw
      else
        syn artifacts show $ART_ID
      fi
    elif [ -n "$WF_FILTER" ]; then
      syn artifacts list --workflow $WF_FILTER
    else
      syn artifacts list
    fi
    ;;
  costs)
    COST_TARGET=$(echo "$ARGS" | awk '{print $1}')
    COST_ID=$(echo "$ARGS" | awk '{print $2}')
    case "$COST_TARGET" in
      session)
        curl -sf "$_url/api/v1/costs/sessions/$COST_ID" | _json
        ;;
      workflow|execution)
        curl -sf "$_url/api/v1/costs/executions/$COST_ID" | _json
        ;;
      *)
        curl -sf "$_url/api/v1/costs/summary" | _json
        ;;
    esac
    ;;
  tools)
    SESSION_ID=$(echo "$ARGS" | awk '{print $1}')
    LIMIT=$(echo "$ARGS" | grep -oP '(?<=--limit )\S+' || echo "100")
    if [ -z "$SESSION_ID" ] || [[ "$SESSION_ID" == --* ]]; then
      echo "Usage: /syn-insights tools <session-id> [--limit N]"
    else
      curl -sf "$_url/api/v1/events/sessions/$SESSION_ID/tools?limit=$LIMIT" | _json
    fi
    ;;
  tokens)
    SESSION_ID=$(echo "$ARGS" | awk '{print $1}')
    if [ -z "$SESSION_ID" ] || [[ "$SESSION_ID" == --* ]]; then
      echo "Usage: /syn-insights tokens <session-id>"
    else
      curl -sf "$_url/api/v1/events/sessions/$SESSION_ID/tokens" | _json
    fi
    ;;
  ""|help)
    echo "Usage: /syn-insights <subcommand> [args]"
    echo ""
    echo "Subcommands:"
    echo "  overview                       Cross-org health and cost summary"
    echo "  sessions [session-id]          List sessions or show session detail"
    echo "  sessions --workflow <id>       Sessions for a specific workflow"
    echo "  sessions --status <status>     Filter by status (running/completed/failed)"
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
