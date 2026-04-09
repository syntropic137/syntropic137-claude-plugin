---
name: syn-marketplace
description: Browse, install, update, export, and publish Syntropic137 workflows via GitHub repositories — the self-hosted workflow marketplace
argument-hint: <list|add|install|installed|update|remove|export|publish> [args]
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
  # --- Consuming: install workflows from GitHub repos ---
  list|search)
    # Browse available workflows from registered marketplace sources
    curl -sf "$_url/api/v1/marketplace/sources" | _json 2>/dev/null || {
      echo "No marketplace sources registered yet."
      echo ""
      echo "Add a source with:"
      echo "  /syn-marketplace add <github-repo-url>"
      echo ""
      echo "Example:"
      echo "  /syn-marketplace add https://github.com/syntropic137/workflow-library"
    }
    ;;
  add)
    # Register a GitHub repo as a marketplace source
    REPO_URL=$(echo "$ARGS" | awk '{print $1}')
    if [ -z "$REPO_URL" ]; then
      echo "Usage: /syn-marketplace add <github-repo-url>"
      echo "Example: /syn-marketplace add https://github.com/syntropic137/workflow-library"
      exit 1
    fi
    curl -sf -X POST "$_url/api/v1/marketplace/sources" \
      -H "Content-Type: application/json" \
      -d "{\"url\": \"$REPO_URL\"}" | _json
    ;;
  install)
    # Install a workflow from a registered source
    WORKFLOW_NAME=$(echo "$ARGS" | awk '{print $1}')
    if [ -z "$WORKFLOW_NAME" ]; then
      echo "Usage: /syn-marketplace install <workflow-name>"
      echo "List available workflows with: /syn-marketplace list"
      exit 1
    fi
    curl -sf -X POST "$_url/api/v1/marketplace/install" \
      -H "Content-Type: application/json" \
      -d "{\"name\": \"$WORKFLOW_NAME\"}" | _json
    ;;
  installed)
    # List installed marketplace workflows
    curl -sf "$_url/api/v1/marketplace/installed" | _json 2>/dev/null || {
      echo "No marketplace workflows installed yet."
      echo "Browse available workflows with: /syn-marketplace list"
    }
    ;;
  update)
    # Update installed workflow(s) to latest version
    WORKFLOW_NAME=$(echo "$ARGS" | awk '{print $1}')
    if [ -n "$WORKFLOW_NAME" ]; then
      curl -sf -X POST "$_url/api/v1/marketplace/update" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$WORKFLOW_NAME\"}" | _json
    else
      curl -sf -X POST "$_url/api/v1/marketplace/update" | _json
    fi
    ;;
  remove)
    # Unregister a marketplace source
    SOURCE=$(echo "$ARGS" | awk '{print $1}')
    if [ -z "$SOURCE" ]; then
      echo "Usage: /syn-marketplace remove <source-url-or-id>"
      exit 1
    fi
    curl -sf -X DELETE "$_url/api/v1/marketplace/sources/$SOURCE" | _json
    ;;
  # --- Publishing: export and share your workflows ---
  export)
    # Package a local workflow for sharing
    WORKFLOW_ID=$(echo "$ARGS" | awk '{print $1}')
    OUTPUT=$(echo "$ARGS" | grep -oP '(?<=--output )\S+' || echo "./workflow-export")
    if [ -z "$WORKFLOW_ID" ]; then
      echo "Usage: /syn-marketplace export <workflow-id> [--output <path>]"
      echo "List workflows with: /syn-workflow list"
      exit 1
    fi
    curl -sf "$_url/api/v1/workflows/$WORKFLOW_ID/export" | _json
    ;;
  publish)
    # Push a workflow to a GitHub repo so others can install it
    WORKFLOW_ID=$(echo "$ARGS" | awk '{print $1}')
    REPO=$(echo "$ARGS" | grep -oP '(?<=--repo )\S+' || true)
    if [ -z "$WORKFLOW_ID" ] || [ -z "$REPO" ]; then
      echo "Usage: /syn-marketplace publish <workflow-id> --repo owner/repo"
      exit 1
    fi
    echo "To publish workflow $WORKFLOW_ID to $REPO:"
    echo ""
    echo "1. Export the workflow:"
    echo "   /syn-marketplace export $WORKFLOW_ID"
    echo ""
    echo "2. Copy the exported YAML to your GitHub repo's workflows/ directory"
    echo ""
    echo "3. Push the repo — others can install it with:"
    echo "   /syn-marketplace add https://github.com/$REPO"
    echo "   /syn-marketplace install <workflow-name>"
    echo ""
    echo "Note: A curated marketplace registry is planned. For now,"
    echo "distribution is via ad-hoc GitHub repo sources."
    ;;
  ""|help)
    echo "Usage: /syn-marketplace <subcommand> [args]"
    echo ""
    echo "Consuming workflows:"
    echo "  list                           Browse workflows from registered sources"
    echo "  add <github-repo-url>          Register a GitHub repo as a marketplace source"
    echo "  install <workflow-name>        Install a workflow from a trusted source"
    echo "  installed                      List installed marketplace workflows"
    echo "  update [workflow-name]         Update to latest version"
    echo "  remove <source>                Unregister a marketplace source"
    echo ""
    echo "Publishing workflows:"
    echo "  export <workflow-id>           Package a workflow for sharing"
    echo "  publish <workflow-id> --repo owner/repo"
    echo "                                 Instructions to push to a GitHub repo"
    echo ""
    echo "Examples:"
    echo "  /syn-marketplace add https://github.com/syntropic137/workflow-library"
    echo "  /syn-marketplace list"
    echo "  /syn-marketplace install github-pr-review"
    echo "  /syn-marketplace export wf-abc123"
    echo ""
    echo "Note: A curated marketplace registry is planned. Current model uses"
    echo "      ad-hoc GitHub repos as trusted sources — like a private npm registry."
    ;;
  *)
    echo "Unknown subcommand: $SUBCOMMAND"
    echo "Run /syn-marketplace help for usage."
    exit 1
    ;;
esac
```

On API errors, run `/syn-health` to diagnose platform status.
