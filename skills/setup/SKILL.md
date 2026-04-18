---
name: setup
description: Syntropic137 platform setup — 14-stage onboarding wizard, 1Password, Cloudflare tunnels, Docker Compose stack, justfile recipes, secrets management, and troubleshooting
---

# Setup & Infrastructure — Syntropic137

Use this knowledge when the user asks about setting up the platform, configuring secrets, managing the Docker stack, understanding the justfile recipes, or troubleshooting infrastructure issues.

## API URL — `SYN_API_URL`

The platform can run locally or behind a public hostname (Cloudflare tunnel, VPS, etc.). All API calls should use `SYN_API_URL` as the base URL, resolved with this priority:

| Priority | Source | Example |
|----------|--------|---------|
| 1 | `SYN_API_URL` env var (explicit override) | `https://syn.example.com` |
| 2 | `SYN_PUBLIC_HOSTNAME` from `~/.syntropic137/.env` | → `https://syn.example.com` |
| 3 | Default | `http://localhost:8137` |

**Resolution pattern (bash):**
```bash
if [ -n "${SYN_API_URL:-}" ]; then
    SYN_API_URL="$SYN_API_URL"
elif [ -f "$HOME/.syntropic137/.env" ]; then
    _hostname=$(grep '^SYN_PUBLIC_HOSTNAME=' "$HOME/.syntropic137/.env" 2>/dev/null | cut -d= -f2 | tr -d '"' | tr -d "'")
    [ -n "$_hostname" ] && SYN_API_URL="https://$_hostname"
fi
SYN_API_URL="${SYN_API_URL:-http://localhost:8137}"
```

**All API endpoints are relative to this base URL:**
- Health: `$SYN_API_URL/health`
- Sessions: `$SYN_API_URL/api/v1/sessions`
- Costs: `$SYN_API_URL/api/v1/costs/summary`
- Metrics: `$SYN_API_URL/api/v1/metrics`
- Events: `$SYN_API_URL/api/v1/events/sessions/<id>`
- Triggers: `$SYN_API_URL/api/v1/triggers`

Every plugin command resolves this before making API calls. If the user is on a remote server, `SYN_PUBLIC_HOSTNAME` gets set during Cloudflare tunnel setup (Phase 8 of `/syn-setup`).

## Onboarding Paths

### Published Path (Self-Hosters)

Self-hosters install to `~/.syntropic137/` via `npx @syntropic137/setup`. No `uv`, `just`, or source repo required.

```bash
npx @syntropic137/setup start   # Start the stack
npx @syntropic137/setup stop    # Stop the stack
npx @syntropic137/setup logs    # View logs
npx @syntropic137/setup update  # Pull latest images and restart
```

The published compose file is `docker-compose.syntropic137.yaml` in `~/.syntropic137/`. All stack management goes through `npx @syntropic137/setup` or direct `docker compose -f ~/.syntropic137/docker-compose.syntropic137.yaml` commands.

### Quick Dev Setup (Source Repo)

```bash
just onboard-dev              # Default: submodules → deps → GitHub App → stack
just onboard-dev --skip-github  # Skip GitHub App (minimal local dev)
just onboard-dev --tunnel     # Include Cloudflare tunnel
just onboard-dev --1password  # Include 1Password secret management
```

`onboard-dev` does:
1. Initialize git submodules (if missing)
2. Create `.env` from template with dev defaults
3. `uv sync` Python dependencies
4. Build workspace image in background (if missing)
5. Set up webhook delivery (Cloudflare tunnel or Smee)
6. Configure GitHub App (unless `--skip-github`)
7. Wait for workspace build
8. Start full dev stack (`just dev`)

### Full Selfhost Setup (Source Repo)

```bash
just onboard                  # Interactive wizard (14 stages)
just onboard --skip-github    # Skip GitHub App
just onboard --non-interactive  # CI/CD mode (reads from env vars)
just onboard --stage <name>   # Re-run a specific stage
```

### Setup Stages (14 total)

