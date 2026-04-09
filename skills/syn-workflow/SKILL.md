---
name: syn-workflow
description: Manage Syntropic137 workflows — list, show, create, run, validate, delete, and check execution status
argument-hint: <list|show|run|create|validate|delete|status> [args]
disable-model-invocation: true
allowed-tools: Bash
model: sonnet
---

Current workflows: !`syn workflow list 2>/dev/null || echo "(syn not found — run: npx @syntropic137/setup cli)"`

```bash
SUBCOMMAND=$(echo "$ARGUMENTS" | awk '{print $1}')
ARGS=$(echo "$ARGUMENTS" | cut -d' ' -f2-)

case "$SUBCOMMAND" in
  list)
    if echo "$ARGS" | grep -q '\-\-archived'; then
      syn workflow list --include-archived
    else
      syn workflow list
    fi
    ;;
  show)
    syn workflow show $ARGS
    ;;
  run)
    syn workflow run $ARGS
    ;;
  create)
    syn workflow create $ARGS
    ;;
  validate)
    syn workflow validate $ARGS
    ;;
  delete)
    syn workflow delete $ARGS
    ;;
  status)
    syn workflow status $ARGS
    ;;
  ""|help)
    echo "Usage: /syn-workflow <subcommand> [args]"
    echo ""
    echo "Subcommands:"
    echo "  list [--archived]              List workflow templates"
    echo "  show <id>                      Show workflow template detail"
    echo "  run <id> --task \"...\" [--input key=value ...]"
    echo "                                 Run a workflow"
    echo "  create --type <type> [--repo owner/repo] [--description \"...\"]"
    echo "                                 Create a new workflow template"
    echo "  validate <path>                Validate a YAML workflow definition"
    echo "  delete <id> [--force]          Archive a workflow template"
    echo "  status <execution-id>          Check execution status"
    echo ""
    echo "Examples:"
    echo "  /syn-workflow list"
    echo "  /syn-workflow run wf-abc123 --task \"refactor auth module\""
    echo "  /syn-workflow run wf-abc123 --task \"fix login bug\" --input repository=owner/repo"
    echo "  /syn-workflow status exec-xyz"
    echo "  /syn-workflow validate ./my-workflow.yaml"
    ;;
  *)
    echo "Unknown subcommand: $SUBCOMMAND"
    echo "Run /syn-workflow help for usage."
    exit 1
    ;;
esac
```

If `syn` is not found, install with: `npx @syntropic137/setup cli`
On API errors, run `/syn-health` to diagnose platform status.
