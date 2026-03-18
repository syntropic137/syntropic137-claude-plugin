---
model: sonnet
allowed-tools: Bash
---

# /syn-health — API Health Check

Run the health check:

```bash
uv run --package syn-cli syn health
```

If the command succeeds, display the health response.

If it fails (non-zero exit or connection error):
1. Check if Docker is running: `docker info >/dev/null 2>&1`
2. Check if the API container is running: `docker compose -f docker/docker-compose.yaml -f docker/docker-compose.dev.yaml ps api --format "table {{.Name}}\t{{.Status}}" 2>/dev/null`
3. If the container exists but API is unhealthy, suggest: `just dev-logs` to check logs
4. If no containers are running, suggest: `just dev` to start the stack
5. If Docker itself is not running, suggest starting Docker Desktop