| # | Stage | What It Does | Can Re-run? |
|---|-------|-------------|-------------|
| 1 | `detect_environment` | Choose: development, selfhost, beta, staging, production | Yes |
| 2 | `check_prerequisites` | Validate Docker ≥24, Compose ≥2.20, Python ≥3.12; uv/just/git for source repo only | Yes |
| 3 | `init_submodules` | `git submodule update --init --recursive` | Yes |
| 4 | `generate_secrets` | Create `db-password.secret`, `redis-password.secret` (32-byte hex) | Yes |
| 5 | `configure_1password` | Optional: set up 1Password vault integration | Yes |
| 6 | `validate_environment` | Audit all env vars, show status table | Yes |
| 7 | `configure_cloudflare` | Cloudflare tunnel token + domain for external access | Yes |
| 8 | `configure_smee` | Dev fallback: Smee.io webhook proxy | Yes |
| 9 | `configure_github_app` | Create/connect GitHub App (manifest flow or manual) | Yes |
| 10 | `configure_env` | Create `.env` files from templates, write defaults | Yes |
| 11 | `security_audit` | Advisory checks (never blocks) | Yes |
| 12 | `build_and_start` | `docker compose up -d --build` | Yes |
| 13 | `wait_for_health` | Poll service health (180s timeout) | Yes |
| 14 | `seed_workflows` | Load example workflows into event store | Yes |

Re-run any stage: `just setup-stage <stage_name>`

## Environment Configuration

### Two-File Separation

| File | Purpose |
|------|---------|
| **Root `.env`** | Application config: GitHub creds, API keys, app settings |
| **`infra/.env`** | Infrastructure config: Docker, resource limits, tunnel, secrets |

### Root `.env` — Key Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `APP_ENVIRONMENT` | Yes | `development`, `selfhost`, `beta`, `staging`, `production` |
| `SYN_GITHUB_APP_ID` | For GitHub | GitHub App ID |
| `SYN_GITHUB_APP_NAME` | For GitHub | GitHub App slug |
| `SYN_GITHUB_PRIVATE_KEY` | For GitHub | Base64-encoded PEM private key |
| `SYN_GITHUB_WEBHOOK_SECRET` | For GitHub | Webhook HMAC secret |
| `ANTHROPIC_API_KEY` | For agents | Anthropic API key |
| `CLAUDE_CODE_OAUTH_TOKEN` | Alt agents | Alternative to API key |
| `DEV__SMEE_URL` | Dev only | Smee.io webhook proxy URL |
| `OP_SERVICE_ACCOUNT_TOKEN_SYN137_DEV` | 1Password | Service account token (per vault) |

### `infra/.env` — Key Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CLOUDFLARE_TUNNEL_TOKEN` | For tunnel | Cloudflare tunnel token |
| `SYN_DOMAIN` | For tunnel | Public domain (e.g., `syn.yourdomain.com`) |
| `POSTGRES_PASSWORD` | Yes | Database password |
| `POSTGRES_DB` | Yes | Database name (default: `syntropic137`) |
| `MINIO_ROOT_USER` | Yes | MinIO access key |
| `MINIO_ROOT_PASSWORD` | Yes | MinIO secret key |
| `REDIS_PASSWORD` | Yes | Redis password |
| `SYN_API_PASSWORD` | Selfhost | Basic auth password for gateway |
| `INCLUDE_OP_CLI` | 1Password | Set to `1` to enable 1Password in containers |

### Generating .env from scratch

```bash
just gen-env         # Generate .env.example from Settings class
cp .env.example .env # Then fill in values
```

## 1Password Integration

### How It Works

- Vault name derived from environment: `development` → `syn137-dev`, `production` → `syn137-prod`
- Service Account Token stored in:
  - **macOS**: Keychain entry `SYN_OP_SERVICE_ACCOUNT_TOKEN_SYN137_{ENV}`
  - **Linux/CI**: Environment variable
  - **Dev**: Root `.env` as `OP_SERVICE_ACCOUNT_TOKEN_SYN137_DEV`
- When `INCLUDE_OP_CLI=1` in `infra/.env`, Docker containers include `op` CLI
- Selfhost entrypoint resolves 1Password references before starting services

