# Platform Operations — Syntropic137

Use this knowledge when troubleshooting, diagnosing, or operating the Syntropic137 platform.

## Architecture Overview

Syntropic137 orchestrates AI agent execution in isolated Docker workspaces and captures every event for observability. Two core capabilities:

- **Orchestration**: Workspace lifecycle, secure token handling, GitHub App integration
- **Observability**: Tool use, tokens, costs, errors — streamed to a real-time dashboard

### Two-Lane Architecture

1. **Lane 1 — Event Sourcing (Domain Truth)**: Aggregates are the sole decision-makers. Commands in, events out. Infrastructure handlers react to events and report results via new commands.
2. **Lane 2 — Observability (Telemetry)**: Token counts, tool traces, timing. Append-only, never replayed for state.

## Service Map

| Service | Port | Description |
|---------|------|-------------|
| API (`syn-api`) | 8000 | FastAPI HTTP server — routes + application services |
| Collector (`syn-collector`) | 8080 | Event ingestion API |
| Event Store | 50051 | Rust gRPC event store |
| TimescaleDB | 5432 | PostgreSQL + TimescaleDB for projections + observability |
| Redis | 6379 | Caching and pub/sub |
| MinIO | 9000 (S3), 9001 (console) | Artifact storage |
| Envoy Proxy | 8081, 9901 (admin) | Shared proxy for API key injection |
| Dashboard | 5173 (dev) | Vite + React real-time dashboard |

## Common Tasks

| Task | Command |
|------|---------|
| Start dev stack | `just dev` |
| Stop dev stack | `just dev-stop` |
| Tear down (remove volumes) | `just dev-down` |
| View logs | `just dev-logs` |
| Environment diagnostics | `just dev-doctor` |
| Run full QA suite | `just qa` |
| Build workspace image | `just workspace-build` |
| Initialize submodules | `just submodules-init` |
| Install dashboard deps | `just dashboard-install` |
| Check prerequisites | `just setup-check` |
| Seed sample data | `just seed-all` |
| Run CLI commands | `just cli <args>` or `uv run --package syn-cli syn <args>` |

## Troubleshooting Recipes

### API Not Responding

1. Check if containers are running: `docker compose -f docker/docker-compose.yaml -f docker/docker-compose.dev.yaml ps`
2. Check API logs: `just dev-logs` (or `docker compose ... logs api --tail 50`)
3. Check health endpoint directly: `curl -sf http://localhost:8137/health`
4. If the API container is restarting, check for dependency issues (TimescaleDB, Event Store)
5. Run `just dev-doctor` for automated diagnostics

### Event Store Issues

1. The event store is a Rust gRPC service on port 50051
2. Check its logs: `docker compose ... logs event-store --tail 50`
3. It depends on TimescaleDB — ensure that's healthy first
4. If the event store fails to start, check if port 50051 is already in use

### Stale Workspace Image

1. The workspace image (`agentic-workspace-claude-cli:latest`) is built from the Dockerfile in the repo
2. Rebuild with: `just workspace-build`
3. If agents fail with missing tools, the image likely needs rebuilding

### Database Issues

