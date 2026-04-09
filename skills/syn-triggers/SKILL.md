---
name: syn-triggers
description: Manage Syntropic137 GitHub webhook trigger rules — list, register, enable, pause, and delete triggers that fire workflows on GitHub events
argument-hint: <list|register|enable|pause|delete> [args]
disable-model-invocation: true
allowed-tools: Bash
model: sonnet
---

Active triggers: !`syn triggers list 2>/dev/null || echo "(syn not found — run: npx @syntropic137/setup cli)"`

```bash
SUBCOMMAND=$(echo "$ARGUMENTS" | awk '{print $1}')
ARGS=$(echo "$ARGUMENTS" | cut -d' ' -f2-)

case "$SUBCOMMAND" in
  list)
    syn triggers list $ARGS
    ;;
  register)
    syn triggers register $ARGS
    ;;
  enable)
    syn triggers enable $ARGS
    ;;
  pause)
    syn triggers pause $ARGS
    ;;
  delete)
    # Resolve API URL for delete (not in Node CLI)
    if [ -n "${SYN_API_URL:-}" ]; then
      _url="$SYN_API_URL"
    elif [ -f "$HOME/.syntropic137/.env" ]; then
      _hostname=$(grep '^SYN_PUBLIC_HOSTNAME=' "$HOME/.syntropic137/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
      _url="${_hostname:+https://$_hostname}"
    fi
    _url="${_url:-http://localhost:8137}"
    TRIGGER_ID=$(echo "$ARGS" | awk '{print $1}')
    curl -sf -X DELETE "$_url/api/v1/triggers/$TRIGGER_ID"
    echo "Trigger $TRIGGER_ID deleted."
    ;;
  ""|help)
    echo "Usage: /syn-triggers <subcommand> [args]"
    echo ""
    echo "Subcommands:"
    echo "  list [--repository owner/repo]"
    echo "                                 List trigger rules"
    echo "  register --name <name> --event <event> --repository owner/repo --workflow <id>"
    echo "                                 Register a new trigger rule"
    echo "  enable <name> --repository owner/repo"
    echo "                                 Enable a paused trigger"
    echo "  pause <id> [--reason \"...\"]    Pause a trigger"
    echo "  delete <id>                    Permanently delete a trigger"
    echo ""
    echo "Supported events: push, pull_request, issues, issue_comment, check_run, workflow_run"
    echo ""
    echo "Examples:"
    echo "  /syn-triggers list --repository syntropic137/syntropic137"
    echo "  /syn-triggers register --name \"pr-review\" --event pull_request --repository owner/repo --workflow wf-abc123"
    echo "  /syn-triggers pause pr-review --reason \"investigating\""
    ;;
  *)
    echo "Unknown subcommand: $SUBCOMMAND"
    echo "Run /syn-triggers help for usage."
    exit 1
    ;;
esac
```

If `syn` is not found, install with: `npx @syntropic137/setup cli`
On API errors, run `/syn-health` to diagnose platform status.
