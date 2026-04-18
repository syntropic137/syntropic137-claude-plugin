---
name: setup
description: Syntropic137 platform setup; npx setup CLI, Docker Compose stack, justfile recipes, secrets management, and troubleshooting
---

# Setup & Infrastructure: Syntropic137

When something stops working at the infrastructure level (services won't start, webhooks aren't arriving, the workspace image is stale), this skill has the answers. Setup is handled by a single CLI command that covers the entire lifecycle.

## Which Path Is Right For You?

**Self-hosters** (running `~/.syntropic137/` install):
```bash
npx @syntropic137/setup        # detect and update/add features on existing install
npx @syntropic137/setup init   # fresh install: full interactive wizard
```
This handles Docker checks, secret generation, API keys, GitHub App, Cloudflare tunnels, and health checks. The `syn` CLI is installed globally during setup.

**Source repo developers:**
```bash
just onboard-dev              # fast path: deps → GitHub App → dev stack
just onboard-dev --skip-github  # minimal, no GitHub App
just onboard                  # full 14-stage wizard (mirrors the npx experience)
```

**Not sure which you are?** If you have a `~/.syntropic137/` directory, you're on the self-hosted path. If you have the source repo cloned, use `just`.

## API URL Resolution

Every command that hits the platform API resolves the base URL in this order:
1. `SYN_API_URL` env var (explicit override)
2. `SYN_PUBLIC_HOSTNAME` from `~/.syntropic137/.env` (for published/tunneled installs)
3. Default: `http://localhost:8137`

If you're getting connection errors, verify which URL is being used. Remote installs must have `SYN_PUBLIC_HOSTNAME` set or `SYN_API_URL` in the environment.

## Setup Stages (14 total, all re-runnable)

The wizard runs these in order. You can re-run any individual stage:

| # | Stage | Purpose |
|---|-------|---------|
| 1 | `detect_environment` | dev / selfhost / production |
| 2 | `check_prerequisites` | Docker ≥24, Compose ≥2.20, Python ≥3.12 |
| 3 | `init_submodules` | git submodule init |
| 4 | `generate_secrets` | db/redis passwords (32-byte hex) |
| 5 | `configure_1password` | optional vault integration |
| 6 | `validate_environment` | audit all env vars |
| 7 | `configure_cloudflare` | tunnel token + domain |
| 8 | `configure_smee` | dev webhook proxy fallback |
| 9 | `configure_github_app` | create/connect GitHub App |
| 10 | `configure_env` | write `.env` from templates |
| 11 | `security_audit` | advisory checks (never blocks) |
| 12 | `build_and_start` | `docker compose up -d --build` |
| 13 | `wait_for_health` | poll health (180s timeout) |
| 14 | `seed_workflows` | load example workflows |

Re-run a single stage: `just setup-stage <stage_name>` (source repo) or `npx @syntropic137/setup --stage <name>` (self-hosted).

## Key Environment Variables

Two files are kept separate to isolate application config from infrastructure config:

**Root `.env`** (application): `ANTHROPIC_API_KEY`, `SYN_GITHUB_APP_ID`, `SYN_GITHUB_APP_NAME`, `SYN_GITHUB_WEBHOOK_SECRET`, `APP_ENVIRONMENT`

**`infra/.env`** (infrastructure): `CLOUDFLARE_TUNNEL_TOKEN`, `SYN_PUBLIC_HOSTNAME`, `POSTGRES_PASSWORD`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `REDIS_PASSWORD`

Run `just dev-doctor` to diagnose env var issues.

## Secrets Management

```bash
just secrets-generate   # create db-password.secret, redis-password.secret
just secrets-check      # verify all secrets exist
just secrets-rotate     # regenerate (requires restart)
just secrets-seal       # encrypt for safe commit
just secrets-unseal     # decrypt
```

In selfhost, the GitHub App PEM is a Docker secret mounted at runtime; it never lands on disk as a file. The compose file handles the mount automatically.

## Troubleshooting Decision Tree

**Services won't start:**
1. `docker info` (is Docker running?)
2. `just setup-check` (prerequisites met?)
3. `just dev-doctor` (env vars correct?)
4. `just health-check` (which service is unhealthy?)

**TimescaleDB slow or unhealthy:** Common root cause for cascading failures. Event Store can't connect, so the API can't start. Run `just health-wait 180` and retry before digging deeper.

**Workspace build fails:** Check disk space, check `lib/agentic-primitives` submodule status, then `just workspace-build`. Apple Silicon: Rust build takes 5-10 min, so don't interrupt it.

**Webhooks not arriving:** Check `grep DEV__SMEE_URL .env`; if empty, you're using Cloudflare. Check Cloudflare tunnel status in Zero Trust dashboard. Dev: `just dev-webhooks-logs`.

**1Password not resolving:** Check `INCLUDE_OP_CLI=1` in `infra/.env`, then `op vault list` to confirm `syn137-dev` vault exists.

## Docker Stack Quick Reference

Start/stop dev: `just dev` / `just dev-stop`

Start/stop selfhost: `just selfhost-up` / `just selfhost-down`

View logs: `just dev-logs` or `just selfhost-logs [service]`

Nuclear reset (destroys data): `just dev-down` / `just selfhost-reset`

## Integration

After setup completes: configure the GitHub App with github-automation, design workflows with workflow-management, then monitor with platform-ops. Run `/syn-setup` from Claude Code to get guided setup instructions.
