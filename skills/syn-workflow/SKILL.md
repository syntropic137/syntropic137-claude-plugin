---
name: syn-workflow
description: Manage Syntropic137 workflows — list, show, create, run, validate, delete, and check execution status
argument-hint: <list|show|run|create|validate|delete|status> [args]
disable-model-invocation: true
allowed-tools: Bash
model: sonnet
---

Installed workflows: !`syn workflow list 2>/dev/null || echo "(syn not found — run: npx @syntropic137/setup cli)"`

```bash
PARSED_ARGS=()
while IFS= read -r arg; do
  PARSED_ARGS+=("$arg")
done < <(
  python3 -c 'import os, shlex; [print(arg) for arg in shlex.split(os.environ.get("ARGUMENTS", ""))]'
)

SUBCOMMAND="${PARSED_ARGS[0]:-}"
ARGS=("${PARSED_ARGS[@]:1}")

case "$SUBCOMMAND" in
  list)
    INCLUDE_ARCHIVED=false
    for arg in "${ARGS[@]}"; do
      if [ "$arg" = "--archived" ] || [ "$arg" = "--include-archived" ]; then
        INCLUDE_ARCHIVED=true
        break
      fi
    done
    if [ "$INCLUDE_ARCHIVED" = true ]; then
      syn workflow list --include-archived
    else
      syn workflow list
    fi
    ;;
  show)
    syn workflow show "${ARGS[@]}"
    ;;
  run)
    syn workflow run "${ARGS[@]}"
    ;;
  create)
    syn workflow create "${ARGS[@]}"
    ;;
  validate)
    syn workflow validate "${ARGS[@]}"
    ;;
  delete)
    syn workflow delete "${ARGS[@]}"
    ;;
  status)
    syn workflow status "${ARGS[@]}"
    ;;
  ""|help)
    echo "Usage: /syn-workflow <subcommand> [args]"
    echo ""
    echo "Subcommands:"
    echo "  list [--archived]              List workflows installed in the platform"
    echo "  show <id>                      Show workflow template detail"
    echo "  run <id> --task \"...\" [--input key=value ...]"
    echo "                                 Run a workflow"
    echo "  create --type <type> [--repo owner/repo] [--description \"...\"]"
    echo "                                 Create a new workflow template"
    echo "  validate <path>                Validate a local YAML workflow definition"
    echo "  delete <id> [--force]          Archive an installed workflow"
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
