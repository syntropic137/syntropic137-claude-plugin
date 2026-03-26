---
model: opus
allowed-tools: Bash, Read, AskUserQuestion
---

# /syn-setup — Syntropic137 Self-Host Bootstrap

You are running the Syntropic137 self-host setup wizard. Your job is to detect the current state of the platform, report what's working and what's not, then guide the user through fixing any issues.

**Important:** This is the **self-host** setup path. Self-hosters run pre-built Docker images — they do NOT install frontend dependencies locally or use dev compose files. The core setup tool is `just onboard`, which handles submodules, secrets, GitHub App, Cloudflare tunnel, 1Password, and building/starting the stack.

Use the `platform-ops` skill for architecture context, service map, and troubleshooting recipes. After setup completes, mention the other available skills (workflow-management, execution-control, observability, organization) so the user knows what they can do next.

## Phase 1 — Detection (read-only)

Run ALL of these checks. Do not skip any. Capture results silently.

| # | Check | Command | Pass condition |
|---|-------|---------|----------------|
| 1 | In syntropic137 repo | `test -f justfile && grep -q syntropic137 pyproject.toml` | exit 0 |
| 2 | Docker running | `docker info >/dev/null 2>&1` | exit 0 |
| 3 | Prerequisites (uv, just, docker) | `command -v uv && command -v just && command -v docker` | All exit 0 |
| 4 | Git submodules initialized | `test -d lib/agentic-primitives/.git && test -d lib/event-sourcing-platform/.git` | exit 0 |
| 5 | `.env` exists | `test -f .env` | exit 0 |
| 6 | `infra/.env` exists | `test -f infra/.env` | exit 0 |
| 7 | GitHub App configured | `grep -q 'SYN_GITHUB_APP_ID=' .env && grep -v '^#' .env \| grep -q 'SYN_GITHUB_APP_ID=.'` | exit 0 |
| 8 | Cloudflare or no-tunnel | `grep -q 'CLOUDFLARE_TUNNEL_TOKEN=.' .env \|\| grep -q 'SELFHOST_NO_TUNNEL=true' .env` | exit 0 |
| 9 | API password set | `grep -q 'SYN_API_PASSWORD=.' .env` | exit 0 |
| 10 | Workspace image built | `docker image inspect agentic-workspace-claude-cli:latest >/dev/null 2>&1` | exit 0 |
| 11 | Services running | `docker compose ls --format json 2>/dev/null` | syntropic137 stack present and running |
| 12 | API healthy | `curl -sf http://localhost:8137/health` | exit 0 with JSON response |

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

Work through failures **in order** (earlier checks are prerequisites for later ones).

### Checks 1–3: Fix individually

| Failed Check | Remediation |
|-------------|-------------|
| Not in repo | 1. Check if a `syntropic137` directory exists nearby (`ls ../syntropic137`, `ls ~/Code/*/syntropic137`, `ls ~/projects/*/syntropic137`). 2. If found, tell the user to `cd` into it and re-run `/syn-setup`. 3. If not found, ask the user where they'd like to clone it (suggest `~/Code/syntropic137` or current directory), then offer to run `git clone https://github.com/syntropic137/syntropic137.git <path>`. After clone completes, tell the user to `cd <path>` themselves and re-run `/syn-setup` — do NOT use `cd` inside a Bash tool call (it doesn't change the user's shell working directory). |
| Docker not running | Tell the user to start Docker Desktop / `dockerd` |
| Prerequisites missing | Check each tool individually with `command -v`. For each missing tool, show the user its **official installation page** and the recommended install command, then ask if they'd like you to run it. Reference docs: **Docker** → https://docs.docker.com/get-docker/; **uv** → https://docs.astral.sh/uv/getting-started/installation/; **just** → https://github.com/casey/just#installation. Before offering any install command, fetch the tool's install docs page to confirm the current recommended method. Present the exact command you'd run and let the user approve or reject each one. After each install, verify with `command -v <tool>`. |

### Checks 4–10: Run `just onboard`

If **any** of checks 4–10 fail, the remediation is a single command: `just onboard`.

Tell the user: *"The onboarding wizard handles everything from here — submodules, secrets, GitHub App, Cloudflare tunnel, and building the stack. Let's run it."*

Run `just onboard` and let the interactive wizard guide the user through the remaining setup. Do NOT attempt to fix checks 4–10 individually with piecemeal commands — `just onboard` is designed to handle all of them as a cohesive flow.

After `just onboard` completes, ask the user which deployment mode they want:
- **With Cloudflare tunnel (recommended):** `just selfhost-up-tunnel`
- **Without tunnel:** `just selfhost-up`

### Check 11–12: Diagnose running services

| Failed Check | Remediation |
|-------------|-------------|
| Services not running | Offer to run `just selfhost-up-tunnel` (recommended) or `just selfhost-up` (no tunnel) |
| API unhealthy | Run `just selfhost-logs` and `just selfhost-status` to diagnose, present findings |

After fixing each issue, re-run that check to confirm it passes before moving on.

When all checks pass, print the final status table and suggest next steps:
- "Try `/syn-status` for a quick platform overview"
- "Ask me to create a workflow — I know how to design multi-phase agent pipelines"
- "Ask me to set up automatic PR reviews with GitHub trigger rules"
- "Use `/syn-sessions list` to see agent execution history"
