---
model: sonnet
allowed-tools: Bash
---

# /syn-health — API Health Check

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

Run the health check:
- If SYN_CLI is set: `$SYN_CLI health`
- Otherwise: `curl -sf "$SYN_API_URL/health"`

If the command succeeds, display the health response.

If it fails (non-zero exit or connection error):
1. Check if Docker is running: `docker info >/dev/null 2>&1`
2. Detect the installation path and check container status:
   ```bash
   if [ -f "$HOME/.syntropic137/docker-compose.syntropic137.yaml" ]; then
       docker compose -f "$HOME/.syntropic137/docker-compose.syntropic137.yaml" ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null
   elif [ -f "docker/docker-compose.yaml" ]; then
       docker compose -f docker/docker-compose.yaml -f docker/docker-compose.dev.yaml ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null
   fi
   ```
3. If the container exists but API is unhealthy, suggest checking logs:
   - Published path (`~/.syntropic137/`): `docker compose -f ~/.syntropic137/docker-compose.syntropic137.yaml logs`
   - Source repo: `just dev-logs`
4. If no containers are running, suggest starting the stack:
   - Published path: `npx @syntropic137/setup` (interactive menu) or `docker compose -f ~/.syntropic137/docker-compose.syntropic137.yaml up -d`
   - Source repo: `just selfhost-up` or `just dev`
5. If Docker itself is not running, suggest starting Docker Desktop
