---
name: syn-marketplace
description: Browse, install, update, export, and publish Syntropic137 workflows via GitHub repositories — the self-hosted workflow marketplace
argument-hint: <list|add|install|installed|update|remove|export|publish> [args]
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
  # --- Consuming: install workflows from GitHub repos ---
  list|search)
    local response
    if response=$(curl -sf "$_url/api/v1/marketplace/sources"); then
      printf '%s\n' "$response" | python3 -m json.tool 2>/dev/null || printf '%s\n' "$response"
    else
      echo "No marketplace sources registered yet."
      echo ""
      echo "Add a source with:"
      echo "  /syn-marketplace add <github-repo-url>"
      echo ""
      echo "Example:"
      echo "  /syn-marketplace add https://github.com/syntropic137/workflow-library"
    fi
    ;;
  add)
    REPO_URL="${ARGS[0]:-}"
    if [ -z "$REPO_URL" ]; then
      echo "Usage: /syn-marketplace add <github-repo-url>" >&2
      echo "Example: /syn-marketplace add https://github.com/syntropic137/workflow-library" >&2
      exit 1
    fi
    BODY=$(python3 -c "import json, sys; print(json.dumps({'url': sys.argv[1]}))" "$REPO_URL")
    local response
    if response=$(curl -sf -X POST "$_url/api/v1/marketplace/sources" \
        -H "Content-Type: application/json" -d "$BODY"); then
      printf '%s\n' "$response" | python3 -m json.tool 2>/dev/null || printf '%s\n' "$response"
    else
      echo "Error: failed to add marketplace source. Run /syn-health to diagnose." >&2
      exit 1
    fi
    ;;
  install)
    WORKFLOW_NAME="${ARGS[0]:-}"
    if [ -z "$WORKFLOW_NAME" ]; then
      echo "Usage: /syn-marketplace install <workflow-name>" >&2
      echo "List available workflows with: /syn-marketplace list" >&2
      exit 1
    fi
    BODY=$(python3 -c "import json, sys; print(json.dumps({'name': sys.argv[1]}))" "$WORKFLOW_NAME")
    local response
    if response=$(curl -sf -X POST "$_url/api/v1/marketplace/install" \
        -H "Content-Type: application/json" -d "$BODY"); then
      printf '%s\n' "$response" | python3 -m json.tool 2>/dev/null || printf '%s\n' "$response"
    else
      echo "Error: failed to install workflow. Run /syn-health to diagnose." >&2
      exit 1
    fi
    ;;
  installed)
    local response
    if response=$(curl -sf "$_url/api/v1/marketplace/installed"); then
      printf '%s\n' "$response" | python3 -m json.tool 2>/dev/null || printf '%s\n' "$response"
    else
      echo "No marketplace workflows installed yet."
      echo "Browse available workflows with: /syn-marketplace list"
    fi
    ;;
  update)
    WORKFLOW_NAME="${ARGS[0]:-}"
    BODY=$(python3 -c "import json, sys; d = {'name': sys.argv[1]} if sys.argv[1] else {}; print(json.dumps(d))" "$WORKFLOW_NAME")
    local response
    if response=$(curl -sf -X POST "$_url/api/v1/marketplace/update" \
        -H "Content-Type: application/json" -d "$BODY"); then
      printf '%s\n' "$response" | python3 -m json.tool 2>/dev/null || printf '%s\n' "$response"
    else
      echo "Error: update failed. Run /syn-health to diagnose." >&2
      exit 1
    fi
    ;;
  remove)
    SOURCE="${ARGS[0]:-}"
    if [ -z "$SOURCE" ]; then
      echo "Usage: /syn-marketplace remove <source-url-or-id>" >&2
      exit 1
    fi
    ENCODED=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$SOURCE")
    if curl -sf -X DELETE "$_url/api/v1/marketplace/sources/$ENCODED"; then
      echo "Marketplace source removed."
    else
      echo "Error: failed to remove source. Run /syn-health to diagnose." >&2
      exit 1
    fi
    ;;
  # --- Publishing: export and share your workflows ---
  export)
    WORKFLOW_ID="${ARGS[0]:-}"
    OUTPUT=$(_flag_value "--output" "${ARGS[@]}")
    OUTPUT="${OUTPUT:-./workflow-export.json}"
    if [ -z "$WORKFLOW_ID" ]; then
      echo "Usage: /syn-marketplace export <workflow-id> [--output <path>]" >&2
      echo "List workflows with: /syn-workflow list" >&2
      exit 1
    fi
    local response
    if response=$(curl -sf "$_url/api/v1/workflows/$WORKFLOW_ID/export"); then
      mkdir -p "$(dirname "$OUTPUT")"
      printf '%s\n' "$response" > "$OUTPUT"
      echo "Workflow exported to: $OUTPUT"
      printf '%s\n' "$response" | python3 -m json.tool 2>/dev/null || true
    else
      echo "Error: export failed. Run /syn-health to diagnose." >&2
      exit 1
    fi
    ;;
  publish)
    WORKFLOW_ID="${ARGS[0]:-}"
    REPO=$(_flag_value "--repo" "${ARGS[@]}")
    if [ -z "$WORKFLOW_ID" ] || [ -z "$REPO" ]; then
      echo "Usage: /syn-marketplace publish <workflow-id> --repo owner/repo" >&2
      exit 1
    fi
    echo "To publish workflow $WORKFLOW_ID to $REPO:"
    echo ""
    echo "1. Export the workflow:"
    echo "   /syn-marketplace export $WORKFLOW_ID --output ./workflow-export.json"
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
    echo "  export <workflow-id> [--output <path>]"
    echo "                                 Package a workflow for sharing"
    echo "  publish <workflow-id> --repo owner/repo"
    echo "                                 Instructions to push to a GitHub repo"
    echo ""
    echo "Examples:"
    echo "  /syn-marketplace add https://github.com/syntropic137/workflow-library"
    echo "  /syn-marketplace list"
    echo "  /syn-marketplace install github-pr-review"
    echo "  /syn-marketplace export wf-abc123 --output ./my-workflow.json"
    echo ""
    echo "Note: A curated marketplace registry is planned. Current model uses"
    echo "      ad-hoc GitHub repos as trusted sources."
    ;;
  *)
    echo "Unknown subcommand: $SUBCOMMAND"
    echo "Run /syn-marketplace help for usage."
    exit 1
    ;;
esac
```

On API errors, run `/syn-health` to diagnose platform status.
