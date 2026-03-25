---
model: opus
allowed-tools: Bash, Read, AskUserQuestion
---

# /syn-setup — Syntropic137 Platform Bootstrap

You are running the Syntropic137 setup wizard. Your job is to detect the current state of the platform, report what's working and what's not, then guide the user through fixing any issues.

**Important:** Use the `platform-ops` skill for architecture context, service map, and troubleshooting recipes. After setup completes, mention the other available skills (workflow-management, execution-control, observability, organization) so the user knows what they can do next.

## Phase 1 — Detection (read-only)

Run ALL of these checks. Do not skip any. Capture results silently.

| # | Check | Command | Pass condition |
|---|-------|---------|----------------|
| 1 | In syntropic137 repo | `test -f justfile && grep -q syntropic137 pyproject.toml` | exit 0 |
| 2 | Docker running | `docker info >/dev/null 2>&1` | exit 0 |
| 3 | Prerequisites (uv, just, pnpm, node) | `just setup-check` | exit 0 |
| 4 | Git submodules initialized | `test -d lib/agentic-primitives/.git && test -d lib/event-sourcing-platform/.git` | exit 0 |
| 5 | `.env` exists | `test -f .env` | exit 0 |
| 6 | Python dependencies installed | `test -d .venv` | exit 0 |
| 7 | Dashboard dependencies installed | `test -d apps/syn-dashboard-ui/node_modules` | exit 0 |
| 8 | Workspace image built | `docker image inspect agentic-workspace-claude-cli:latest >/dev/null 2>&1` | exit 0 |
| 9 | Services running | `docker compose -f docker/docker-compose.yaml -f docker/docker-compose.dev.yaml ps --format json 2>/dev/null` | Non-empty, services in "running" state |
| 10 | API healthy | `curl -sf http://localhost:8137/health` | exit 0 with JSON response |

## Phase 2 — Status Report

Present results as a clear table:

```
Syntropic137 Platform Status
═══════════════════════════════════════
 #  Check                    Status
───────────────────────────────────────
 1  Repository               ✓ PASS
 2  Docker                   ✓ PASS
 3  Prerequisites            ✗ FAIL
 ...
═══════════════════════════════════════
```

If everything passes, congratulate the user and suggest trying `/syn-status` or `/syn-sessions list`.

## Phase 3 — Guided Remediation

For each FAIL, offer the fix. **Ask before running anything destructive.**

| Failed Check | Remediation |
|-------------|-------------|
| Not in repo | 1. Check if a `syntropic137` directory exists nearby (`ls ../syntropic137`, `ls ~/Code/*/syntropic137`, `ls ~/projects/*/syntropic137`). 2. If found, tell the user to `cd` into it and re-run `/syn-setup`. 3. If not found, ask the user where they'd like to clone it (suggest `~/Code/syntropic137` or current directory), then offer to run `git clone https://github.com/syntropic137/syntropic137.git <path> && cd <path>`. |
| Docker not running | Tell the user to start Docker Desktop / `dockerd` |
| Prerequisites missing | Check each tool individually. For each missing tool, show the user its **official installation page** and the recommended install command, then ask if they'd like you to run it. Reference docs: **Docker** → https://docs.docker.com/get-docker/; **uv** → https://docs.astral.sh/uv/getting-started/installation/; **just** → https://github.com/casey/just#installation; **Node.js** → https://nodejs.org/en/download/; **pnpm** → https://pnpm.io/installation. Before offering any install command, fetch the tool's install docs page to confirm the current recommended method. Present the exact command you'd run and let the user approve or reject each one. After each install, verify with `command -v <tool>`. |
| Submodules not initialized | Offer to run `just submodules-init` |
| `.env` missing | Offer to run `cp .env.example .env`, then prompt for required API keys (ANTHROPIC_API_KEY, GITHUB_TOKEN) |
| Python deps missing | Offer to run `uv sync` |
| Dashboard deps missing | Offer to run `just dashboard-install` |
| Workspace image missing | Offer to run `just workspace-build` (warn: takes a few minutes) |
| Services not running | Offer to run `just dev` |
| API unhealthy | Run `just dev-logs` and `just dev-doctor` to diagnose, present findings |

Work through failures **in order** (earlier checks are prerequisites for later ones). After fixing each issue, re-run that check to confirm it passes before moving on.

When all checks pass, print the final status table and suggest next steps:
- "Try `/syn-status` for a quick platform overview"
- "Ask me to create a workflow — I know how to design multi-phase agent pipelines"
- "Ask me to set up automatic PR reviews with GitHub trigger rules"
- "Use `/syn-sessions list` to see agent execution history"
