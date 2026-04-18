---
name: platform-ops
description: Syntropic137 infrastructure operations; service map, Docker stack, workspace lifecycle, Envoy token injection security, QA/testing commands, and troubleshooting recipes
---

# Platform Operations: Syntropic137

When something is broken at the infrastructure level (a service is down, a workspace won't build, API calls are failing), this is the reference for diagnosing and fixing it. **Start with `just health-check` before reading logs.** It pinpoints the failing service in seconds and saves you from grepping through megabytes of log output.

## When to Use This Skill

Use this when you are: diagnosing a service that won't start, understanding the security model for agent token injection, running QA, operating the selfhost stack, or navigating the project structure.

Not needed for first-time setup; use the setup skill for that. Not needed for session costs or observability data; use the observability skill.

## Architecture at a Glance

Syntropic137 has two core capabilities:
- **Orchestration**: workspace lifecycle, GitHub App, secure token handling via Envoy proxy
- **Observability**: every tool call, token count, and cost streamed to a real-time dashboard

The platform is split into two lanes: **Domain State** (event-sourced aggregates, where `aggregates decide, handlers execute`) and **Telemetry** (append-only time-series data). Both feed the same API but are queried differently.

## Service Map

| Service | Port | Role |
|---------|------|------|
| `syn-api` | 8137 | FastAPI HTTP: all routes and application services |
| `syn-collector` | 8080 | Event ingestion from agents |
| Event Store | 50051 | Rust gRPC event store |
| TimescaleDB | 5432 | PostgreSQL + time-series (projections + telemetry) |
| Redis | 6379 | Cache and pub/sub |
| MinIO | 9000/9001 | S3-compatible artifact storage |
| Envoy Proxy | 8081/9901 | API key injection sidecar |
| Dashboard | 5173 (dev) | Vite + React real-time UI |

**TimescaleDB is the most critical dependency.** If it's unhealthy, the Event Store can't connect, the API can't start, and nothing works. Always check TimescaleDB first when diagnosing cascading failures.

## Common Operations

| Task | Command |
|------|---------|
| Start dev stack | `just dev` |
| Stop (preserve data) | `just dev-stop` |
| Remove containers (preserve volumes) | `just dev-down` |
| View logs | `just dev-logs` |
| Diagnose env issues | `just dev-doctor` |
| Check health | `just health-check` |
| Wait for health | `just health-wait 180` |
| Build workspace image | `just workspace-build` |
| Run full QA | `just qa` |
| Seed sample data | `just seed-all` |

## Workspace Security Model (Token Injection)

Agents never see real API keys. The Envoy proxy sidecar (port 8081) handles credential injection:

1. Before agent launch: `InjectTokensCommand` sends real keys to Envoy
2. Agent holds placeholder tokens (`proxy-managed`) 
3. Envoy intercepts outbound API calls and swaps in real credentials
4. After execution: workspace destroyed, tokens cleared

This means agents can't exfiltrate credentials even if the prompt is hijacked. Network isolation: agents on `agent-net` can only reach Envoy, not the internet directly.

## Workspace Lifecycle

```
PENDING → CREATING → READY → RUNNING → DESTROYED
                                     ↘ ERROR
```

Each workflow phase gets its own isolated workspace. Rebuild the image when tools need updating: `just workspace-build`. Signs a rebuild is needed: agents failing with "command not found", missing CLIs, or security CVEs in the base image.

## Troubleshooting Recipes

**API not responding:**
1. `just health-check` to identify which service is down
2. `docker compose ps` to check if containers are actually running
3. `just dev-logs` to look for startup errors
4. Check if TimescaleDB finished starting before the API tried to connect

**Event Store not connecting:**
Event Store (port 50051) is a Rust gRPC service that depends on TimescaleDB. If TimescaleDB starts slow, Event Store will fail to connect on boot. Fix: `just dev-stop && just dev` (restart after DB is healthy).

**Stale workspace image:**
Agents fail with missing tools or old Claude CLI version. Fix: `just workspace-build`. On Apple Silicon, allow 5-10 min for the Rust components.

**Database issues:**
`just dev-stop && just dev` for soft restart. If tables are corrupted: `just dev-down` destroys volumes and you'll lose local data.

**Dashboard not loading:**
`just dashboard-install` then `just dashboard-frontend`. Dashboard requires the API to be healthy on port 8137.

## QA Commands

```bash
just qa              # full suite: lint + typecheck + test + coverage + vsa-validate
just test-unit       # fast, parallel
just test-integration  # needs test stack running
just typecheck       # Pyright strict mode
just lint            # Ruff
just vsa-validate    # Vertical Slice Architecture validation
```

## Integration

Use setup skill for first-time configuration. After diagnosis, use execution-control to check execution state or observability to check session health. Run `just dev-doctor` for automated env diagnostics before filing a bug.
