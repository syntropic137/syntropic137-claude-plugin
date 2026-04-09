---
name: syn-repo
description: Manage Syntropic137 organizations, systems, and registered repositories — the hierarchy for cost rollup, health monitoring, and repo registration
argument-hint: <list|show|create|assign> [org|system|repo] [args]
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

SUBCOMMAND=$(echo "$ARGUMENTS" | awk '{print $1}')
TARGET=$(echo "$ARGUMENTS" | awk '{print $2}')
ARGS=$(echo "$ARGUMENTS" | cut -d' ' -f3-)

case "$SUBCOMMAND" in
  list)
    case "$TARGET" in
      org|orgs)
        curl -sf "$_url/api/v1/organizations" | python3 -m json.tool 2>/dev/null || curl -sf "$_url/api/v1/organizations"
        ;;
      system|systems)
        curl -sf "$_url/api/v1/systems" | python3 -m json.tool 2>/dev/null || curl -sf "$_url/api/v1/systems"
        ;;
      repo|repos|"")
        syn github repos 2>/dev/null || curl -sf "$_url/api/v1/repos" | python3 -m json.tool 2>/dev/null || curl -sf "$_url/api/v1/repos"
        ;;
      *)
        echo "Usage: /syn-repo list [org|system|repo]"
        ;;
    esac
    ;;
  overview)
    curl -sf "$_url/api/v1/organizations/overview" | python3 -m json.tool 2>/dev/null || curl -sf "$_url/api/v1/organizations/overview"
    ;;
  github)
    syn github repos $ARGS
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
    echo "Note: Organizations, systems, and repos form the hierarchy for cost rollup and health."
    echo "Repos are typically auto-registered when the GitHub App is installed on a repository."
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
