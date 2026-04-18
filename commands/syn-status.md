---
model: sonnet
allowed-tools: Bash
---

# /syn-status — Composite Platform Status

First, resolve the API URL:

```bash
if [ -n "${SYN_API_URL:-}" ]; then
    SYN_API_URL="$SYN_API_URL"
elif [ -f "$HOME/.syntropic137/.env" ]; then
    _hostname=$(grep '^SYN_PUBLIC_HOSTNAME=' "$HOME/.syntropic137/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
    if [ -n "$_hostname" ]; then
        SYN_API_URL="https://$_hostname"
    fi
fi
SYN_API_URL="${SYN_API_URL:-http://localhost:8137}"
```

Detect whether the `syn` CLI is available:

```bash
if command -v syn &>/dev/null; then
    SYN_CLI="syn"
else
    SYN_CLI=""
fi
```

Run the following three checks and present a unified status view:

## 1. Container Status

Detect the installation path and check containers:

```bash
if [ -f "$HOME/.syntropic137/docker-compose.syntropic137.yaml" ]; then
    docker compose -f "$HOME/.syntropic137/docker-compose.syntropic137.yaml" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
elif [ -f "docker/docker-compose.yaml" ]; then
    docker compose -f docker/docker-compose.yaml -f docker/docker-compose.dev.yaml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
fi
```

If Docker is not running or no containers exist, note that the stack is down and suggest:
- Published path (`~/.syntropic137/`): `npx @syntropic137/setup` (interactive menu) or `docker compose -f ~/.syntropic137/docker-compose.syntropic137.yaml up -d`
- Source repo: `just selfhost-up` or `just dev`

## 2. API Health

- If SYN_CLI: `$SYN_CLI health`
- Else: `curl -sf "$SYN_API_URL/health"`

If the API is unreachable, note it and suggest checking container status or starting the stack.

## 3. Recent Activity

- If SYN_CLI: `$SYN_CLI metrics show`
- Else: `curl -sf "$SYN_API_URL/api/v1/metrics"`

## Presentation

Present all three sections in a clean, scannable format:

```
Platform Status
═══════════════════════════════════════

Containers
──────────
[container table or "Stack is down"]

API Health
──────────
[health output or "Unreachable"]

Recent Activity
───────────────
[metrics output or "No data"]
```

If everything is healthy, keep the output concise. If something is wrong, add a brief suggestion at the bottom.