1. TimescaleDB runs on port 5432
2. Check status: `docker compose ... ps timescaledb`
3. If stuck, try: `just dev-stop && just dev` (restart)
4. Nuclear option: `just dev-down` (destroys volumes — you'll lose local data)

### Dashboard Not Loading

1. Ensure deps are installed: `just dashboard-install`
2. Start frontend dev server: `just dashboard-frontend`
3. Dashboard connects to API on port 8000 — ensure API is healthy

## Workspace Management

Workspaces are isolated Docker containers where agents execute. Each workflow phase gets its own workspace.

### Workspace Lifecycle

```
PENDING → CREATING → READY → RUNNING → DESTROYED
                                    ↘ ERROR
```

### Token Injection (Security Model)

Agents never see real API keys. The Envoy proxy sidecar injects credentials:

1. **Setup phase**: `InjectTokensCommand` sends real keys to Envoy proxy (port 8081)
2. **Agent phase**: Agent holds placeholder tokens (`proxy-managed`), Envoy intercepts outbound API calls and swaps in real credentials
3. **Teardown**: Workspace destroyed, tokens cleared

This means:
- Agents can't exfiltrate real credentials
- Token rotation happens at the proxy, not per-workspace
- Network isolation: agents on `agent-net` can only reach Envoy, not the internet directly

### Building the Workspace Image

```bash
just workspace-build
```

This builds `agentic-workspace-claude-cli:latest` with Claude CLI, tools, and the agent runtime. Rebuild when:
- Claude CLI version changes
- New tools need to be available to agents
- Base image security updates

## Docker Compose Variants

| File | Purpose |
|------|---------|
| `docker-compose.yaml` | Base services (no ports, no volumes) |
| `docker-compose.dev.yaml` | Dev override: exposed ports, local volumes, `.env` |
| `docker-compose.test.yaml` | Test stack: ports +10000, ephemeral |
| `docker-compose.selfhost.yaml` | Self-hosting with multi-compose |
| `docker-compose.cloudflare.yaml` | Cloudflare tunnel integration |

Dev stack command pattern:
```bash
docker compose -f docker/docker-compose.yaml -f docker/docker-compose.dev.yaml <command>
```

## QA & Testing

```bash
just qa                    # Full suite: lint, format, typecheck, test, coverage, vsa-validate
just lint                  # Ruff + Pylint
just fmt                   # Auto-format
just typecheck             # Pyright (strict mode)
just test                  # All tests
just test-unit             # Unit tests only (fast, parallel)
just test-integration      # Integration tests (needs test stack)
just test-cov              # Coverage report (80% threshold)
just vsa-validate          # Vertical Slice Architecture validation
just test-stack            # Start ephemeral test infrastructure
just test-stack-down       # Tear down test infrastructure
```

## Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `SYN_API_URL` | API base URL (default: `http://localhost:8137`) |
| `ANTHROPIC_API_KEY` | Required for agent execution |
| `GITHUB_TOKEN` | Required for GitHub App integration |
| `GITHUB_APP_ID` | GitHub App ID |
| `SYN_GITHUB_PRIVATE_KEY` | GitHub App private key |
| `GITHUB_WEBHOOK_SECRET` | Webhook signature verification |
| `APP_ENVIRONMENT` | `development`, `beta`, `staging` |
| `DATABASE_URL` | PostgreSQL connection (auto in Docker) |
| `EVENT_STORE_URL` | gRPC event store (auto in Docker) |
| `MINIO_ROOT_USER` | MinIO access key |
| `MINIO_ROOT_PASSWORD` | MinIO secret key |

## Project Structure Quick Reference

```
syntropic137/
├── apps/
│   ├── syn-api/               # FastAPI server (routes + v1 services)
│   ├── syn-cli/               # CLI tool ("syn")
│   └── syn-dashboard-ui/      # React dashboard (Vite)
├── packages/
│   ├── syn-domain/            # Domain events, aggregates, projections
│   ├── syn-adapters/          # Orchestration + observability adapters
│   ├── syn-collector/         # Event ingestion + JSONL watcher
│   └── syn-shared/            # Shared settings, configuration
├── lib/
│   ├── agentic-primitives/    # Agent building blocks (submodule)
│   └── event-sourcing-platform/ # ES infrastructure (submodule)
├── docker/                    # Compose files (base, dev, test, selfhost)
└── infra/                     # Setup wizard, secrets
```

### Bounded Contexts (Domain Layer)

| Context | Aggregates | Purpose |
|---------|------------|---------|
| `orchestration` | Workspace, WorkflowTemplate, WorkflowExecution | Workflow execution and workspace management |
| `agent_sessions` | AgentSession | Agent sessions and observability |
| `github` | Installation, TriggerRule | GitHub App integration, webhook triggers |
| `artifacts` | Artifact | Artifact storage (code, logs, analysis) |
| `organization` | Organization, System, Repo | Org hierarchy, system/repo management |