### Managing Tokens

```bash
just secrets-store-token    # Store SA token in macOS Keychain
just secrets-delete-token   # Remove from Keychain
```

### Vault Structure

The wizard saves to a `syntropic137-config` item in the vault with fields:
- GitHub App credentials
- Cloudflare tunnel token
- Database passwords
- API keys

## Cloudflare Tunnel Setup

### Purpose

Zero-trust external access — webhooks from GitHub, remote dashboard access, API access.

### Flow

1. Create Cloudflare account + add domain
2. Go to Zero Trust dashboard → Network → Tunnels → Create
3. Copy the tunnel token or install command
4. Run `just onboard` → stage 7 asks for token + domain
5. Writes `CLOUDFLARE_TUNNEL_TOKEN` and `SYN_DOMAIN` to `infra/.env`
6. `cloudflared` container runs in Docker stack
7. Set tunnel's public hostname service URL to `http://gateway:8081` in Cloudflare dashboard

### Compose Overlays

- `docker-compose.cloudflare.yaml` — adds `cloudflared` service (selfhost)
- `docker-compose.dev-cloudflare.yaml` — adds tunnel to dev stack

## Secrets Management

```bash
just secrets-generate   # Create db-password.secret, redis-password.secret
just secrets-check      # Verify all secrets exist
just secrets-rotate     # Regenerate all secrets (requires restart)
just secrets-seal       # Encrypt with passphrase (safe to commit .enc files)
just secrets-unseal     # Decrypt from .enc files
```

### Secret Files

Located in `infra/docker/secrets/`:
- `db-password.secret` (32-byte hex, permissions 600)
- `redis-password.secret` (32-byte hex, permissions 600)
- `github-private-key.pem` (optional, base64 in .env preferred)
- `cloudflare-tunnel-token.secret` (if using tunnel)

## Docker Compose Stack

### Compose Variants

| File | Purpose | Used By |
|------|---------|---------|
| `docker-compose.yaml` | Base services (abstract, no ports) | All |
| `docker-compose.dev.yaml` | Dev: ports, volumes, `.env` | `just dev` |
| `docker-compose.test.yaml` | Test: ports +10000, ephemeral | `just test-stack` |
| `docker-compose.selfhost.yaml` | Selfhost: security hardening, secrets, resource limits | `just selfhost-up` |
| `docker-compose.cloudflare.yaml` | Adds Cloudflare tunnel | `just selfhost-up-tunnel` |
| `docker-compose.dev-cloudflare.yaml` | Adds tunnel to dev | `just dev --tunnel` |

### Services & Ports (Dev)

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| TimescaleDB | `syn-db` | 5432 | PostgreSQL + time-series |
| Event Store | `syn-event-store` | 50051 | Rust gRPC event store |
| Collector | `syn-collector` | 8080 | Event ingestion |
| API (`syn-api`) | 8137 | FastAPI HTTP server |
| Redis | `syn-redis` | 6379 | Cache + pub/sub |
| MinIO | `syn-minio` | 9000/9001 | S3 artifact storage |
| Envoy Proxy | `syn-envoy` | 8081/9901 | Token injection proxy |
| Dashboard | (host process) | 5173 | Vite + React |
| Pulse | (host process) | 5174 | Metrics UI |

### Selfhost Security Hardening

- `read_only: true` filesystem
- `cap_drop: ALL` + minimal `cap_add`
- `no-new-privileges` security opt
- Secrets mounted from files (not env vars)
- Resource limits per service
- JSON logging with rotation
- Gateway with optional basic auth

## Justfile Recipe Reference

### Dev Stack

| Recipe | Description |
|--------|-------------|
| `just dev` | Start full dev env (backend + frontend + webhooks) |
| `just dev-fresh` | Wipe data + restart from scratch |
| `just dev-stop` | Stop (preserves data) |
| `just dev-down` | Remove containers (preserves volumes) |
| `just dev-logs` | Tail all service logs |
| `just dev-doctor` | Diagnose .env and config issues |

