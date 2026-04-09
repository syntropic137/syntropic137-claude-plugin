---
name: syn-repo
description: Manage Syntropic137 organizations, systems, and registered repositories — the hierarchy for cost rollup, health monitoring, and repo registration
argument-hint: <list|overview|github> [org|system|repo] [args]
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
TARGET="${PARSED_ARGS[1]:-}"
ARGS=("${PARSED_ARGS[@]:2}")

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

case "$SUBCOMMAND" in
  list)
    case "$TARGET" in
      org|orgs)
        _curl_json "$_url/api/v1/organizations"
        ;;
      system|systems)
        _curl_json "$_url/api/v1/systems"
        ;;
      repo|repos|"")
        if command -v syn &>/dev/null; then
          syn github repos "${ARGS[@]}"
        else
          _curl_json "$_url/api/v1/repos"
        fi
        ;;
      *)
        echo "Usage: /syn-repo list [org|system|repo]"
        ;;
    esac
    ;;
  overview)
    _curl_json "$_url/api/v1/organizations/overview"
    ;;
  github)
    syn github repos "${ARGS[@]}"
    ;;
  ""|help)
    echo "Usage: /syn-repo <subcommand> [target] [args]"
    echo ""
    echo "Subcommands:"
    echo "  list [org|system|repo]         List organizations, systems, or repos"
    echo "  overview                       Cross-org health and cost overview"
    echo "  github [--installation <id>]   List repos accessible to the GitHub App"
    echo ""
    echo "Examples:"
    echo "  /syn-repo list"
    echo "  /syn-repo list org"
    echo "  /syn-repo list system"
    echo "  /syn-repo overview"
    echo "  /syn-repo github"
    echo ""
    echo "Note: Repos are auto-registered when the GitHub App is installed on a repository."
    echo "If repos are missing, verify the GitHub App: npx @syntropic137/setup github-app"
    ;;
  *)
    echo "Unknown subcommand: $SUBCOMMAND"
    echo "Run /syn-repo help for usage."
    exit 1
    ;;
esac
```

On API errors, run `/syn-health` to diagnose platform status.
If GitHub repos are not listed, verify the GitHub App is installed: `npx @syntropic137/setup github-app`
