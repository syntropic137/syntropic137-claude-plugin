---
model: sonnet
allowed-tools: Bash
---

# /syn-status — Composite Platform Status

Run the following three checks and present a unified status view:

## 1. Container Status

```bash
docker compose -f docker/docker-compose.yaml -f docker/docker-compose.dev.yaml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
```

If Docker is not running or no containers exist, note that the stack is down and suggest `just dev`.

## 2. API Health

```bash
uv run --package syn-cli syn health
```

If the API is unreachable, note it and suggest checking container status or running `just dev`.

## 3. Recent Activity

```bash
uv run --package syn-cli syn metrics show
```

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