### Selfhost

| Recipe | Description |
|--------|-------------|
| `just selfhost-up` | Start selfhost stack (no tunnel) |
| `just selfhost-up-tunnel` | Start with Cloudflare tunnel |
| `just selfhost-down` | Stop (auto-detects tunnel) |
| `just selfhost-status` | Container status + access URLs |
| `just selfhost-logs [service]` | View logs |
| `just selfhost-restart <svc>` | Restart specific service |
| `just selfhost-update` | Pull + rebuild + restart |
| `just selfhost-reset` | Nuclear: wipe volumes + restart |
| `just selfhost-seed` | Seed workflows + triggers |

### Building

| Recipe | Description |
|--------|-------------|
| `just workspace-build` | Build Claude workspace Docker image |
| `just workspace-versions` | List workspace image versions |
| `just proxy-build` | Build egress proxy image |

### QA & Testing

| Recipe | Description |
|--------|-------------|
| `just qa` | Full QA: lint + format + typecheck + test + vsa |
| `just qa-full` | QA + coverage report |
| `just check` | Fast static checks (pre-commit) |
| `just check-fix` | Static checks with auto-fix |
| `just test` | All tests |
| `just test-unit` | Unit tests (fast, parallel) |
| `just test-integration` | Integration tests |
| `just test-cov` | Tests with coverage (80% threshold) |
| `just test-stack` | Start ephemeral test infra (ports +10000) |
| `just test-stack-down` | Tear down test infra |
| `just typecheck` | Pyright strict mode |
| `just lint` | Ruff linting |
| `just format` | Ruff formatting |
| `just vsa-validate` | VSA architecture validation |

### Health & Monitoring

| Recipe | Description |
|--------|-------------|
| `just health-check` | Health check all services |
| `just health-wait [timeout]` | Wait for services (default 120s) |
| `just health-json` | Health as JSON (for CI) |

### Submodules

| Recipe | Description |
|--------|-------------|
| `just submodules-init` | `git submodule update --init --recursive` |
| `just submodules-update` | Update to latest remote |

### Seed Data

| Recipe | Description |
|--------|-------------|
| `just seed-workflows` | Seed example workflows |
| `just seed-triggers` | Seed trigger presets |
| `just seed-organization` | Seed org/system/repo |
| `just seed-all` | All of the above |

### Dependencies

| Recipe | Description |
|--------|-------------|
| `just sync` | `uv sync` |
| `just sync-es` | Reinstall event-sourcing-platform |
| `just lock` | `uv lock` |
| `just update` | `uv lock --upgrade && uv sync` |
| `just dashboard-install` | Install dashboard + UI deps |
| `just clean` | Remove .venv, caches, Docker containers |

## Troubleshooting

### "just dev fails"

1. Check Docker: `docker info`
2. Check prerequisites: `just setup-check`
3. Check env: `just dev-doctor`
4. Check ports: another process on 5432, 8137, etc.?

### "Services unhealthy after start"

1. `just health-check` — see which service is down
2. `just dev-logs` — check service logs
3. Common: TimescaleDB slow to start → event store can't connect → API can't start
4. Wait and retry: `just health-wait 180`

### "Workspace build fails"

1. Check Docker disk space
2. Check agentic-primitives submodule: `cd lib/agentic-primitives && git status`
3. Rebuild: `just workspace-build`
4. Apple Silicon note: Rust components build slower (~5-10 min)

### "Webhooks not arriving"

1. Check delivery method: `grep DEV__SMEE_URL .env` or `grep CLOUDFLARE_TUNNEL_TOKEN infra/.env`
2. Smee: `just dev-webhooks-logs`
3. Cloudflare: check tunnel status in Zero Trust dashboard
4. Test: open a PR → check API logs for webhook receipt

### "1Password not resolving"

1. Check `INCLUDE_OP_CLI=1` in `infra/.env`
2. Check SA token: `just secrets-store-token` (macOS) or env var
3. Check vault exists: `op vault list` should show `syn137-dev`
4. Check item exists: `op item get syntropic137-config --vault syn137-dev`
